"""La mitad de `presentacion.py` que corre dentro de Django.

    python scripts/demo/presentacion_carga.py exportar <archivo.json>   # sobre la base vieja
    python scripts/demo/presentacion_carga.py cargar <archivo.json>     # sobre la base nueva

No se usa sola: la llama `presentacion.py`, que elige la base de cada paso con
`DB_NAME`. Corre con los ajustes de desarrollo (no con los de la demostración de
resistencia).

- **exportar** guarda lo que se conserva: las tres cuentas (con el hash de su
  contraseña, así siguen entrando igual), la identidad visual y los parámetros.
- **cargar** lo vuelve a crear en la base nueva y suma el catálogo real de Ivrea
  (sólo Ivrea, nada sintético), el proveedor, unos correos de novedades, unas
  ofertas, tres banners armados con portadas y las filas de la portada.

Lo raspado se limpia al cargar (`limpias()`, `sinopsis()`): fuera las páginas que
agrupan una franquicia, la cabecera comercial y el código de la galería del sitio
que quedaron pegados a la sinopsis, y la categoría de Ivrea se traduce a tipo de
producto y etiqueta.
"""

import json
import os
import re
import sys
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(RAIZ), str(AQUI)]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from django.core.files.base import ContentFile  # noqa: E402
from django.core.serializers.json import DjangoJSONEncoder  # noqa: E402
from django.utils import timezone  # noqa: E402

CUENTAS = ("admin@correo.com", "cajero@correo.com", "cliente@correo.com")
NO_SE_COPIA = {"id", "actualizado_por", "actualizado_por_id"}

FAQ = """## ¿Qué es una pre-venta?

Un tomo que todavía no llegó a la tienda. Se puede **reservar** desde su ficha: la reserva no tiene
tope de unidades y se cobra al precio vigente.

## ¿El carrito guarda lo que elegí?

Sí. Con la cuenta iniciada, el carrito se conserva entre visitas. Si elegiste productos sin
iniciar sesión, al entrar se suman a los de tu cuenta.

## ¿Por qué cambió el precio de algo que tenía en el carrito?

Porque cambió el precio de lista o terminó una oferta. El carrito te avisa en esa línea y te
muestra el precio anterior, para que decidas.

## Olvidé mi contraseña

Desde «Ingresar», «¿Olvidó su contraseña?»: te llega un enlace que vale 30 minutos.
"""


# ---------------------------------------------------------------------------
def exportar(destino):
    from django.db.models import FileField

    from apps.accounts.models import Usuario
    from apps.core.models import ConfiguracionSistema, IdentidadVisual

    def fila(objeto):
        return {
            campo.name: getattr(objeto, campo.attname)
            for campo in objeto._meta.concrete_fields
            # Las imágenes no se copian: `media/` queda en el respaldo.
            if campo.name not in NO_SE_COPIA and not isinstance(campo, FileField)
        }

    cuentas = [fila(usuario) for usuario in Usuario.objects.filter(email__in=CUENTAS)]
    faltan = set(CUENTAS) - {cuenta["email"] for cuenta in cuentas}
    if faltan:
        raise SystemExit(f"No están en la base: {', '.join(sorted(faltan))}")
    datos = {
        "cuentas": cuentas,
        "identidad": fila(IdentidadVisual.obtener()),
        "configuracion": fila(ConfiguracionSistema.obtener()),
    }
    Path(destino).write_text(
        json.dumps(datos, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Exportado: {len(cuentas)} cuentas, identidad visual y parámetros → {destino}")


# ---------------------------------------------------------------------------
# Limpieza de lo raspado
# ---------------------------------------------------------------------------

# La categoría con que Ivrea clasifica la serie (`generos` en el Excel; la
# columna `demografia` trae texto suelto de la página): decide el tipo de
# producto y la etiqueta.
CATEGORIAS = {
    "shonen": ("Manga", "Demografía", "Shonen"),
    "seinen": ("Manga", "Demografía", "Seinen"),
    "shojo": ("Manga", "Demografía", "Shojo"),
    "bl/yaoi": ("Manga", "Género", "BL / Yaoi"),
    "gl/yuri": ("Manga", "Género", "GL / Yuri"),
    "webtoon/manhwa": ("Manga", "Colección", "Manhwa / Webtoon"),
    "comics": ("Cómic", None, None),
    "novelas": ("Novela ligera", None, None),
}
ESTADOS = {
    "serie completa": "Serie completa",
    "serie en curso": "Serie en curso",
    "tomo único": "Tomo único",
}
COLECCIONES = {"norteamericano": "Cómic norteamericano", "argentinos": "Autores argentinos"}
DEMOGRAFIAS = ("Shonen", "Seinen", "Shojo")


def categoria(serie):
    return str(serie.get("generos") or "").replace("Manga ", "").strip().lower()


def sinopsis(texto):
    """La sinopsis sin la cabecera comercial ni el código de la galería del sitio."""
    texto = str(texto or "")
    if "INFORMACIÓN SOBRE LA OBRA" in texto:
        texto = texto.split("INFORMACIÓN SOBRE LA OBRA", 1)[1]
    texto = re.split(r"\bPORTADAS\b|var bwg_", texto, maxsplit=1)[0]
    return " ".join(texto.split())


def cantidad_de_tomos(serie):
    if isinstance(serie.get("tomos_argentina"), int) and serie["tomos_argentina"] > 0:
        return min(serie["tomos_argentina"], 120)
    if "tomo único" in str(serie.get("etiquetas") or "").lower():
        return 1
    hallado = re.search(r"\((\d+) TOMOS?\)", str(serie.get("sinopsis") or ""))
    return min(int(hallado.group(1)), 120) if hallado else 1


def formato(serie):
    if categoria(serie) == "comics":
        return "Rústica"
    cabecera = " ".join(str(serie.get(c) or "") for c in ("formato", "sinopsis"))[:600].upper()
    if "KANZENBAN" in cabecera:
        return "Kanzenban"
    return "B6" if "B6" in cabecera else "Tankōbon"


def limpias(series):
    """Las series de verdad: sin las páginas que agrupan una franquicia ni títulos repetidos."""
    vistas, resultado = set(), []
    for serie in sorted(series, key=lambda s: s["slug"]):
        titulo = " ".join(serie["titulo"].split())
        clave = titulo.lower()
        if "(franquicia)" in clave or clave in vistas or categoria(serie) not in CATEGORIAS:
            continue
        vistas.add(clave)
        resultado.append({**serie, "titulo": titulo})
    return resultado


# ---------------------------------------------------------------------------
def _banner(rutas, nombre):
    """Un banner de 1920×810: portadas en fila sobre noche, con la cinta naranja abajo."""
    from PIL import Image, ImageDraw

    from apps.core import imagenes

    ancho, alto, cinta = 1920, 810, 44
    lienzo = Image.new("RGB", (ancho, alto), (10, 10, 12))
    alto_portada, margen, separacion = alto - cinta - 120, 60, 36
    portadas, ocupado = [], 0
    for ruta in rutas:
        portada = Image.open(ruta).convert("RGB")
        portada.thumbnail((10_000, alto_portada))
        if ocupado + portada.width > ancho - 2 * margen:
            break
        portadas.append(portada)
        ocupado += portada.width + separacion
    x = (ancho - (ocupado - separacion)) // 2
    for portada in portadas:
        lienzo.paste(portada, (x, margen))
        x += portada.width + separacion
    dibujo = ImageDraw.Draw(lienzo)
    for inicio in range(-cinta, ancho + cinta, 56):
        dibujo.polygon(
            [
                (inicio, alto),
                (inicio + 28, alto),
                (inicio + 28 + cinta, alto - cinta),
                (inicio + cinta, alto - cinta),
            ],
            fill=(255, 106, 19),
        )
    salida = BytesIO()
    lienzo.save(salida, "PNG")
    archivo = ContentFile(salida.getvalue(), name=f"{nombre}.png")
    return imagenes.procesar(
        archivo, lado_mayor=imagenes.LADO_MAYOR_BANNER, tamano_maximo=imagenes.TAMANO_MAXIMO_BANNER
    )


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

MEDIDAS = {
    "B6": "12,8 × 18,2 cm",
    "Tankōbon": "11,5 × 17,5 cm",
    "Kanzenban": "15 × 21 cm",
    "Rústica": "17 × 26 cm",
}
PVP = {
    ("Manga", "B6"): 15900,
    ("Manga", "Tankōbon"): 17500,
    ("Manga", "Kanzenban"): 29900,
    ("Novela ligera", "B6"): 19900,
    ("Novela ligera", "Tankōbon"): 19900,
    ("Novela ligera", "Kanzenban"): 24900,
    ("Cómic", "Rústica"): 32900,
}


def cargar(origen):
    from enviar_novedades import armar, renglones_al_azar
    from enviar_novedades import series as leer_series
    from poblar import DATOS, Poblador, _uno

    from apps.accounts.models import Usuario
    from apps.catalog.models import (
        Editorial,
        Etiqueta,
        Formato,
        GrupoEtiqueta,
        Oferta,
        Producto,
        ProductoEditorial,
        TablaPrecioReferencia,
        Tipo,
    )
    from apps.core.models import (
        Banner,
        ConfiguracionSistema,
        ContenidoFAQ,
        FilaPortada,
        IdentidadVisual,
    )
    from apps.suppliers import services
    from apps.suppliers.models import Proveedor

    if Producto.objects.exists() or Usuario.objects.exists():
        raise SystemExit("La base nueva no está vacía.")
    datos = json.loads(Path(origen).read_text(encoding="utf-8"))

    Usuario.objects.bulk_create([Usuario(**cuenta) for cuenta in datos["cuentas"]])
    administrador = Usuario.objects.get(rol=Usuario.ADMINISTRADOR)
    for clave, modelo in (("configuracion", ConfiguracionSistema), ("identidad", IdentidadVisual)):
        objeto = modelo.obtener()
        for campo, valor in datos[clave].items():
            setattr(objeto, campo, valor)
        if hasattr(objeto, "actualizado_por"):
            objeto.actualizado_por = administrador
        objeto.save()
    faq = ContenidoFAQ.obtener()
    faq.contenido = FAQ
    faq.save()

    series = limpias(leer_series())
    carga = Poblador()
    ivrea = _uno(Editorial, "Ivrea")
    tipos = {
        n: _uno(Tipo, n, clase=Producto.EDITORIAL, usa_formato=True)
        for n in ("Manga", "Cómic", "Novela ligera")
    }
    formatos = {n: _uno(Formato, n, descripcion=d, aplica_a_todos=True) for n, d in MEDIDAS.items()}
    carga.precios = {}
    for (tipo, nombre), pvp in PVP.items():
        fila = TablaPrecioReferencia.objects.create(
            editorial=ivrea, tipo=tipos[tipo], formato=formatos[nombre], pvp=Decimal(pvp)
        )
        carga.precios[(ivrea.pk, tipos[tipo].pk, formatos[nombre].pk)] = fila
    grupos = {
        n: _uno(GrupoEtiqueta, n)
        for n in ("Demografía", "Género", "Colección", "Estado de la serie")
    }
    etiquetas = {}

    def etiqueta(grupo, nombre):
        if (grupo, nombre) not in etiquetas:
            etiquetas[(grupo, nombre)] = Etiqueta.objects.filter(
                nombre__iexact=nombre, grupo=grupos[grupo]
            ).first() or Etiqueta.objects.create(nombre=nombre, grupo=grupos[grupo])
        return etiquetas[(grupo, nombre)]

    # Fechas de alta verosímiles: el último tomo de una serie en curso es de
    # estos meses; el de una completa, de antes. Así «lo más nuevo» de cada
    # fila mezcla series en vez de mostrar doce tomos de la última cargada.
    azar, hoy, ahora = carga.azar, carga.hoy, timezone.now()
    altas = []
    for serie in series:
        tipo, grupo, nombre = CATEGORIAS[categoria(serie)]
        propias = [etiqueta(grupo, nombre)] if grupo else []
        marcas = str(serie.get("etiquetas") or "").lower()
        propias += [etiqueta("Estado de la serie", v) for k, v in ESTADOS.items() if k in marcas]
        propias += [etiqueta("Colección", v) for k, v in COLECCIONES.items() if k in marcas]
        tomos = cantidad_de_tomos(serie)
        en_curso = "en curso" in marcas
        dias = azar.randint(0, 75) if en_curso else azar.randint(120, 2200)
        ultimo = ahora - timedelta(days=dias)
        portada = carga.portada(serie)
        for volumen in range(1, tomos + 1):
            producto = carga.producto_editorial(
                titulo=serie["titulo"],
                volumen=volumen,
                editorial=ivrea,
                tipo=tipos[tipo],
                formato=formatos[formato(serie)],
                autor=" ".join(str(serie.get("autor") or "").split()).replace(" ,", ","),
                descripcion=sinopsis(serie.get("sinopsis")),
                portada=portada,
                etiquetas=propias,
                ultimo=volumen == tomos,
                en_curso=en_curso,
            )
            producto.creado_en = ultimo - timedelta(days=75 * (tomos - volumen))
            altas.append(producto)
    Producto.objects.bulk_update(altas, ["creado_en"], batch_size=1000)

    proveedor = Proveedor.objects.create(
        razon_social="Editorial Ivrea",
        correo_comercial="novedades@ivrea.demo",
        nombre_contacto="Comercial Ivrea",
        editorial=ivrea,
        tipo_por_defecto=tipos["Manga"],
        procesa_novedades=True,
    )
    for indice in range(3):
        correo = armar(
            proveedor.correo_comercial,
            "casilla@longbox.demo",
            renglones_al_azar(azar, series, 6, hoy),
            hoy - timedelta(days=indice * 7),
            message_id=f"<presentacion-{indice}@ivrea.demo>",
        )
        services.ingerir(bytes(correo), nombre_archivo=f"novedades-{indice}.eml")

    def destacadas(demografia, cantidad):
        """Las series más largas de la demografía, que suelen ser las más conocidas."""
        propias = [
            s
            for s in series
            if CATEGORIAS[categoria(s)][2] == demografia and s.get("portada_archivo")
        ]
        return sorted(propias, key=cantidad_de_tomos, reverse=True)[:cantidad]

    for indice, (demografia, valor) in enumerate(zip(DEMOGRAFIAS, (15, 20, 10), strict=True)):
        serie = destacadas(demografia, 1)[0]
        producto = ProductoEditorial.objects.get(titulo=serie["titulo"], volumen=1)
        Oferta.objects.create(
            descripcion=f"Para empezar {producto.titulo}",
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=14 + indice * 7),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal(valor),
            alcance=Oferta.PRODUCTO,
            producto=producto,
            estado=Oferta.ACTIVA,
        )

    filas = []
    for orden, demografia in enumerate(DEMOGRAFIAS, start=1):
        filas.append(FilaPortada(etiqueta=etiquetas[("Demografía", demografia)], orden=orden))
        rutas = [DATOS / "portadas" / s["portada_archivo"] for s in destacadas(demografia, 8)]
        Banner.objects.create(imagen=_banner(rutas, demografia.lower()), posicion=orden - 1)
    filas.append(
        FilaPortada(
            etiqueta=etiquetas[("Estado de la serie", "Serie completa")],
            titulo="Series completas",
            orden=len(filas) + 1,
        )
    )
    filas.append(FilaPortada(grupo=grupos["Género"], titulo="BL y Yuri", orden=len(filas) + 1))
    FilaPortada.objects.bulk_create(filas)

    print(
        f"Cargado: {Usuario.objects.count()} cuentas, {len(series)} series, {len(altas)} tomos "
        f"de Ivrea, {Oferta.objects.count()} ofertas, {Banner.objects.count()} banners, "
        f"{FilaPortada.objects.count()} filas de portada"
    )


if __name__ == "__main__":
    accion, archivo = sys.argv[1], sys.argv[2]
    {"exportar": exportar, "cargar": cargar}[accion](archivo)
