"""D6-02 · Un modelo de lenguaje que responde basura, para ver qué hace el sistema.

    python scripts/demo/llm_falso.py roto        # JSON roto
    python scripts/demo/llm_falso.py inventado   # forma correcta, datos inventados
    python scripts/demo/llm_falso.py --apuntar   # la demo usa este modelo (Parámetros globales)
    python scripts/demo/llm_falso.py --restaurar # vuelve a la URL de LM Studio

Escucha en `http://127.0.0.1:1235` y contesta como un servidor compatible con la
API de OpenAI (`/v1/models` y `/v1/chat/completions`), igual que LM Studio. El
sistema le habla por la misma puerta única de salida HTTP que usa siempre.

- **roto**: el contenido no es JSON. Esperado: el correo queda en «Falló el
  procesamiento», con el motivo, y sigue en la cola para reprocesar.
- **inventado**: JSON válido con un ISBN de dígito incorrecto, un precio
  negativo, una fecha imposible y una portada que el correo no trae. Esperado:
  cada dato inventado se descarta con su reparo. El título inventado no se puede
  verificar: queda como **borrador**, que una persona tiene que confirmar
  (regla 4: el modelo propone, nunca aplica).
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PUERTO = 1235
URL = f"http://127.0.0.1:{PUERTO}/v1/chat/completions"

INVENTADO = {
    "intencion": "novedades",
    "periodo": "marzo 2026",
    "productos": [
        {
            "titulo": "Tomo que no existe",
            "volumen": "7",
            "formato": "B6",
            "isbn": "978-987-1234-56-0",
            "precio": "-12500",
            "fecha": "31/02/2026",
            "imagen": "cid:portada-inventada@demo",
            "confianza": {"titulo": "alta", "isbn": "altísima"},
        }
    ],
}


class Manejador(BaseHTTPRequestHandler):
    modo = "roto"

    def _responder(self, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):  # noqa: N802 - nombre de la API de http.server
        self._responder({"data": [{"id": "modelo-falso", "object": "model"}]})

    def do_POST(self):  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        contenido = (
            '{"intencion": "novedades", "productos": [{"titulo": "Akira"'
            if self.modo == "roto"
            else json.dumps(INVENTADO, ensure_ascii=False)
        )
        self._responder({"choices": [{"message": {"role": "assistant", "content": contenido}}]})

    def log_message(self, formato, *argumentos):
        print(f"[modelo falso · {self.modo}] {formato % argumentos}", flush=True)


def apuntar(url):
    from entorno import preparar

    preparar()
    from apps.core.models import ConfiguracionSistema

    configuracion = ConfiguracionSistema.obtener()
    anterior = configuracion.llm_url
    configuracion.llm_url = url
    configuracion.save()
    print(f"URL del modelo: {anterior} → {url}")


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("modo", nargs="?", choices=["roto", "inventado"])
    argumentos.add_argument("--apuntar", action="store_true")
    argumentos.add_argument("--restaurar", action="store_true")
    opciones = argumentos.parse_args()
    if opciones.apuntar:
        return apuntar(URL)
    if opciones.restaurar:
        return apuntar("http://127.0.0.1:1234/v1/chat/completions")
    Manejador.modo = opciones.modo or "roto"
    print(f"Modelo falso en {URL}, modo «{Manejador.modo}». Ctrl+C para detener.", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
