"""Puebla `longbox_demo` con un volumen realista y reproducible (plan 00, apartado 2).

    python scripts/demo/poblar.py

Requiere la base recién migrada (`manejar.py migrate`) y el Excel de Ivrea
(`raspar_ivrea.py`). Con la misma semilla, dos corridas dan los mismos datos.

Qué crea:

- **Personal y clientes.** 3 Administradores, 7 Cajeros y 500 clientes (RNF-07).
  Todas las cuentas tienen la contraseña `Demo-2026!`; los correos son
  `admin1@longbox.demo`, `cajero1@…`, `cliente001@…`.
- **Catálogos.** Editoriales, tipos de los dos rubros, formatos con medidas,
  grupos de etiquetas y etiquetas tomadas de los géneros y demografías de Ivrea,
  y la tabla de precios de referencia.
- **20 000 productos.** Los tomos de las series **reales** de Ivrea, con su
  autor, sinopsis, etiquetas y portada (procesada como manda RNF-05). Hasta
  completar 14 000 editoriales, series sintéticas de otras editoriales, y 6 000
  productos no editoriales sintéticos. Todo lo sintético lo dice en su
  descripción. ISBN y códigos de barras sintéticos con dígito verificador válido.
- **50 proveedores y 1 000 correos** en la cola, en todos sus estados. Los
  correos entran por la misma ingesta que usa el sistema (`services.ingerir`).
- **100 000 entradas de auditoría**, repartidas en el último año.
- Unas ofertas vigentes, algunos carritos y la identidad visual configurada.

Sólo corre sobre `longbox_demo` (`entorno.preparar`).
"""

import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from entorno import SALIDA, preparar

SEMILLA = 20261005
CONTRASENA = "Demo-2026!"
TOTAL_EDITORIALES = 14_000
TOTAL_NO_EDITORIALES = 6_000
TOTAL_AUDITORIA = 100_000
TOTAL_CORREOS = 1_000
DATOS = Path(__file__).resolve().parent / "datos"
SINTETICO = "Dato sintético de la demostración."


def _hash(_):
    preparar(django_setup=False)
    import django

    django.setup()
    from django.contrib.auth.hashers import make_password

    return make_password(CONTRASENA)


def hashes(cantidad):
    """Un hash distinto por cuenta, con su sal; en paralelo: PBKDF2 es lento a propósito."""
    with ProcessPoolExecutor() as grupo:
        return list(grupo.map(_hash, range(cantidad), chunksize=8))


def _uno(modelo, nombre, **datos):
    """El registro con ese nombre, sin distinguir mayúsculas; si no existe, se crea.

    Las migraciones ya siembran algunos catálogos (el tipo «Manga», por ejemplo),
    y los nombres son únicos sin distinguir mayúsculas.
    """
    existente = modelo.objects.filter(nombre__iexact=nombre).first()
    if existente is not None:
        for campo, valor in datos.items():
            setattr(existente, campo, valor)
        existente.save()
        return existente
    return modelo.objects.create(nombre=nombre, **datos)


def con_verificador_13(cuerpo12):
    suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(cuerpo12))
    return cuerpo12 + str((10 - suma % 10) % 10)


class Poblador:
    def __init__(self):
        from django.utils import timezone

        self.azar = random.Random(SEMILLA)  # nosec B311 - semilla fija para datos reproducibles
        self.ahora = timezone.now()
        self.hoy = timezone.localdate()
        self.isbn = 0
        self.ean = 0
        self.tiempos = {}

    def medir(self, nombre, funcion):
        inicio = time.perf_counter()
        resultado = funcion()
        self.tiempos[nombre] = round(time.perf_counter() - inicio, 1)
        print(f"  {nombre}: {self.tiempos[nombre]} s", flush=True)
        return resultado

    def siguiente_isbn(self):
        self.isbn += 1
        return con_verificador_13(f"978987{self.isbn:06d}")

    def siguiente_ean(self):
        self.ean += 1
        return con_verificador_13(f"779{self.ean:09d}")

    # -------------------------------------------------------------------
    def cuentas(self):
        from apps.accounts.models import Usuario

        planes = [("administrador", f"admin{i}") for i in range(1, 4)]
        planes += [("cajero", f"cajero{i}") for i in range(1, 8)]
        planes += [("cliente", f"cliente{i:03d}") for i in range(1, 501)]
        claves = hashes(len(planes))
        nombres = [
            "Ana",
            "Bruno",
            "Carla",
            "Diego",
            "Elena",
            "Facundo",
            "Gala",
            "Hernán",
            "Inés",
            "Julián",
        ]
        apellidos = ["Pérez", "Gómez", "Sosa", "Ibáñez", "Núñez", "Fernández", "Ruiz", "Acosta"]
        Usuario.objects.bulk_create(
            [
                Usuario(
                    username=usuario,
                    email=f"{usuario}@longbox.demo",
                    first_name=self.azar.choice(nombres),
                    last_name=self.azar.choice(apellidos),
                    rol=rol,
                    estado=Usuario.ACTIVO,
                    password=clave,
                )
                for (rol, usuario), clave in zip(planes, claves, strict=True)
            ]
        )
        self.personal = list(Usuario.objects.exclude(rol="cliente"))
        self.clientes = list(Usuario.objects.filter(rol="cliente"))

    # -------------------------------------------------------------------
    def catalogos(self, series):
        from apps.catalog.models import (
            Editorial,
            Etiqueta,
            Formato,
            GrupoEtiqueta,
            Producto,
            TablaPrecioReferencia,
            Tipo,
        )

        nombres_editoriales = [
            "Ivrea",
            "Panini Manga",
            "Ovni Press",
            "Kemuri",
            "Distrito Manga",
            "Planeta Cómic",
            "ECC Ediciones",
            "Utopía",
            "Moztros",
            "Hotel de las Ideas",
        ]
        self.editoriales = {n: _uno(Editorial, nombre=n) for n in nombres_editoriales}
        self.tipos = {
            n: _uno(Tipo, nombre=n, clase=Producto.EDITORIAL, usa_formato=True)
            for n in ("Manga", "Cómic", "Novela gráfica", "Libro ilustrado")
        }
        self.tipos_no_editoriales = {
            n: _uno(Tipo, nombre=n, clase=Producto.NO_EDITORIAL, usa_formato=False)
            for n in ("Figura", "TCG", "Merchandising", "Insumo")
        }
        medidas = {
            "B6": "12,8 × 18,2 cm",
            "Tankoubon": "11,5 × 17,5 cm",
            "A5": "14,8 × 21 cm",
            "Kanzenban": "15 × 21 cm",
            "Big Size": "17 × 26 cm",
            "Deluxe": "Tapa dura, 18 × 26 cm",
            "Rústica": "17 × 26 cm",
        }
        self.formatos = {
            n: _uno(Formato, nombre=n, descripcion=d, aplica_a_todos=True)
            for n, d in medidas.items()
        }
        self.pvp_formato = {
            "B6": 14900,
            "Tankoubon": 16500,
            "A5": 21900,
            "Kanzenban": 28900,
            "Big Size": 34900,
            "Deluxe": 45900,
            "Rústica": 24900,
        }
        self.precios = {}
        for editorial in self.editoriales.values():
            recargo = Decimal(self.azar.choice([0, 500, 1000, 1500]))
            for tipo in self.tipos.values():
                for nombre, formato in self.formatos.items():
                    fila = TablaPrecioReferencia.objects.create(
                        editorial=editorial,
                        tipo=tipo,
                        formato=formato,
                        pvp=Decimal(self.pvp_formato[nombre]) + recargo,
                    )
                    self.precios[(editorial.pk, tipo.pk, formato.pk)] = fila

        grupos = {
            n: _uno(GrupoEtiqueta, nombre=n)
            for n in ("Demografía", "Género", "Estado de la serie", "Franquicia", "Escala")
        }
        self.etiquetas = {}

        def etiqueta(grupo, nombre):
            nombre = " ".join(str(nombre).split())[:80]
            clave = (grupo, nombre.lower())
            if nombre and clave not in self.etiquetas:
                self.etiquetas[clave] = Etiqueta.objects.filter(
                    nombre__iexact=nombre, grupo=grupos[grupo]
                ).first() or Etiqueta.objects.create(nombre=nombre, grupo=grupos[grupo])
            return self.etiquetas.get(clave)

        self.etiqueta = etiqueta
        for serie in series:
            etiqueta("Demografía", (serie.get("demografia") or "").title())
            for genero in str(serie.get("generos") or "").replace("Manga ", "").split(","):
                etiqueta("Género", genero.strip().title())
            for estado in str(serie.get("etiquetas") or "").split(","):
                etiqueta("Estado de la serie", estado.strip())
        self.franquicias = [s["titulo"] for s in series[:120]]
        for franquicia in self.franquicias:
            etiqueta("Franquicia", franquicia)
        for escala in ("1/4", "1/6", "1/7", "1/8", "Nendoroid", "Pop Up Parade", "Figma"):
            etiqueta("Escala", escala)

    # -------------------------------------------------------------------
    def portada(self, serie):
        """La portada de Ivrea procesada como manda RNF-05, una por serie."""
        from django.core.files.base import File
        from django.core.files.storage import default_storage

        from apps.core.imagenes import ImagenInvalida, procesar

        archivo = serie.get("portada_archivo")
        if not archivo or not (DATOS / "portadas" / archivo).exists():
            return ""
        try:
            with open(DATOS / "portadas" / archivo, "rb") as original:
                procesada = procesar(File(original))
        except ImagenInvalida:
            return ""
        return default_storage.save(f"portadas/{serie['slug']}.webp", procesada)

    def estado_y_stock(self, ultimo, en_curso):
        from apps.catalog.models import Producto

        tirada = self.azar.random()
        if ultimo and en_curso and tirada < 0.5:
            return Producto.PRE_VENTA, 0, self.hoy + timedelta(days=self.azar.randint(7, 60))
        if tirada < 0.05:
            return Producto.AGOTADO, 0, None
        if tirada < 0.07:
            return Producto.DESCATALOGADO, 0, None
        return Producto.ACTIVO, self.azar.choice([0, 1, 2, 3, 4, 5, 6, 8, 12]), None

    def producto_editorial(
        self,
        *,
        titulo,
        volumen,
        editorial,
        tipo,
        formato,
        autor,
        descripcion,
        portada,
        etiquetas,
        ultimo,
        en_curso,
    ):
        from apps.catalog.models import ProductoEditorial

        estado, stock, llegada = self.estado_y_stock(ultimo, en_curso)
        fila = self.precios[(editorial.pk, tipo.pk, formato.pk)]
        producto = ProductoEditorial.objects.create(
            titulo=titulo[:200],
            volumen=volumen,
            isbn=self.siguiente_isbn(),
            editorial=editorial,
            tipo=tipo,
            formato=formato,
            origen=ProductoEditorial.NACIONAL,
            autor=(autor or "")[:200],
            estado=estado,
            stock=stock,
            fecha_llegada=llegada,
            precio=fila.pvp,
            precio_base=fila.pvp,
            precio_referencia=fila,
            descripcion=descripcion or "",
            portada=portada,
        )
        etiquetas = [e for e in etiquetas if e]
        if etiquetas:
            producto.etiquetas.set(etiquetas)
        return producto

    def editoriales_de_ivrea(self, series):
        ivrea, manga = self.editoriales["Ivrea"], self.tipos["Manga"]
        creados = 0
        vistos = set()
        self.repetidas = []
        for serie in series:
            # Ivrea publica algunas series con el mismo título (otra edición, la
            # novela): el tomo 1 de las dos sería la misma edición para el
            # sistema. Se carga la primera y se informa la otra.
            clave = " ".join(serie["titulo"].split()).lower()
            if clave in vistos:
                self.repetidas.append(serie["titulo"])
                continue
            vistos.add(clave)
            texto = " ".join(
                str(serie.get(c) or "") for c in ("formato", "estado_argentina", "sinopsis")
            )
            formato = self.formatos[
                (
                    "B6"
                    if "B6" in texto
                    else "Kanzenban" if "KANZENBAN" in texto.upper() else "Tankoubon"
                )
            ]
            tomos = serie.get("tomos_argentina") or self.azar.randint(1, 10)
            tomos = max(1, min(int(tomos), 120))
            en_curso = "curso" in str(serie.get("estado_argentina") or "").lower()
            portada = self.portada(serie)
            etiquetas = [
                self.etiqueta("Demografía", (serie.get("demografia") or "").title()),
                *[
                    self.etiqueta("Género", g.strip().title())
                    for g in str(serie.get("generos") or "").replace("Manga ", "").split(",")
                ],
                *[
                    self.etiqueta("Estado de la serie", e.strip())
                    for e in str(serie.get("etiquetas") or "").split(",")
                ],
            ]
            for volumen in range(1, tomos + 1):
                self.producto_editorial(
                    titulo=serie["titulo"],
                    volumen=volumen,
                    editorial=ivrea,
                    tipo=manga,
                    formato=formato,
                    autor=serie.get("autor"),
                    descripcion=serie.get("sinopsis"),
                    portada=portada,
                    etiquetas=etiquetas,
                    ultimo=volumen == tomos,
                    en_curso=en_curso,
                )
                creados += 1
        return creados

    def editoriales_sinteticas(self, faltan):
        palabras = [
            "Noche",
            "Acero",
            "Cielo",
            "Ruido",
            "Sombra",
            "Brasa",
            "Cristal",
            "Hueso",
            "Marea",
            "Neón",
            "Óxido",
            "Ceniza",
            "Trueno",
            "Vidrio",
            "Ámbar",
            "Niebla",
        ]
        sufijos = ["Saga", "Crónicas", "Protocolo", "Distrito", "Leyenda", "Expediente", "Ciclo"]
        otras = [e for n, e in self.editoriales.items() if n != "Ivrea"]
        creados, numero = 0, 0
        while creados < faltan:
            numero += 1
            titulo = f"{self.azar.choice(sufijos)} {self.azar.choice(palabras)} {numero}"
            editorial = self.azar.choice(otras)
            tipo = self.azar.choice(list(self.tipos.values()))
            formato = self.formatos[self.azar.choice(list(self.formatos))]
            tomos = min(self.azar.randint(1, 18), faltan - creados)
            for volumen in range(1, tomos + 1):
                self.producto_editorial(
                    titulo=titulo,
                    volumen=volumen,
                    editorial=editorial,
                    tipo=tipo,
                    formato=formato,
                    autor="Autor sintético",
                    descripcion=SINTETICO,
                    portada="",
                    etiquetas=[],
                    ultimo=volumen == tomos,
                    en_curso=self.azar.random() < 0.4,
                )
                creados += 1
        return creados

    def no_editoriales(self):
        from apps.catalog.models import Producto, ProductoNoEditorial

        plantillas = {
            "Figura": (
                ["Figura Pop Up Parade", "Figura Nendoroid", "Figura escala 1/7", "Figma"],
                ["Good Smile", "Bandai", "Banpresto", "Kotobukiya"],
                [39900, 59900, 129900, 189900],
            ),
            "TCG": (
                ["Sobre de expansión", "Mazo inicial", "Caja de sobres"],
                ["Bandai", "Konami", "Bushiroad"],
                [4900, 18900, 89900],
            ),
            "Merchandising": (
                ["Llavero acrílico", "Póster", "Taza", "Remera"],
                ["Ivrea Store", "Funko", "Abystyle"],
                [5900, 7900, 12900, 21900],
            ),
            "Insumo": (
                ["Fundas x100", "Caja para mazo", "Carpeta de 9 bolsillos", "Protector de tomo"],
                ["Dragon Shield", "Ultra Pro", "Ultimate Guard"],
                [8900, 12900, 24900, 2900],
            ),
        }
        for indice in range(TOTAL_NO_EDITORIALES):
            nombre_tipo = list(plantillas)[indice % 4]
            productos, marcas, precios = plantillas[nombre_tipo]
            franquicia = self.azar.choice(self.franquicias)
            tirada = self.azar.random()
            estado = Producto.AGOTADO if tirada < 0.05 else Producto.ACTIVO
            producto = ProductoNoEditorial.objects.create(
                titulo=f"{self.azar.choice(productos)} · {franquicia} #{indice + 1}"[:200],
                tipo=self.tipos_no_editoriales[nombre_tipo],
                marca=self.azar.choice(marcas),
                codigo_barras=self.siguiente_ean(),
                estado=estado,
                stock=0 if estado == Producto.AGOTADO else self.azar.randint(0, 20),
                precio=Decimal(self.azar.choice(precios)),
                descripcion=SINTETICO,
            )
            producto.etiquetas.set([self.etiqueta("Franquicia", franquicia)])
        return TOTAL_NO_EDITORIALES

    # -------------------------------------------------------------------
    def proveedores_y_correos(self, series):
        from enviar_novedades import armar, renglones_al_azar

        from apps.suppliers import services
        from apps.suppliers.models import CorreoProveedor, Proveedor

        proveedores = []
        for indice in range(50):
            nombre = (
                list(self.editoriales)[indice]
                if indice < len(self.editoriales)
                else f"Distribuidora {indice + 1}"
            )
            editorial = self.editoriales.get(nombre)
            proveedores.append(
                Proveedor.objects.create(
                    razon_social=nombre if editorial else f"{nombre} S.R.L.",
                    correo_comercial=f"novedades{indice + 1}@proveedores.demo",
                    nombre_contacto=f"Contacto {indice + 1}",
                    estado=Proveedor.INACTIVO if indice % 17 == 16 else Proveedor.ACTIVO,
                    procesa_novedades=indice % 9 != 8,
                    editorial=editorial,
                    tipo_por_defecto=self.tipos["Manga"],
                )
            )
        validos = [p for p in proveedores if p.estado == Proveedor.ACTIVO and p.procesa_novedades]
        for indice in range(TOTAL_CORREOS):
            proveedor = self.azar.choice(validos)
            fecha = self.hoy - timedelta(days=self.azar.randint(0, 120))
            correo = armar(
                proveedor.correo_comercial,
                "casilla@longbox.demo",
                renglones_al_azar(self.azar, series, self.azar.randint(3, 12), fecha),
                fecha,
                message_id=f"<demo-{indice:05d}@proveedores.demo>",
            )
            services.ingerir(bytes(correo), nombre_archivo=f"demo-{indice:05d}.eml")
        reparto = [
            (CorreoProveedor.PENDIENTE, 0.40),
            (CorreoProveedor.PROCESADO, 0.35),
            (CorreoProveedor.FALLIDO, 0.10),
            (CorreoProveedor.DESCARTADO, 0.10),
            (CorreoProveedor.EN_PROCESO, 0.05),
        ]
        ids = list(CorreoProveedor.objects.order_by("pk").values_list("pk", flat=True))
        self.azar.shuffle(ids)
        inicio = 0
        for estado, parte in reparto:
            cantidad = round(len(ids) * parte)
            tramo = ids[inicio : inicio + cantidad]
            inicio += cantidad
            cambios = {"estado": estado}
            if estado == CorreoProveedor.FALLIDO:
                cambios["motivo"] = "El modelo de lenguaje no respondió a tiempo."
            CorreoProveedor.objects.filter(pk__in=tramo).update(**cambios)
        return len(ids)

    # -------------------------------------------------------------------
    def auditoria(self):
        """Inserta con la fecha elegida.

        `ocurrido_en` es auto_now_add: se apaga sólo en este proceso.
        """
        from apps.core.models import RegistroAuditoria

        campo = RegistroAuditoria._meta.get_field("ocurrido_en")
        campo.auto_now_add = False
        acciones = [valor for valor, _ in RegistroAuditoria.ACCION_CHOICES]
        lote = []
        for indice in range(TOTAL_AUDITORIA):
            actor = self.azar.choice(self.personal)
            lote.append(
                RegistroAuditoria(
                    accion=self.azar.choice(acciones),
                    actor=actor,
                    actor_email=actor.email,
                    ip=f"10.0.{self.azar.randint(0, 9)}.{self.azar.randint(1, 254)}",
                    detalle=f"Entrada histórica {indice + 1} de la demostración.",
                    ocurrido_en=self.ahora - timedelta(minutes=self.azar.randint(1, 525_600)),
                )
            )
            if len(lote) == 5000:
                RegistroAuditoria.objects.bulk_create(lote)
                lote = []
        if lote:
            RegistroAuditoria.objects.bulk_create(lote)
        campo.auto_now_add = True
        return TOTAL_AUDITORIA

    # -------------------------------------------------------------------
    def tienda(self):
        from apps.catalog.models import Oferta, Producto
        from apps.core.models import IdentidadVisual
        from apps.tienda.models import Carrito, LineaCarrito

        identidad = IdentidadVisual.obtener()
        identidad.nombre_tienda = "Longbox"
        identidad.correo_contacto = "hola@longbox.demo"
        identidad.actualizado_en = self.ahora
        identidad.save()
        Oferta.objects.create(
            descripcion="Semana del manga",
            fecha_inicio=self.hoy - timedelta(days=2),
            fecha_vencimiento=self.hoy + timedelta(days=5),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("15"),
            alcance=Oferta.TIPO,
            tipo=self.tipos["Manga"],
            estado=Oferta.ACTIVA,
        )
        disponibles = list(
            Producto.objects.filter(estado=Producto.ACTIVO, stock__gt=0).values_list(
                "pk", "precio"
            )[:2000]
        )
        for cliente in self.clientes[:80]:
            carrito = Carrito.objects.create(usuario=cliente, persistencia=Carrito.PERSISTENTE)
            for pk, precio in self.azar.sample(disponibles, self.azar.randint(1, 4)):
                LineaCarrito.objects.create(
                    carrito=carrito,
                    producto_id=pk,
                    cantidad=1,
                    precio_vigente=precio,
                    precio_visto=precio,
                )


def main():
    import argparse

    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--excel", type=Path, default=DATOS / "ivrea.xlsx")
    opciones = argumentos.parse_args()
    preparar()
    from enviar_novedades import series as leer_series

    from apps.catalog.models import Producto

    if Producto.objects.exists():
        raise SystemExit(
            "La base ya tiene productos. Restaurala (restaurar.py) o recreala antes de poblar."
        )
    series = sorted(leer_series(opciones.excel), key=lambda s: s["slug"])
    print(f"Series de Ivrea en el Excel: {len(series)}")

    poblador = Poblador()
    poblador.medir("cuentas", poblador.cuentas)
    poblador.medir("catálogos", lambda: poblador.catalogos(series))
    ivrea = poblador.medir("tomos de Ivrea", lambda: poblador.editoriales_de_ivrea(series))
    poblador.medir(
        "editoriales sintéticos",
        lambda: poblador.editoriales_sinteticas(max(0, TOTAL_EDITORIALES - ivrea)),
    )
    poblador.medir("no editoriales", poblador.no_editoriales)
    poblador.medir("proveedores y correos", lambda: poblador.proveedores_y_correos(series))
    poblador.medir("auditoría", poblador.auditoria)
    poblador.medir("tienda", poblador.tienda)

    from apps.accounts.models import Usuario
    from apps.core.models import RegistroAuditoria
    from apps.suppliers.models import CorreoProveedor, Proveedor

    resumen = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "semilla": SEMILLA,
        "usuarios": Usuario.objects.count(),
        "productos": Producto.objects.count(),
        "tomos_de_ivrea": ivrea,
        "series_repetidas_omitidas": poblador.repetidas,
        "proveedores": Proveedor.objects.count(),
        "correos": CorreoProveedor.objects.count(),
        "auditoria": RegistroAuditoria.objects.count(),
        "tiempos_s": poblador.tiempos,
    }
    (SALIDA / "poblar.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(resumen)


if __name__ == "__main__":
    sys.exit(main())
