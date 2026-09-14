"""Armado de correos de novedades de ejemplo, para los tests y para probar a mano.

Los correos se construyen acá en vez de commitear archivos `.eml` sueltos por
dos motivos: un `.eml` con imágenes embebidas es ilegible en una revisión de
código, y desde acá se puede generar la variante que cada test necesita —sin
imágenes, con el remitente equivocado, sin identificador— cambiando un argumento
en vez de manteniendo ocho archivos casi iguales.

**Reproducen lo que mandan los proveedores nacionales de verdad:** HTML con una
tabla por producto, con ISBN, portada, nombre, volumen, formato y PVP en celdas,
y las portadas **embebidas** como partes `image/webp` referenciadas con `cid:`
desde el HTML. Ese último punto no es un detalle de implementación: es lo que
hace que CU-ALT-NOV paso 7 —"descarga las imágenes referenciadas por URL"— no aplique
(ver la corrección 16 de `docs/correcciones-fuente.md`).

Vienen con las trampas puestas a propósito, porque probar contra un correo ideal
no prueba nada: una tabla de maquetado envolviendo el contenido, un logo
embebido que **no** es una portada, y una fila de encabezado.
"""

import io
from email.message import EmailMessage
from email.utils import formatdate

from PIL import Image

# Un catálogo chico pero con los casos que importan: dos tomos de la misma serie
# —para que el volumen distinga— y uno de otra, con un formato distinto.
NOVEDADES = [
    {
        "isbn": "9789878271583",
        "cid": "tapa001@ivrea.test",
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "pvp": "24900",
    },
    {
        "isbn": "9789878271590",
        "cid": "tapa002@ivrea.test",
        "titulo": "Berserk Deluxe",
        "volumen": "6",
        "formato": "Tapa dura",
        "pvp": "24900",
    },
    {
        "isbn": "9789878274652",
        "cid": "tapa003@ivrea.test",
        "titulo": "Blue Period",
        "volumen": "12",
        "formato": "B6",
        "pvp": "11500",
    },
]


def portada_webp(color="#B0102A", medidas=(80, 120)):
    """Una imagen WebP mínima. El formato es el que usan los proveedores."""
    buffer = io.BytesIO()
    Image.new("RGB", medidas, color).save(buffer, format="WEBP")
    return buffer.getvalue()


def _fila(producto):
    return (
        "<tr>"
        f'<td>{producto["isbn"]}</td>'
        f'<td><img src="cid:{producto["cid"]}" alt="Tapa"></td>'
        f'<td>{producto["titulo"]}</td>'
        f'<td>{producto["volumen"]}</td>'
        f'<td>{producto["formato"]}</td>'
        f'<td>${producto["pvp"]}</td>'
        "</tr>"
    )


def cuerpo_html(productos, con_logo=True, periodo="marzo 2026"):
    """El HTML del correo, con las trampas de un correo real.

    La tabla de productos va **envuelta en otra tabla de maquetado**, que es como
    se arma el HTML de un correo, y arriba va un logo embebido que no es la
    portada de nada. Las dos cosas están a propósito: si el extractor solo
    funcionara con una tabla limpia, funcionaría solo con correos de prueba.
    """
    logo = '<tr><td><img src="cid:logo@ivrea.test" alt="Ivrea"></td></tr>' if con_logo else ""
    filas = "".join(_fila(producto) for producto in productos)
    return (
        "<html><head><style>.x{color:red}</style></head><body>"
        '<table class="maqueta">'
        f"{logo}"
        "<tr><td>"
        f"<p>Novedades de {periodo}</p>"
        "<table>"
        "<tr><th>ISBN</th><th>Tapa</th><th>Título</th>"
        "<th>Vol.</th><th>Formato</th><th>PVP</th></tr>"
        f"{filas}"
        "</table>"
        "<p>Los pedidos se reciben hasta el 20 de marzo.</p>"
        "</td></tr>"
        "</table>"
        "</body></html>"
    )


def correo_de_novedades(
    remitente="novedades@ivrea.test",
    nombre_remitente="Novedades Ivrea",
    asunto="Novedades marzo 2026",
    productos=None,
    message_id="<marzo-2026@ivrea.test>",
    con_imagenes=True,
    con_logo=True,
    periodo="marzo 2026",
):
    """Los bytes de un correo de novedades listo para `services.ingerir`.

    El remitente lleva nombre de fantasía a propósito: el encabezado real llega
    como `"Novedades Ivrea" <novedades@ivrea.test>` y el matcheo tiene que
    encontrar al proveedor igual.

    `periodo` es lo que el correo anuncia en la prosa de alrededor de la tabla,
    y es de donde los borradores sacan la fecha. Se puede cambiar porque de él
    depende si nacen en Pre-venta o Activos, que es la rama con consecuencias:
    un producto que todavía no llegó figurando disponible no da ningún síntoma
    hasta que alguien lo compra.
    """
    productos = NOVEDADES if productos is None else productos

    mensaje = EmailMessage()
    mensaje["From"] = f"{nombre_remitente} <{remitente}>" if nombre_remitente else remitente
    mensaje["To"] = "compras@longbox.test"
    mensaje["Subject"] = asunto
    mensaje["Date"] = formatdate(localtime=True)
    if message_id:
        mensaje["Message-ID"] = message_id

    mensaje.set_content("Este correo requiere un lector con soporte HTML.")
    mensaje.add_alternative(
        cuerpo_html(productos, con_logo=con_logo, periodo=periodo), subtype="html"
    )

    if con_imagenes:
        # Las portadas se adjuntan a la parte HTML, que es la que las referencia.
        parte_html = mensaje.get_payload()[1]
        if con_logo:
            _adjuntar(parte_html, "logo@ivrea.test", portada_webp("#0A0A0D", (200, 40)))
        for producto in productos:
            _adjuntar(parte_html, producto["cid"], portada_webp())

    return mensaje.as_bytes()


def _adjuntar(parte, cid, contenido):
    parte.add_related(
        contenido,
        maintype="image",
        subtype="webp",
        cid=f"<{cid}>",
        filename=f"{cid.split('@')[0]}.webp",
    )


def correo_de_demora(
    remitente="novedades@ivrea.test",
    message_id="<demora-berserk@ivrea.test>",
):
    """Un aviso de demora: el otro tipo de correo que llega por la misma casilla.

    No se procesa distinto todavía —clasificar la intención es trabajo del
    modelo, y eso llega después— pero existe acá desde ahora porque es la razón
    de ser de la cola de aprobación: por la dirección comercial del proveedor no
    llegan solo novedades.
    """
    mensaje = EmailMessage()
    mensaje["From"] = f"Novedades Ivrea <{remitente}>"
    mensaje["To"] = "compras@longbox.test"
    mensaje["Subject"] = "Reprogramación de Berserk Deluxe 5"
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = message_id
    mensaje.set_content("Este correo requiere un lector con soporte HTML.")
    mensaje.add_alternative(
        "<html><body><p>Estimados,</p>"
        "<p>Les informamos que Berserk Deluxe vol. 5 se reprograma para mayo.</p>"
        "</body></html>",
        subtype="html",
    )
    return mensaje.as_bytes()
