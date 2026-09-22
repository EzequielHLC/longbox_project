"""El prompt de novedades y la validación de lo que devuelve el modelo.

Acá están las reglas; el transporte está en `apps/core/llm.py`. La división
importa porque estas dos partes cambian por motivos distintos: el prompt se
ajusta cuando un proveedor manda algo raro, el cliente solo si se cambia de
servidor.

**Qué se le pide y qué no.** El correo trae ISBN, portada, título, volumen,
formato y PVP, más el **período** que anuncia —"Novedades de marzo 2026"—, que
vive en la prosa de alrededor de la tabla y no dentro de ella. De ese período
sacan la fecha los borradores, y de la fecha sale si nacen en Pre-venta o
Activos (CU-ALT-NOV paso 6): sin pedirlo, todos nacerían Activos, y un producto que
todavía no llegó figurando disponible no da ningún síntoma hasta que alguien lo
compra. **No trae editorial ni rubro**, y no por descuido: la
comunicación es directa de la editorial a la comiquería, así que nadie escribe
su propio nombre en su propio newsletter. Esos dos los aporta la ficha del
proveedor, que CU-PRV-ALT declara (`Proveedor.editorial` y `Proveedor.rubro`).
Pedírselos al modelo sería
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
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from apps.catalog import isbn as isbn_util
from apps.core import llm

logger = logging.getLogger(__name__)

# Se guarda junto a cada extracción. Subirla cuando cambie el prompt o el
# esquema de forma que el resultado deje de ser comparable con el anterior.
VERSION_PROMPT = "2"

# Las tres que reconoce el pipeline. `otro` no es un cajón de sastre: es la
# respuesta correcta para una factura o un saludo, y es lo que justifica que la
# cola de aprobación exista.
NOVEDADES = "novedades"
DEMORA = "demora"
OTRO = "otro"
INTENCIONES = (NOVEDADES, DEMORA, OTRO)

# Cómo de seguro está el modelo de cada campo. Los tres valores son los que pide
# CU-ALT-NOV paso 4, y CU-ALT-REV los usa para decidir qué se puede confirmar en lote.
CONFIANZAS = ("alta", "media", "baja")

# De qué campos se le pide al modelo que declare cuánto confía. Está en una
# constante y no escrita dos veces adentro del esquema porque la lista de
# propiedades y la de obligatorias tienen que decir lo mismo: si se separan,
# el servidor deja de exigir la confianza de un campo y nadie se entera.
CAMPOS_CON_CONFIANZA = ("isbn", "titulo", "volumen", "formato", "precio", "fecha")

# Los meses escritos como los escribe un proveedor. "setiembre" convive con
# "septiembre" porque las dos formas son correctas en castellano y en un correo
# aparecen las dos.
MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
_DIA_MES_ANIO = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_MES_ANIO_EN_NUMEROS = re.compile(r"(?<!\d)(\d{1,2})/(\d{4})")
_MES_ANIO_EN_LETRAS = re.compile(r"([a-záéíóú]+)\s+(?:de\s+)?(\d{4})")


def interpretar_fecha(texto):
    """Convierte a `date` una fecha escrita como la escribe un proveedor.

    Devuelve `None` si no se entiende, y eso **no es lo mismo que un error**:
    un correo que no anuncia ninguna fecha es el caso normal, y sus borradores
    nacen Activos (CU-ALT-NOV paso 6).

    Reconoce las cuatro formas que aparecen en los correos reales: `2026-03-15`,
    `15/04/2026`, `04/2026` y `marzo 2026` (con o sin "de" en el medio).

    **Un mes sin año no se interpreta.** "Novedades de marzo" podría ser de este
    año o del que viene, y elegir uno sería exactamente lo que el resto de este
    archivo se cuida de no hacer: completar un dato que no está. Sin año, el
    borrador nace Activo y el Administrador le pone la fecha en la revisión.

    **Un mes sin día se toma como el día 1.** Es el extremo conservador del
    rango: adelanta la vigilancia de la pre-venta en vez de atrasarla, y un
    producto vigilado de más se corrige mirándolo, mientras que uno vigilado de
    menos no se descubre hasta que un cliente pregunta dónde está su reserva.
    """
    limpio = " ".join(str(texto or "").split()).lower()
    if not limpio:
        return None

    encontrado = _ISO.search(limpio)
    if encontrado:
        anio, mes, dia = (int(parte) for parte in encontrado.groups())
        return _fecha_valida(anio, mes, dia)

    encontrado = _DIA_MES_ANIO.search(limpio)
    if encontrado:
        dia, mes, anio = (int(parte) for parte in encontrado.groups())
        return _fecha_valida(anio, mes, dia)

    encontrado = _MES_ANIO_EN_NUMEROS.search(limpio)
    if encontrado:
        mes, anio = (int(parte) for parte in encontrado.groups())
        return _fecha_valida(anio, mes, 1)

    encontrado = _MES_ANIO_EN_LETRAS.search(limpio)
    if encontrado:
        nombre, anio = encontrado.groups()
        if nombre in MESES:
            return _fecha_valida(int(anio), MESES[nombre], 1)

    return None


def _fecha_valida(anio, mes, dia):
    """`None` en vez de reventar: un 31 de febrero es un dato malo, no un fallo."""
    try:
        return date(anio, mes, dia)
    except ValueError:
        return None


SISTEMA = """Sos un asistente que extrae datos de correos de novedades que las \
editoriales argentinas de historieta y manga le mandan a una comiquería.

El correo ya viene convertido a texto. Las filas de una tabla de datos aparecen \
con este formato:

| celda | celda | celda |

y las portadas embebidas aparecen dentro de su fila como un marcador \
[imagen:identificador].

Tu trabajo tiene tres partes.

1. Clasificar el correo en una de tres intenciones:
   - "novedades": anuncia productos que la editorial va a publicar o publicó.
   - "demora": avisa que algo se atrasa o se reprograma.
   - "otro": cualquier otra cosa (facturas, promociones, saludos).

2. Si es "novedades", copiar el período que el correo anuncia, tal como está escrito y en una \
sola línea. Suele estar en el texto de alrededor de la tabla, no dentro de ella: "Novedades de \
marzo 2026", "Lanzamientos: 15/04/2026". Si el correo no anuncia ningún período, dejalo vacío.

3. Si es "novedades", extraer un objeto por cada producto anunciado.

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
- La fecha de un producto se copia **solo si la fila la trae**. La del período general no se \
repite en cada producto: para eso está el campo de arriba. Si la fila no dice ninguna fecha, \
dejala vacía.
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
        "periodo": {"type": "string"},
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
                    "fecha": {"type": "string"},
                    "imagen": {"type": "string"},
                    "confianza": {
                        "type": "object",
                        "properties": {
                            campo: {"type": "string", "enum": list(CONFIANZAS)}
                            for campo in CAMPOS_CON_CONFIANZA
                        },
                        "required": list(CAMPOS_CON_CONFIANZA),
                    },
                },
                "required": [
                    "isbn",
                    "titulo",
                    "volumen",
                    "formato",
                    "precio",
                    "fecha",
                    "imagen",
                    "confianza",
                ],
            },
        },
    },
    "required": ["intencion", "periodo", "productos"],
}


@dataclass
class ProductoExtraido:
    """Un producto anunciado, ya limpio y con sus reparos anotados."""

    titulo: str = ""
    volumen: int | None = None
    isbn: str = ""
    formato: str = ""
    precio: Decimal | None = None
    # La fecha que trae **esta fila**. Casi siempre vacía: el período lo
    # anuncia el correo entero y vive en `Extraccion.periodo`.
    fecha: date | None = None
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
    # El período que el correo anuncia ("Novedades de marzo 2026"), que es de
    # donde los borradores heredan la fecha cuando la fila no trae una propia.
    # Se guardan las dos cosas: lo que el modelo copió y lo que se pudo
    # interpretar. Sin el texto, un período que no se entendió sería
    # indistinguible de un correo que no anunciaba ninguno.
    periodo_texto: str = ""
    periodo: date | None = None
    # Reparos del correo entero, no de un producto. Hoy solo uno: el período
    # ilegible, que si no quedara anotado dejaría a todos sus borradores
    # naciendo Activos sin que nadie sepa por qué.
    reparos: list = field(default_factory=list)
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
            "periodo_texto": self.periodo_texto,
            "periodo": self.periodo.isoformat() if self.periodo else "",
            "reparos": self.reparos,
            "productos": [
                {
                    "titulo": producto.titulo,
                    "volumen": producto.volumen,
                    "isbn": producto.isbn,
                    "formato": producto.formato,
                    "precio": str(producto.precio) if producto.precio is not None else "",
                    "fecha": producto.fecha.isoformat() if producto.fecha else "",
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
    entera, que es lo que piden E2 y E3 de CU-ALT-NOV.
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

    periodo_texto = " ".join(str(datos.get("periodo", "")).split())
    periodo = interpretar_fecha(periodo_texto) if intencion == NOVEDADES else None
    reparos = []
    if intencion == NOVEDADES and periodo_texto and periodo is None:
        # Que no se entienda no invalida el correo, pero tiene que quedar
        # anotado: sin la fecha, todos sus borradores nacen Activos, y esa es
        # exactamente la clase de cosa que no da ningún síntoma.
        reparos.append(f"Período ilegible: «{periodo_texto}». Los borradores nacen sin fecha.")

    return Extraccion(
        intencion=intencion,
        productos=productos,
        periodo_texto=periodo_texto,
        periodo=periodo,
        reparos=reparos,
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
    producto.fecha = _fecha_de_fila(crudo.get("fecha"), producto)
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


def _fecha_de_fila(crudo, producto):
    """La fecha propia de un producto, cuando la fila la trae.

    Que venga vacía es el caso normal y **no deja reparo**: la fecha la anuncia
    el correo entero, no cada fila. Solo se anota cuando el modelo copió algo
    que después no se pudo interpretar, que es cuando hay algo que mirar.
    """
    texto = str(crudo or "").strip()
    if not texto:
        return None
    fecha = interpretar_fecha(texto)
    if fecha is None:
        producto.reparos.append(f"Fecha ilegible: «{texto}».")
    return fecha


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
