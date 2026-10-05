"""Baja la portada de cada tomo desde la galería PORTADAS de cada serie de Ivrea.

    python scripts/demo/raspar_portadas_tomos.py [--limite N]

**Sólo para la demostración en clase**, como `raspar_ivrea.py`: los archivos
quedan en `scripts/demo/datos/portadas_tomos/`, fuera del control de versiones.

La ficha de una serie (`/titulo/<slug>/`) trae, bajo el título PORTADAS, una
galería con una imagen por tomo. El nombre de la imagen dice la serie y el
número: `agenciadelamor01`, `onepiece109`; algunas obras tienen tomo `00`. La
galería llega de dos maneras según la ficha:

- el complemento de galerías: `<a class="bwg-a" href="<imagen completa>">` con
  `alt="onepiece01"` en la miniatura de adentro;
- la galería de WordPress: `<img src="agenciadelamor02-142x200.jpg"
  title="agenciadelamor02">`, y la imagen completa es la misma sin el tamaño.

Una ficha puede traer galerías de series hermanas (otra edición, un spin-off).
Se queda con las imágenes cuyo nombre empieza igual que la portada principal de
la serie; si no se puede saber, con el prefijo más repetido.

Una ficha por segundo, las imágenes de a cuatro, y se puede cortar: lo ya
bajado no se vuelve a pedir y el índice (`portadas_tomos.json`: serie → tomo →
archivo) se guarda a medida
que avanza.
"""

import argparse
import html
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from enviar_novedades import series as leer_series
from raspar_ivrea import DATOS, PAUSA, pedir

CARPETA = DATOS / "portadas_tomos"
INDICE = DATOS / "portadas_tomos.json"
MAXIMO_TOMO = 120
SIMULTANEAS = 4
NOMBRE = re.compile(r"^(?P<prefijo>.*?)(?P<numero>\d{1,3})$")
TAMANO = re.compile(r"-\d+x\d+(?=\.\w+$)")


def _nombre(url):
    """`.../onepiece01-142x200.jpg?bwg=1` → `onepiece01`."""
    archivo = url.split("?")[0].rsplit("/", 1)[-1]
    return TAMANO.sub("", archivo).rsplit(".", 1)[0].lower()


def imagenes(pagina):
    """Pares (nombre, url completa) de la sección PORTADAS, en el orden de la página."""
    inicio = pagina.find("PORTADAS</h4>")
    if inicio < 0:
        return []
    seccion = pagina[inicio:]
    hallados = []
    for enlace in re.finditer(r'<a[^>]*class="bwg-a[^"]*"[^>]*href="([^"]+)"', seccion):
        hallados.append(html.unescape(enlace.group(1)))
    for imagen in re.finditer(r'<img[^>]*src="([^"]+-\d+x\d+\.(?:jpe?g|png|webp))"', seccion):
        hallados.append(TAMANO.sub("", html.unescape(imagen.group(1))))
    vistos, pares = set(), []
    for url in hallados:
        nombre = _nombre(url)
        if nombre not in vistos:
            vistos.add(nombre)
            pares.append((nombre, url))
    return pares


def por_tomo(pares, portada_url):
    """{tomo: url} de la serie, descartando galerías de otras series."""
    numerados = [(NOMBRE.match(n), url) for n, url in pares]
    numerados = [(m["prefijo"], int(m["numero"]), url) for m, url in numerados if m]
    if not numerados:
        return {}
    principal = NOMBRE.match(_nombre(portada_url or ""))
    prefijos = Counter(prefijo for prefijo, _, _ in numerados)
    if principal and principal["prefijo"] in prefijos:
        prefijo = principal["prefijo"]
    else:
        prefijo = prefijos.most_common(1)[0][0]
    return {numero: url for p, numero, url in numerados if p == prefijo and numero <= MAXIMO_TOMO}


def bajar(url, destino):
    datos = pedir(url)
    if len(datos) < 1024:
        raise ValueError("respuesta demasiado chica para ser una imagen")
    destino.write_bytes(datos)


def main():
    opciones = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    opciones.add_argument("--limite", type=int, help="Sólo las primeras N series.")
    argumentos = opciones.parse_args()

    CARPETA.mkdir(parents=True, exist_ok=True)
    indice = json.loads(INDICE.read_text(encoding="utf-8")) if INDICE.exists() else {}
    series = [s for s in leer_series() if "(franquicia)" not in s["titulo"].lower()]
    if argumentos.limite:
        series = series[: argumentos.limite]

    fallas = 0
    for posicion, serie in enumerate(series, start=1):
        slug = serie["slug"]
        if slug in indice and indice[slug].get("_completa"):
            continue
        try:
            pagina = pedir(serie["url"]).decode("utf-8", errors="replace")
            time.sleep(PAUSA)
            tomos = por_tomo(imagenes(pagina), serie.get("portada_url"))
        except Exception as error:  # noqa: BLE001 - se anota y se sigue
            print(f"[{posicion}/{len(series)}] {slug}: no se pudo leer la ficha ({error})")
            fallas += 1
            continue
        propia = CARPETA / slug
        propia.mkdir(exist_ok=True)
        registro = {}

        def uno(numero, url, propia=propia, slug=slug):
            extension = url.split("?")[0].rsplit(".", 1)[-1].lower()
            destino = propia / f"{numero:03d}.{extension}"
            if not destino.exists():
                bajar(url, destino)
            return numero, f"{slug}/{destino.name}"

        # Las imágenes de una serie, de a SIMULTANEAS: el servidor tarda más de un
        # segundo en cada una, así que el ritmo real queda en una o dos por segundo.
        with ThreadPoolExecutor(SIMULTANEAS) as grupo:
            pendientes = {grupo.submit(uno, n, u): n for n, u in sorted(tomos.items())}
            for hecho in as_completed(pendientes):
                try:
                    numero, archivo = hecho.result()
                    registro[str(numero)] = archivo
                except Exception as error:  # noqa: BLE001
                    print(f"    {slug} tomo {pendientes[hecho]}: {error}")
                    fallas += 1
        registro["_completa"] = True
        indice[slug] = registro
        INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{posicion}/{len(series)}] {slug}: {len(registro) - 1} tomos", flush=True)

    total = sum(len(r) - 1 for r in indice.values())
    print(f"Listo: {len(indice)} series, {total} portadas por tomo, {fallas} fallas.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
