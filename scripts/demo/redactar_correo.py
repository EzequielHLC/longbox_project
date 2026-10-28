"""Redactar a mano un correo de proveedor y mandarlo a la casilla de prueba. Sólo desarrollo.

    python scripts/demo/redactar_correo.py
    python scripts/demo/redactar_correo.py --smtp 127.0.0.1:2525 --para casilla@longbox.demo

Abre una página en http://127.0.0.1:8770 donde se escribe el correo como lo
escribiría una editorial: remitente, asunto, el texto de alrededor y, si hace
falta, la tabla de productos con sus portadas. Tres plantillas de arranque
—novedades, demora y libre (una factura, un saludo)— y todo se puede editar.
Se manda por SMTP al correo de prueba (`config/correo-de-prueba/`) o se baja
como `.eml` para cargarlo con `manage.py ingerir_correos`.

Después, «Revisar la casilla» en la cola de correos (o `manage.py revisar_casilla`)
lo trae sin esperar al Temporizador.

Es una herramienta de la demostración (plan 00 del circuito con los
proveedores, ítem H): **no es parte del sistema** y no lo toca. No lee la base
ni importa Django; los estilos los toma de `static/` para que se vea como el
panel. Escucha sólo en esta máquina.
"""

import argparse
import html
import json
import mimetypes
import smtplib
import sys
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import format_datetime, make_msgid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESTATICOS = RAIZ / "static"
TAMANIO_MAXIMO = 20 * 1024 * 1024
COLUMNAS = ("isbn", "titulo", "tomo", "formato", "fecha", "precio")
FILAS = 8

PLANTILLAS = {
    "novedades": {
        "asunto": "Novedades de {mes}",
        "cuerpo": "Estimados,\n\nLes compartimos las novedades de {mes}.\n\n"
        "Saludos, el equipo comercial.",
        "tabla": True,
    },
    "demora": {
        "asunto": "Reprogramación de lanzamientos",
        "cuerpo": "Estimados,\n\nLes informamos que los siguientes títulos se reprograman "
        "para {mes}. Disculpen las molestias.\n\nSaludos, el equipo comercial.",
        "tabla": True,
    },
    "libre": {
        "asunto": "Factura de octubre",
        "cuerpo": "Estimados,\n\nAdjuntamos el resumen de cuenta del mes.\n\nSaludos, "
        "administración.",
        "tabla": False,
    },
}


# ---------------------------------------------------------------------------
# El correo
# ---------------------------------------------------------------------------


def armar(datos, portadas, *, para):
    """El mensaje, con la tabla en HTML y las portadas embebidas por `Content-ID`."""
    correo = EmailMessage()
    correo["From"] = datos.get("de") or "novedades@ivrea.demo"
    correo["To"] = para
    correo["Subject"] = datos.get("asunto") or "Sin asunto"
    correo["Date"] = format_datetime(datetime.now().astimezone())
    correo["Message-ID"] = make_msgid(domain="redactado.demo")

    cuerpo = datos.get("cuerpo", "")
    renglones = _renglones(datos) if datos.get("con_tabla") else []
    cids = {}
    for indice, (contenido, tipo) in portadas.items():
        if any(r["indice"] == indice for r in renglones):
            cids[indice] = (make_msgid(domain="portadas.demo")[1:-1], contenido, tipo)

    texto = [cuerpo, ""] if cuerpo else []
    for r in renglones:
        texto.append(" · ".join(r[c] for c in COLUMNAS if r[c]))
    correo.set_content("\n".join(texto) or " ")

    parrafos = "".join(f"<p>{html.escape(p)}</p>" for p in cuerpo.split("\n\n") if p.strip())
    tabla = ""
    if renglones:
        encabezado = "".join(
            f"<th>{n}</th>"
            for n in ("Portada", "ISBN", "Título", "Tomo", "Formato", "Fecha", "Precio")
        )
        filas = ""
        for r in renglones:
            portada = (
                f"<img src='cid:{cids[r['indice']][0]}' width='80'>" if r["indice"] in cids else ""
            )
            celdas = "".join(f"<td>{html.escape(r[c])}</td>" for c in COLUMNAS)
            filas += f"<tr><td>{portada}</td>{celdas}</tr>"
        tabla = f"<table border='1'><tr>{encabezado}</tr>{filas}</table>"
    correo.add_alternative(f"<html><body>{parrafos}{tabla}</body></html>", subtype="html")

    alternativa = correo.get_payload()[1]
    for cid, contenido, tipo in cids.values():
        principal, _, secundario = tipo.partition("/")
        alternativa.add_related(contenido, principal, secundario, cid=f"<{cid}>")
    return correo


def _renglones(datos):
    salida = []
    for indice in range(FILAS):
        renglon = {c: (datos.get(f"{c}_{indice}") or "").strip() for c in COLUMNAS}
        if renglon["titulo"] or renglon["isbn"]:
            renglon["indice"] = indice
            salida.append(renglon)
    return salida


def mandar(correo, smtp):
    servidor, _, puerto = smtp.partition(":")
    with smtplib.SMTP(servidor, int(puerto or 25), timeout=20) as conexion:
        conexion.send_message(correo)


# ---------------------------------------------------------------------------
# El formulario
# ---------------------------------------------------------------------------


def leer_formulario(tipo, cuerpo):
    """Un `multipart/form-data` sin el módulo `cgi`, que Python 3.13 sacó."""
    mensaje = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {tipo}\r\n\r\n".encode() + cuerpo
    )
    datos, portadas = {}, {}
    for parte in mensaje.iter_parts():
        nombre = parte.get_param("name", header="content-disposition")
        if not nombre:
            continue
        if parte.get_filename():
            contenido = parte.get_payload(decode=True) or b""
            if contenido and nombre.startswith("portada_"):
                tipo_imagen = (
                    parte.get_content_type()
                    if parte.get_content_maintype() == "image"
                    else mimetypes.guess_type(parte.get_filename())[0] or "image/jpeg"
                )
                portadas[int(nombre.removeprefix("portada_"))] = (contenido, tipo_imagen)
        else:
            # El navegador manda UTF-8 sin declarar el `charset` de cada campo.
            datos[nombre] = (parte.get_payload(decode=True) or b"").decode("utf-8", "replace")
    return datos, portadas


def pagina(opciones, *, aviso="", error=""):
    filas = "".join(
        "<tr>"
        + "".join(
            f'<td><label class="sr-only" for="{c}_{i}">{c} {i + 1}</label>'
            f'<input type="text" id="{c}_{i}" name="{c}_{i}"'
            + (' inputmode="numeric" class="entrada-cifra"' if c in ("tomo", "precio") else "")
            + "></td>"
            for c in COLUMNAS
        )
        + f'<td><label class="sr-only" for="portada_{i}">Portada {i + 1}</label>'
        f'<input type="file" id="portada_{i}" name="portada_{i}" accept="image/*"></td>'
        "</tr>"
        for i in range(FILAS)
    )
    mensaje = ""
    if aviso:
        mensaje = f'<p class="mensaje mensaje--listo"><span>{aviso}</span></p>'
    if error:
        mensaje = f'<p class="mensaje mensaje--error"><span>{html.escape(error)}</span></p>'
    plantillas = "".join(
        f'<button type="button" class="boton-seccion boton-seccion--tenue" '
        f'data-plantilla="{clave}">{clave.capitalize()}</button>'
        for clave in PLANTILLAS
    )
    return PAGINA.format(
        mensaje=mensaje,
        plantillas=plantillas,
        filas=filas,
        para=html.escape(opciones.para),
        smtp=html.escape(opciones.smtp),
        web=html.escape(opciones.web),
        datos_plantillas=json.dumps(PLANTILLAS, ensure_ascii=False),
    )


PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redactar correo de proveedor</title>
<link rel="stylesheet" href="/static/css/tokens.css">
<link rel="stylesheet" href="/static/css/longbox.css">
<style>
  body {{ background: var(--fondo); }}
  .redactor {{ max-width: 72rem; margin: 0 auto; padding: var(--esp-6) var(--esp-4); }}
  .redactor textarea {{ min-height: 9rem; }}
  .redactor .tabla input {{ width: 100%; min-width: 6rem; }}
  .redactor .tabla input[type=file] {{ min-width: 17rem; }}
</style></head>
<body class="modo-operativo"><main class="redactor pila-3">
<header class="encabezado-de-pantalla"><div class="encabezado-de-pantalla__textos">
  <h1>Redactar correo de proveedor</h1>
  <p class="secundario">Herramienta de la demostración. Sale por <span class="datos">{smtp}</span>
  hacia <span class="datos">{para}</span>; mirá la bandeja en <a href="{web}">{web}</a>
  y traelo con «Revisar la casilla» en la cola de correos.</p>
</div></header>
{mensaje}
<form method="post" enctype="multipart/form-data" class="formulario">
  <div class="fila-2"><span class="etiqueta">Empezar desde</span>{plantillas}</div>
  <div class="rejilla-2">
    <div class="campo"><label class="etiqueta" for="de">Remitente</label>
      <input type="email" id="de" name="de" value="novedades@ivrea.demo" required>
      <p class="ayuda">Tiene que ser el correo comercial de un proveedor cargado.</p></div>
    <div class="campo"><label class="etiqueta" for="asunto">Asunto</label>
      <input type="text" id="asunto" name="asunto" required></div>
  </div>
  <div class="campo"><label class="etiqueta" for="cuerpo">Texto del correo</label>
    <textarea id="cuerpo" name="cuerpo"></textarea>
    <p class="ayuda">Un párrafo por bloque, separados por una línea en blanco. El período
    («Novedades de marzo 2026», «se reprograman para mayo») va acá.</p></div>
  <label class="fila-2"><input type="checkbox" id="con_tabla" name="con_tabla" value="1" checked>
    <span>Incluir la tabla de productos</span></label>
  <div class="tabla-desplazable" id="tabla">
    <table class="tabla"><thead><tr><th>ISBN</th><th>Título</th><th>Tomo</th><th>Formato</th>
    <th>Fecha</th><th>Precio</th><th>Portada</th></tr></thead><tbody>{filas}</tbody></table>
  </div>
  <div class="acciones">
    <button type="submit" name="accion" value="mandar" class="boton-primario">
      Mandar a la casilla</button>
    <button type="submit" name="accion" value="eml" class="boton-seccion">Bajar .eml</button>
  </div>
</form></main>
<script>
const plantillas = {datos_plantillas};
const mes = new Date(Date.now() + 40 * 864e5)
  .toLocaleDateString("es-AR", {{month: "long", year: "numeric"}});
const conTabla = document.getElementById("con_tabla");
const tabla = document.getElementById("tabla");
conTabla.addEventListener("change", () => {{ tabla.hidden = !conTabla.checked; }});
document.querySelectorAll("[data-plantilla]").forEach((boton) => {{
  boton.addEventListener("click", () => {{
    const p = plantillas[boton.dataset.plantilla];
    document.getElementById("asunto").value = p.asunto.replace("{{mes}}", mes);
    document.getElementById("cuerpo").value = p.cuerpo.replace("{{mes}}", mes);
    conTabla.checked = p.tabla;
    tabla.hidden = !p.tabla;
  }});
}});
</script></body></html>"""


# ---------------------------------------------------------------------------
# El servidor
# ---------------------------------------------------------------------------


class Redactor(BaseHTTPRequestHandler):
    opciones = None

    def do_GET(self):  # noqa: N802 - nombre de http.server
        if self.path.startswith("/static/"):
            return self._estatico(self.path.removeprefix("/static/").split("?")[0])
        if self.path not in ("/", ""):
            return self.send_error(HTTPStatus.NOT_FOUND)
        return self._html(pagina(self.opciones))

    def do_POST(self):  # noqa: N802 - nombre de http.server
        largo = int(self.headers.get("Content-Length") or 0)
        if largo > TAMANIO_MAXIMO:
            return self._html(pagina(self.opciones, error="El correo pesa más de 20 MB."))
        datos, portadas = leer_formulario(
            self.headers.get("Content-Type", ""), self.rfile.read(largo)
        )
        correo = armar(datos, portadas, para=self.opciones.para)
        if datos.get("accion") == "eml":
            contenido = bytes(correo)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "message/rfc822")
            self.send_header("Content-Disposition", 'attachment; filename="redactado.eml"')
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
            return None
        try:
            mandar(correo, self.opciones.smtp)
        except OSError as error:
            return self._html(
                pagina(
                    self.opciones,
                    error=f"No se pudo mandar por {self.opciones.smtp}: {error}. "
                    "¿Está levantado el correo de prueba?",
                )
            )
        aviso = (
            f"Se mandó «{html.escape(correo['Subject'])}» a {html.escape(self.opciones.para)}. "
            "Traelo con «Revisar la casilla» en la cola de correos."
        )
        return self._html(pagina(self.opciones, aviso=aviso))

    def _html(self, texto):
        contenido = texto.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def _estatico(self, ruta):
        archivo = (ESTATICOS / ruta).resolve()
        if not archivo.is_relative_to(ESTATICOS) or not archivo.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND)
        contenido = archivo.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type", mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        )
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)
        return None


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--puerto", type=int, default=8770)
    argumentos.add_argument("--smtp", default="127.0.0.1:2525")
    argumentos.add_argument("--para", default="casilla@longbox.demo")
    argumentos.add_argument("--web", default="http://127.0.0.1:5000")
    opciones = argumentos.parse_args()

    Redactor.opciones = opciones
    servidor = ThreadingHTTPServer(("127.0.0.1", opciones.puerto), Redactor)
    print(f"Redactor en http://127.0.0.1:{opciones.puerto} (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
