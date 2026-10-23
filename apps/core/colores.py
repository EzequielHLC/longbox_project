"""El mapa de colores de la tienda (plan 00 de interfaz, cuarta parte, B y A).

Cada **rol** es una parte de la tienda —el botón principal, los enlaces, los
precios…— y el Administrador elige qué color de la paleta lleva (`CU-CFG-VIS`).
De ese color salen solas sus variantes, en `longbox.css`: `-vivo` para el hover,
`-hondo` para lo presionado, `-suave` para los fondos de selección. Elegir azul da
hover azul claro sin cargar nada más.

Lo que no se puede derivar en CSS se calcula acá, con el contraste de WCAG:

- `-sobre`: el texto encima del color, noche o blanco.
- `-texto`: el color usado como texto sobre el fondo de la tienda. Si no llega a
  3:1 contra el fondo, se usa el más legible de noche o blanco: un precio
  amarillo sobre papel no se lee.

Los valores iniciales reproducen la tienda tal como se veía antes del mapa.
"""

from dataclasses import dataclass

from apps.core.contraste import contraste, mas_legible

PRIMARIO = "primario"
SECUNDARIO = "secundario"
ACENTO = "acento"
NEUTRO = "neutro"
FONDO = "fondo"
NOMBRES = {
    PRIMARIO: "Primario",
    SECUNDARIO: "Secundario",
    ACENTO: "Acento",
    NEUTRO: "Neutro (sin color)",
    FONDO: "Fondo",
}
OPCIONES = [(clave, nombre) for clave, nombre in NOMBRES.items()]

NOCHE = "#0A0A0C"
BLANCO = "#FFFFFF"
MINIMO_TEXTO_GRANDE = 3

PALETA = (PRIMARIO, SECUNDARIO, ACENTO)


@dataclass(frozen=True)
class Rol:
    clave: str
    nombre: str
    alcance: str
    inicial: str
    opciones: tuple

    @property
    def campo(self):
        return f"color_rol_{self.clave}"


ROLES = (
    Rol("boton", "Botón principal", "Comprar, agregar al carrito y confirmar.", PRIMARIO, PALETA),
    Rol(
        "enlaces",
        "Botones secundarios y enlaces",
        "Los demás botones, los enlaces, el foco y lo seleccionado.",
        ACENTO,
        PALETA,
    ),
    Rol(
        "precios",
        "Precios",
        "El precio en las tarjetas y en la ficha del producto.",
        NEUTRO,
        (NEUTRO, *PALETA),
    ),
    Rol(
        "marcas",
        "Rótulos y carteles",
        "El rótulo de pre-venta y el cartel «¡Tomo 1!».",
        ACENTO,
        PALETA,
    ),
    Rol(
        "titulos",
        "Títulos de sección",
        "Los antetítulos y la barra debajo de cada título.",
        ACENTO,
        (NEUTRO, *PALETA),
    ),
    Rol(
        "tarjetas",
        "Tarjetas e imágenes",
        "La sombra que aparece al pasar por encima de una tarjeta o de una imagen.",
        ACENTO,
        (NEUTRO, *PALETA),
    ),
    Rol(
        "encabezado",
        "Encabezado y pie",
        "El fondo de la barra de arriba y del pie de la tienda.",
        FONDO,
        (FONDO, *PALETA),
    ),
)
POR_CLAVE = {rol.clave: rol for rol in ROLES}


def _hex(identidad, opcion):
    return {
        PRIMARIO: identidad.color_primario,
        SECUNDARIO: identidad.color_secundario,
        ACENTO: identidad.color_acento,
        FONDO: identidad.color_fondo,
    }.get(opcion)


def _referencia(opcion):
    """La variable de la paleta: así la vista previa la cambia en vivo."""
    if opcion == NEUTRO:
        return "var(--texto-fuerte)"
    return f"var(--tienda-{opcion})"


def texto_sobre_fondo(color, fondo):
    if contraste(color, fondo) >= MINIMO_TEXTO_GRANDE:
        return color
    return mas_legible(fondo, (NOCHE, BLANCO))


def variables(identidad):
    """Las variables `--rol-*` de la hoja de la tienda, en orden."""
    fondo = identidad.color_fondo
    salida = []
    for rol in ROLES:
        opcion = getattr(identidad, rol.campo)
        color = _hex(identidad, opcion)
        nombre = f"--rol-{rol.clave}"
        salida.append((nombre, _referencia(opcion)))
        if color is None:  # neutro: el texto fuerte de la superficie
            salida.append((f"{nombre}-sobre", "var(--fondo)"))
            salida.append((f"{nombre}-texto", "var(--texto-fuerte)"))
            continue
        salida.append((f"{nombre}-sobre", mas_legible(color, (NOCHE, BLANCO))))
        salida.append((f"{nombre}-texto", texto_sobre_fondo(color, fondo)))
    return salida


def encabezado_con_color(identidad):
    """Si el encabezado y el pie dejan el fondo, su texto pasa al color de contraste."""
    opcion = identidad.color_rol_encabezado
    if opcion == FONDO:
        return None
    return mas_legible(_hex(identidad, opcion), (NOCHE, BLANCO))


def mapa(identidad):
    """Para la pantalla: cada rol con su color elegido."""
    return [
        {
            "rol": rol,
            "opcion": getattr(identidad, rol.campo),
            "color": _hex(identidad, getattr(identidad, rol.campo)),
        }
        for rol in ROLES
    ]
