"""El prompt de novedades y la validación de lo que devuelve el modelo.

Acá están las reglas; el transporte está en `apps/core/llm.py`. La división
importa porque estas dos partes cambian por motivos distintos: el prompt se
ajusta cuando un proveedor manda algo raro, el cliente solo si se cambia de
servidor.

**Qué se le pide y qué no.** El correo trae ISBN, portada, título, volumen,
formato y PVP. **No trae editorial ni rubro**, y no por descuido: la
comunicación es directa de la editorial a la comiquería, así que nadie escribe
su propio nombre en su propio newsletter. Esos dos los aporta la ficha del
proveedor (A7 de `/docs/modulos/proveedores.md`). Pedírselos al modelo sería
invitarlo a inventarlos.

**Por qué el prompt se versiona.** Un borrador generado con el prompt de marzo y
otro con el de junio no son comparables, y cuando algo salga raro la primera
pregunta va a ser con cuál se extrajo. La versión se guarda junto al resultado.

**Por qué la validación es tan desconfiada.** Un modelo no falla avisando: falla
devolviendo algo con la forma correcta y el contenido inventado. Las tres
defensas de este archivo son (1) el esquema, que el servidor hace cumplir al
decodificar, (2) el dígito verificador del ISBN, que es aritmética nuestra y
atrapa un número alucinado, y (3) la comprobación de que cada portada
referenciada exista de verdad entre las partes del correo.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from apps.catalog import isbn as isbn_util
from apps.core import llm

logger = logging.getLogger(__name__)

# Se guarda junto a cada extracción. Subirla cuando cambie el prompt o el
# esquema de forma que el resultado deje de ser comparable con el anterior.
VERSION_PROMPT = "1"

# Las tres que reconoce el pipeline. `otro` no es un cajón de sastre: es la
# respuesta correcta para una factura o un saludo, y es lo que justifica que la
# cola de aprobación exista.
NOVEDADES = "novedades"
DEMORA = "demora"
OTRO = "otro"
INTENCIONES = (NOVEDADES, DEMORA, OTRO)

# Cómo de seguro está el modelo de cada campo. Los tres valores son los que pide
# CU-04 paso 4, y CU-05 los usa para decidir qué se puede confirmar en lote.
CONFIANZAS = ("alta", "media", "baja")

SISTEMA = """Sos un asistente que extrae datos de correos de novedades que las \
editoriales argentinas de historieta y manga le mandan a una comiquería.

El correo ya viene convertido a texto. Las filas de una tabla de datos aparecen \
con este formato:

| celda | celda | celda |

y las portadas embebidas aparecen dentro de su fila como un marcador \
[imagen:identificador].

Tu trabajo tiene dos partes.

1. Clasificar el correo en una de tres intenciones:
   - "novedades": anuncia productos que la editorial va a publicar o publicó.
   - "demora": avisa que algo se atrasa o se reprograma.
   - "otro": cualquier otra cosa (facturas, promociones, saludos).

2. Si es "novedades", extraer un objeto por cada producto anunciado.

Reglas que no podés romper:

- Copiá los datos, no los completes. Si un dato no está en el correo, dejalo \
vacío y marcá su confianza como "baja". Nunca lo deduzcas ni lo inventes.
- No devuelvas la editorial ni el rubro del material: ese dato no está en el \
correo y lo aporta el sistema.
- El ISBN se copia tal cual, con o sin guiones. Si no hay, dejalo vacío.
- El precio va solo con dígitos y, si corresponde, un punto decimal: sin signo \
de peso ni separadores de miles.
- El identificador de la portada es el que aparece dentro del marcador \
[imagen:...] de la fila de ese producto. Si la fila no tiene ninguno, dejalo \
vacío. Nunca uses el de otra fila.
- Las filas de encabezado de una tabla no son productos.
- La confianza es "alta" si el dato está escrito claro en la fila, "media" si \
tuviste que interpretarlo, y "baja" si está ausente o dudoso."""

# El esquema que el servidor hace cumplir al decodificar. Es la primera de las
# tres defensas: con esto el modelo **no puede** devolver una forma distinta, y
# la validación de abajo deja de tener que ocuparse de la estructura para
# ocuparse solo del contenido.
ESQUEMA = {
    "type": "object",
    "properties": {
        "intencion": {"type": "string", "enum": list(INTENCIONES)},
        "productos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "isbn": {"type": "string"},
                    "titulo": {"type": "string"},
                    "volumen": {"type": "string"},
                    "formato": {"type": "string"},
                    "precio": {"type": "string"},
                    "imagen": {"type": "string"},
                    "confianza": {
                        "type": "object",
                        "properties": {
                            campo: {"type": "string", "enum": list(CONFIANZAS)}
                            for campo in ("isbn", "titulo", "volumen", "formato", "precio")
                        },
                        "required": ["isbn", "titulo", "volumen", "formato", "precio"],
                    },
                },
                "required": [
                    "isbn",
                    "titulo",
                    "volumen",
                    "formato",
                    "precio",
                    "imagen",
                    "confianza",
                ],
            },
        },
    },
    "required": ["intencion", "productos"],
}


@dataclass
class ProductoExtraido:
    """Un producto anunciado, ya limpio y con sus reparos anotados."""

    titulo: str = ""
    volumen: int | None = None
    isbn: str = ""
    formato: str = ""
    precio: Decimal | None = None
    imagen: str = ""
    confianza: dict = field(default_factory=dict)
    # Lo que el sistema le corrigió o le descartó al modelo. No es lo mismo que
    # una confianza baja: eso lo declara el modelo, esto lo detectamos nosotros.
    reparos: list = field(default_factory=list)

    @property
    def esta_completo(self):
        """Si trae lo mínimo para poder armar un borrador con él."""
        return bool(self.titulo) and self.precio is not None


@dataclass
class Extraccion:
    """El resultado completo de leer un correo."""

    intencion: str = OTRO
    productos: list = field(default_factory=list)
    error: str = ""
    version_prompt: str = VERSION_PROMPT
    crudo: str = ""
    # Cuánto tardó el modelo. Con uno local la diferencia entre dos segundos y
    # dos minutos decide si el pipeline puede correr en una tarea corta o
    # necesita una cola de verdad, así que se conserva junto al resultado.
    milisegundos: int = 0

    def __bool__(self):
        return not self.error

    @property
    def sin_servicio(self):
        """El modelo no contestó, a diferencia de contestar algo ilegible.

        Se expone como propiedad para que la pantalla no tenga que comparar
        contra la cadena `"sin_servicio"` escrita a mano: renombrar la constante
        rompería el mensaje en silencio, que es el mismo motivo por el que
        `solo_adultos` es un campo y no una etiqueta.
        """
        return self.error == llm.SIN_SERVICIO

    @property
    def resumen(self):
        """Para el log de auditoría y la pantalla."""
        completos = sum(1 for producto in self.productos if producto.esta_completo)
        return {
            "intencion": self.intencion,
            "productos": len(self.productos),
            "completos": completos,
            "incompletos": len(self.productos) - completos,
            "con_reparos": sum(1 for producto in self.productos if producto.reparos),
        }

    def como_json(self):
        """Lo que se guarda en el correo para poder mirarlo después."""
        return {
            "version_prompt": self.version_prompt,
            "intencion": self.intencion,
            "error": self.error,
            "milisegundos": self.milisegundos,
            "productos": [
                {
                    "titulo": producto.titulo,
                    "volumen": producto.volumen,
                    "isbn": producto.isbn,
                    "formato": producto.formato,
                    "precio": str(producto.precio) if producto.precio is not None else "",
                    "imagen": producto.imagen,
                    "confianza": producto.confianza,
                    "reparos": producto.reparos,
                }
                for producto in self.productos
            ],
        }


def extraer(contenido, *, cids=()):
    """Lee un correo ya extraído a texto y devuelve lo que el modelo entendió.

    `cids` son los identificadores de las portadas que el correo trae de verdad.
    Sirven para descartar una imagen inventada: sin esa comprobación, un
    identificador alucinado dejaría el borrador con una portada que no existe y
    el fallo aparecería recién al intentar adjuntarla.

    Nunca levanta. Un correo raro no puede tumbar la lectura de la casilla
    entera, que es lo que piden E2 y E3 de CU-04.
    """
    respuesta = llm.pedir_json(SISTEMA, contenido, formato=ESQUEMA)
    if not respuesta:
        return Extraccion(
            error=respuesta.error,
            crudo=respuesta.crudo,
            milisegundos=respuesta.milisegundos,
        )

    datos = respuesta.datos
    intencion = datos.get("intencion")
    if intencion not in INTENCIONES:
        intencion = OTRO

    # Solo se leen productos de un correo de novedades. Si el modelo clasificó
    # "demora" y devolvió productos igual, se ignoran: mezclar las dos cosas es
    # exactamente el error que la clasificación viene a evitar.
    productos = []
    if intencion == NOVEDADES:
        productos = [
            _producto(crudo, cids)
            for crudo in datos.get("productos", [])
            if isinstance(crudo, dict)
        ]

    return Extraccion(
        intencion=intencion,
        productos=productos,
        version_prompt=VERSION_PROMPT,
        crudo=respuesta.crudo,
        milisegundos=respuesta.milisegundos,
    )


def _producto(crudo, cids):
    """Limpia un producto y anota lo que hubo que corregirle."""
    producto = ProductoExtraido(
        titulo=" ".join(str(crudo.get("titulo", "")).split()),
        formato=" ".join(str(crudo.get("formato", "")).split()),
        confianza=_confianza(crudo.get("confianza")),
    )
    producto.volumen = _volumen(crudo.get("volumen"), producto)
    producto.isbn = _isbn(crudo.get("isbn"), producto)
    producto.precio = _precio(crudo.get("precio"), producto)
    producto.imagen = _imagen(crudo.get("imagen"), cids, producto)

    if not producto.titulo:
        producto.reparos.append("Sin título: el producto no se puede identificar.")
    return producto


def _confianza(crudo):
    """Solo los tres valores válidos; lo demás se toma como baja.

    Al alza sería peor: un valor raro interpretado como "alta" haría que un dato
    dudoso se confirmara en lote sin que nadie lo mire.
    """
    if not isinstance(crudo, dict):
        return {}
    return {
        campo: (valor if valor in CONFIANZAS else "baja")
        for campo, valor in crudo.items()
        if isinstance(valor, str)
    }


def _volumen(crudo, producto):
    texto = str(crudo or "").strip()
    if not texto:
        return None
    # Un "Vol. 5" o un "5" tienen que dar lo mismo: el modelo copia lo que ve.
    digitos = "".join(caracter for caracter in texto if caracter.isdigit())
    if not digitos:
        producto.reparos.append(f"Volumen ilegible: «{texto}».")
        return None
    return int(digitos)


def _isbn(crudo, producto):
    """Se normaliza y **se verifica el dígito de control**.

    Es la defensa que atrapa un ISBN alucinado o mal transcripto. Un número que
    no verifica no se guarda: pasaría a identificar un producto que no existe, y
    el chequeo de duplicados dejaría de encontrar el que sí.
    """
    valor = isbn_util.normalizar(str(crudo or ""))
    if not valor:
        return ""
    motivo = isbn_util.motivo_de_rechazo(valor)
    if motivo:
        producto.reparos.append(f"ISBN descartado («{valor}»): {motivo}")
        return ""
    return valor


def _precio(crudo, producto):
    texto = str(crudo or "").strip()
    if not texto:
        return None
    # Aunque el prompt lo pide limpio, un "$ 24.900" llega igual: el separador de
    # miles argentino es el punto, así que se saca antes de interpretar.
    limpio = texto.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        precio = Decimal(limpio)
    except InvalidOperation:
        producto.reparos.append(f"Precio ilegible: «{texto}».")
        return None
    if precio <= 0:
        producto.reparos.append(f"Precio fuera de rango: «{texto}».")
        return None
    return precio


def _imagen(crudo, cids, producto):
    """La portada solo vale si existe de verdad entre las partes del correo."""
    valor = str(crudo or "").strip().strip("[]")
    if valor.startswith("imagen:"):
        valor = valor[len("imagen:") :]
    valor = valor.strip()
    if not valor:
        return ""
    if cids and valor not in cids:
        producto.reparos.append(f"Portada inexistente («{valor}»): se ignora.")
        return ""
    return valor
