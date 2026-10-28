"""El modelo de lenguaje en el bot (módulo 19, etapa 2; decisiones 9 y 10 del plan).

Dos usos, los dos con un esquema que el servidor hace cumplir:

- **Elegir la consulta** (`CU-AVI-CON`): una pregunta libre («¿cuántos Chainsaw Man
  12 tengo?») se traduce a una de las consultas fijas, con su argumento. **El
  modelo no toca la base**: elige; el sistema consulta y responde.
- **Leer un producto** (`CU-AVI-BOR`): el texto de `/cargar` o el epígrafe de una
  foto, a los mismos campos de una novedad. Lo limpia la misma validación de los
  correos (`extraccion._producto`): ISBN con dígito verificador, precio, fecha,
  volumen pegado al título. Sale un borrador, nunca un producto (regla 4).
"""

from dataclasses import dataclass
from datetime import date

from apps.core import llm
from apps.suppliers import extraccion

CONSULTAS = (
    "stock",
    "llega",
    "pendientes",
    "caja",
    "estado",
    "borradores",
    "cargar",
    "ninguna",
)

SISTEMA_CONSULTA = """Sos el asistente del bot de una comiquería argentina. Te escribe el \
Administrador. Elegí cuál de estas consultas responde lo que pregunta:

- "stock": el stock, el precio o el estado de un producto. En "texto" copiá el título (con su \
número de tomo), el código o el ISBN que nombra.
- "llega": lo que llega en los próximos días, lo que está atrasado, las pre-ventas por llegar.
- "pendientes": lo que espera una decisión: correos de proveedores, borradores, pedidos por armar.
- "caja": lo vendido o cobrado hoy.
- "estado": cómo anda el sistema: disco, memoria, respaldos.
- "borradores": quiere ver los borradores de productos que esperan revisión. En "texto", el \
título si nombra uno.
- "cargar": describe un producto para darlo de alta.
- "ninguna": cualquier otra cosa.

Respondé sólo con la consulta y, si es "stock" o "borradores", el texto. No inventes datos."""

ESQUEMA_CONSULTA = {
    "type": "object",
    "properties": {
        "consulta": {"type": "string", "enum": list(CONSULTAS)},
        "texto": {"type": "string"},
    },
    "required": ["consulta", "texto"],
}

SISTEMA_PRODUCTO = """Sos el asistente que carga productos de una comiquería argentina. Te \
mandan un texto corto que describe UN producto. Copiá sus datos:

- "rubro": "editorial" si es un tomo para leer (manga, cómic, novela ligera, libro, artbook); \
"no_editorial" si es otra cosa (figura, carta o mazo de TCG, merchandising, insumo).
- "tipo": la clase de producto si la dice o es evidente (Manga, Cómic, Novela ligera, Libro, \
Artbook, Figura, TCG, Merchandising, Insumo), o vacío.
- "editorial": el nombre de la editorial si lo dice (Ivrea, Panini, Ovni Press…), o vacío. \
"Nacional" e "importado" no son editoriales: son el origen.
- "titulo": el título de la serie, sin el número de tomo.
- "volumen": el número de tomo, sólo los dígitos, o vacío.
- "isbn": el ISBN si lo trae, tal cual, o vacío.
- "formato": el formato si lo dice (B6, Tankōbon, Kanzenban, tapa dura…), o vacío.
- "precio": el precio con dígitos y punto decimal, sin signo ni separadores de miles, o vacío.
- "fecha": la fecha de salida si la dice, tal cual, o vacío.
- "confianza": por cada campo, "alta" si está escrito claro, "media" si lo interpretaste, \
"baja" si falta o es dudoso.

Copiá, no completes: si un dato no está, dejalo vacío con confianza "baja"."""

ESQUEMA_PRODUCTO = {
    "type": "object",
    "properties": {
        "rubro": {"type": "string", "enum": ["editorial", "no_editorial"]},
        "tipo": {"type": "string"},
        "editorial": {"type": "string"},
        "producto": extraccion.ESQUEMA["properties"]["productos"]["items"],
    },
    "required": ["rubro", "tipo", "editorial", "producto"],
}


@dataclass
class Lectura:
    """Lo que el modelo leyó de un mensaje: el producto con la forma de una novedad
    (`crudo`, ya validado y con sus reparos) y los nombres que el sistema resuelve."""

    crudo: dict
    editorial: str = ""
    tipo: str = ""
    no_editorial: bool = False


def _limpio(valor):
    return " ".join(str(valor or "").split())


def elegir_consulta(texto):
    """`(consulta, argumento)`, o `None` si el modelo no contestó."""
    respuesta = llm.pedir_json(SISTEMA_CONSULTA, texto, formato=ESQUEMA_CONSULTA)
    if not respuesta or not isinstance(respuesta.datos, dict):
        return None
    consulta = respuesta.datos.get("consulta")
    if consulta not in CONSULTAS:
        consulta = "ninguna"
    return consulta, _limpio(respuesta.datos.get("texto"))


def leer_producto(texto, *, hoy=None):
    """La `Lectura` del mensaje, o `None` si el modelo no contestó."""
    respuesta = llm.pedir_json(SISTEMA_PRODUCTO, texto, formato=ESQUEMA_PRODUCTO)
    if not respuesta or not isinstance(respuesta.datos, dict):
        return None
    datos = respuesta.datos.get("producto")
    if not isinstance(datos, dict):
        return None
    datos.setdefault("imagen", "")
    leido = extraccion._producto(datos, cids=(), recibido=hoy or date.today())
    crudo = {
        "titulo": leido.titulo,
        "volumen": leido.volumen,
        "isbn": leido.isbn,
        "formato": leido.formato,
        "precio": str(leido.precio) if leido.precio is not None else "",
        "fecha": leido.fecha.isoformat() if leido.fecha else "",
        "imagen": "",
        "confianza": leido.confianza,
        "reparos": leido.reparos,
    }
    return Lectura(
        crudo=crudo,
        editorial=_limpio(respuesta.datos.get("editorial")),
        tipo=_limpio(respuesta.datos.get("tipo")),
        no_editorial=respuesta.datos.get("rubro") == "no_editorial",
    )
