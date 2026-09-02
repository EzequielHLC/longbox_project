"""Lectura de un correo de novedades: de bytes MIME a texto parseable.

Vive aparte y **sin Django de por medio** —igual que `precios.py` o `isbn.py`—
para poder probarlo con correos de ejemplo sin levantar la base ni una casilla.
Lo que entra son los bytes de un mensaje; lo que sale es un dato plano que el
servicio guarda.

Dos decisiones que no son obvias:

**No se aplana a texto plano.** CU-04 paso 3 pide "extraer el contenido a texto
plano", y para estos correos eso está mal: son HTML con una tabla por producto
—ISBN, foto, nombre, volumen, formato y PVP en celdas— y aplanarla destruye la
asociación fila-columna. A partir de ahí el modelo empieza a atribuirle a un
tomo el precio del siguiente, un error que no da ningún síntoma y se descubre
tres meses después mirando un precio raro. Acá la tabla se conserva como filas
de celdas separadas por barras. Ver la corrección 15 de
`docs/correcciones-fuente.md`.

**Las portadas no se descargan: ya vinieron.** CU-04 paso 7 supone que la imagen
está referenciada por URL, pero los proveedores nacionales las mandan embebidas
como partes MIME con un `Content-ID`. Cada `<img>` se reemplaza por un marcador
`[imagen:identificador]` dentro de su fila, de modo que el modelo lo devuelve
como un campo más del producto y la resolución posterior es una búsqueda exacta
de la parte, sin correlacionar por orden —que se rompe con el logo del
encabezado—. Ver la corrección 16.

No se usa ninguna biblioteca de terceros: `email` y `html.parser` son de la
biblioteca estándar, y el intercambio no lo justifica.
"""

from dataclasses import dataclass, field
from email import message_from_bytes, policy
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import unquote

# Etiquetas cuyo contenido no es texto para leer. Sin esto, la hoja de estilos
# de un correo entra al contenido extraído como si fuera prosa.
ETIQUETAS_MUDAS = {"style", "script", "head", "title"}

# Prefijo del marcador con el que viaja una imagen embebida.
MARCADOR_IMAGEN = "[imagen:{cid}]"


@dataclass
class ImagenEmbebida:
    """Una parte MIME de imagen, identificada por su `Content-ID`.

    Lleva **el contenido y su tamaño por separado**, y no es redundancia: lo que
    se guarda en `CorreoProveedor.imagenes` es el resumen —cuántos bytes pesa—,
    mientras que el contenido solo se necesita en el momento de adjuntarle la
    portada a un borrador. Copiar los bytes a la tabla engordaría cada fila con
    algo que ya está en el `.eml` archivado.
    """

    cid: str
    tipo: str
    bytes_: int
    nombre: str = ""
    contenido: bytes = b""

    def resumen(self):
        """Lo que se persiste. Sin el contenido, a propósito."""
        return {"cid": self.cid, "tipo": self.tipo, "bytes": self.bytes_, "nombre": self.nombre}


@dataclass
class CorreoLeido:
    """Todo lo que se puede sacar de un correo sin decidir nada del negocio."""

    message_id: str
    remitente: str
    asunto: str
    fecha: object | None
    html: str
    contenido: str
    imagenes: list = field(default_factory=list)

    @property
    def cids(self):
        return {imagen.cid for imagen in self.imagenes}


class _ExtractorDeTabla(HTMLParser):
    """Convierte el HTML de un correo en texto que conserva la forma de la tabla.

    Emite las filas de datos como `| celda | celda |` y todo lo demás como
    párrafos sueltos. Cada imagen se reemplaza por su marcador **en el lugar
    donde estaba**, que es lo que la ata a la fila de su producto.

    **Las tablas vienen anidadas, y eso no es un caso raro.** El HTML de un
    correo usa tablas para maquetar: la de productos viene envuelta en otra que
    acomoda el diseño, y la prosa de alrededor —"Novedades de marzo 2026", que
    es de donde sale el período del envío— vive en la celda de esa tabla
    exterior. Por eso el estado son **pilas** y no variables sueltas: con una
    sola fila "actual", abrir la tabla interna pisaba la externa y esa prosa se
    perdía sin dejar rastro.

    **Una fila de una sola celda se emite como párrafo, no como fila.** Una fila
    de datos tiene varias columnas; una de una sola celda es maquetado —el
    encabezado con el logo, un pie— y marcarla con barras la haría parecer un
    producto de una sola columna. Así, las únicas líneas con barras del
    contenido extraído son las que de verdad son filas de una tabla de datos.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lineas = []
        self._filas = []  # pila de filas abiertas; cada una, sus celdas cerradas
        self._celdas = []  # pila de celdas abiertas; cada una, sus fragmentos
        self._suelto = []  # texto que no está dentro de ninguna celda
        self._mudas = 0

    # -- estructura ----------------------------------------------------------

    def handle_starttag(self, tag, attrs):
        if tag in ETIQUETAS_MUDAS:
            self._mudas += 1
            return
        if tag == "img":
            self._agregar_imagen(dict(attrs))
        elif tag == "table":
            # Lo que se venía escribiendo en esta celda es prosa que precede a
            # la tabla, no parte de ella: se emite ahora para no perderla y para
            # que quede en el orden en que estaba escrita.
            self._volcar_celda_abierta()
            self._volcar_suelto()
        elif tag == "tr":
            self._filas.append([])
        elif tag in ("td", "th"):
            self._celdas.append([])
        elif tag in ("br", "p", "div", "li"):
            self._volcar_suelto()

    def handle_endtag(self, tag):
        if tag in ETIQUETAS_MUDAS:
            self._mudas = max(0, self._mudas - 1)
            return
        if tag in ("td", "th"):
            self._cerrar_celda()
        elif tag == "tr":
            self._cerrar_fila()
        elif tag == "table":
            self._cerrar_fila()

    def handle_data(self, datos):
        if self._mudas:
            return
        texto = datos.strip()
        if not texto:
            return
        destino = self._celdas[-1] if self._celdas else self._suelto
        destino.append(texto)

    def close(self):
        super().close()
        # Un correo mal cerrado —y llegan— no puede hacer que se pierda la
        # última fila ni el último párrafo.
        while self._celdas:
            self._cerrar_celda()
        while self._filas:
            self._cerrar_fila()
        self._volcar_suelto()

    # -- piezas --------------------------------------------------------------

    def _agregar_imagen(self, atributos):
        origen = atributos.get("src", "")
        if origen.startswith("cid:"):
            marca = MARCADOR_IMAGEN.format(cid=normalizar_cid(origen[4:]))
        elif atributos.get("alt"):
            # Una imagen que no es embebida igual ocupa un lugar en la fila; sin
            # dejar rastro, la celda quedaría vacía y correría las columnas.
            marca = f"[imagen: {atributos['alt'].strip()}]"
        else:
            return
        destino = self._celdas[-1] if self._celdas else self._suelto
        destino.append(marca)

    def _cerrar_celda(self):
        if not self._celdas:
            return
        texto = _juntar(self._celdas.pop())
        if self._filas:
            self._filas[-1].append(texto)
        elif texto:
            # Una celda sin fila es HTML roto; su texto se conserva igual.
            self.lineas.append(texto)

    def _cerrar_fila(self):
        if not self._filas:
            return
        celdas = self._filas.pop()
        con_texto = [celda for celda in celdas if celda]
        if not con_texto:
            return
        if len(celdas) == 1:
            self.lineas.append(con_texto[0])
        else:
            self.lineas.append("| " + " | ".join(celdas) + " |")

    def _volcar_celda_abierta(self):
        """Emite lo acumulado en la celda más interna sin cerrarla."""
        if not self._celdas:
            return
        texto = _juntar(self._celdas[-1])
        if texto:
            self.lineas.append(texto)
        self._celdas[-1].clear()

    def _volcar_suelto(self):
        texto = _juntar(self._suelto)
        if texto:
            self.lineas.append(texto)
        self._suelto.clear()


def _juntar(fragmentos):
    """Los fragmentos de una celda como un texto de una línea, sin espacios de más."""
    return " ".join(" ".join(fragmentos).split())


def normalizar_cid(valor):
    """El identificador de una imagen, comparable venga de donde venga.

    El `src` del HTML llega como `cid:tapa001@ivrea` y puede estar codificado
    (`cid:tapa001%40ivrea`), mientras que la cabecera de la parte llega como
    `<tapa001@ivrea>`. Sin normalizar los dos lados, el marcador de la fila
    nunca encontraría su imagen — y fallaría en silencio, dejando el borrador
    con "Imagen pendiente" sin que nadie entienda por qué.
    """
    return unquote(valor or "").strip().strip("<>").strip()


def extraer_contenido(html):
    """El HTML convertido en texto que conserva las filas y marca las imágenes."""
    extractor = _ExtractorDeTabla()
    extractor.feed(html or "")
    extractor.close()
    return "\n".join(extractor.lineas)


def leer(datos):
    """Lee los bytes de un correo. No decide nada del negocio, solo extrae.

    El remitente sale de `From` con `parseaddr`, que separa la dirección del
    nombre de fantasía: un `"Novedades Ivrea" <novedades@ivrea.test>` tiene que
    encontrar al mismo proveedor que la dirección pelada.
    """
    mensaje = message_from_bytes(datos, policy=policy.default)

    html, imagenes = _cuerpo_y_partes(mensaje)
    return CorreoLeido(
        message_id=(mensaje.get("Message-ID") or "").strip(),
        remitente=parseaddr(mensaje.get("From", ""))[1].strip().lower(),
        asunto=(mensaje.get("Subject") or "").strip(),
        fecha=_fecha(mensaje),
        html=html,
        contenido=extraer_contenido(html),
        imagenes=imagenes,
    )


def _cuerpo_y_partes(mensaje):
    """El HTML del cuerpo y las imágenes embebidas.

    Se prefiere la parte HTML sobre la de texto plano: es la que trae la tabla.
    Si el correo viniera solo en texto plano se usa esa, aunque para estos
    proveedores no es el caso.
    """
    html = ""
    respaldo = ""
    imagenes = []

    for parte in mensaje.walk():
        if parte.get_content_maintype() == "multipart":
            continue

        tipo = parte.get_content_type()
        if tipo == "text/html" and not html:
            html = parte.get_content()
        elif tipo == "text/plain" and not respaldo:
            respaldo = parte.get_content()
        elif parte.get_content_maintype() == "image":
            imagenes.append(_imagen(parte, tipo))

    return html or _como_html(respaldo), imagenes


def _imagen(parte, tipo):
    contenido = parte.get_payload(decode=True) or b""
    return ImagenEmbebida(
        cid=normalizar_cid(parte.get("Content-ID", "")),
        tipo=tipo,
        bytes_=len(contenido),
        nombre=parte.get_filename() or "",
        contenido=contenido,
    )


def _como_html(texto):
    """Envuelve un cuerpo de texto plano para que el extractor lo trate igual."""
    if not texto:
        return ""
    return "<p>" + "</p><p>".join(linea for linea in texto.splitlines() if linea.strip()) + "</p>"


def _fecha(mensaje):
    """La fecha del encabezado, o `None` si viene ausente o ilegible.

    Un `Date` roto no puede tumbar la lectura de un correo por lo demás válido:
    la fecha es un dato de presentación, y el que manda para el orden de la cola
    es cuándo lo recibimos nosotros.
    """
    try:
        return parsedate_to_datetime(mensaje.get("Date"))
    except (TypeError, ValueError):
        return None
