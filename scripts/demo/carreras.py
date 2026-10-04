"""Acto 4 · Concurrencia con hilos reales contra PostgreSQL.

    python scripts/demo/carreras.py                 # todas, 20 repeticiones
    python scripts/demo/carreras.py D4-04 --veces 50

Cada carrera suelta dos pedidos a la vez (una barrera los larga juntos), por la
dirección real, y repite. En todas el criterio tiene dos partes: el efecto
declarado se cumple **y ninguna respuesta es un error 500**. La carrera del
último Administrador (D4-01) vive en la suite
(`apps/accounts/tests/test_concurrencia_ultimo_administrador.py`).

- D4-02 · Dos aprobaciones del mismo correo (CO-017): una procesa, la otra
  informa el estado.
- D4-03 · El mismo correo ingerido dos veces (I-16): una sola fila. Reprocesar uno
  procesado (CO-019): termina en Procesado o Falló, sin tocar los confirmados.
- D4-04 · Doble clic en el alta de una editorial: una sola editorial.
- D4-05 · Dos pestañas suman el mismo producto al carrito (CO-083): una línea con
  la suma.
- D4-06 · Dos ofertas solapadas registradas a la vez (I-20): una sola oferta.

Escribe en la base: después de este acto se corre `restaurar.py`.
"""

import argparse
import sys
import threading
import time
from datetime import date, timedelta

from entorno import SALIDA, preparar

RESULTADOS = []


def navegador(usuario=None):
    from django.test import Client

    cliente = Client()
    cliente.defaults.update({"HTTP_HOST": "127.0.0.1", "wsgi.url_scheme": "https"})
    cliente.raise_request_exception = False
    if usuario is not None:
        cliente.force_login(usuario)
    return cliente


def a_la_vez(*pedidos):
    from django.db import connection

    barrera = threading.Barrier(len(pedidos))
    respuestas = [None] * len(pedidos)

    def correr(indice, pedido):
        try:
            barrera.wait()
            respuestas[indice] = pedido()
        finally:
            connection.close()

    hilos = [threading.Thread(target=correr, args=par) for par in enumerate(pedidos)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=120)
    return respuestas


def registrar(codigo, que, veces, ok, quinientos, detalle, segundos):
    RESULTADOS.append((codigo, que, veces, ok, quinientos, detalle, segundos))
    marca = "OK   " if ok == veces and not quinientos else "FALLA"
    print(
        f"[{marca}] {codigo} · {que}: {ok}/{veces} correctas, {quinientos} respuestas 500 "
        f"({segundos:.1f} s){' · ' + detalle if detalle else ''}"
    )


def administradores():
    from apps.accounts.models import Usuario

    return list(Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)[:2])


# ---------------------------------------------------------------------------
def d4_02(veces):
    from django.urls import reverse

    from apps.suppliers.models import CorreoProveedor

    a, b = administradores()
    ok = quinientos = 0
    finales = set()
    for correo in CorreoProveedor.objects.filter(estado=CorreoProveedor.PENDIENTE)[:veces]:
        url = reverse("suppliers:correo_aprobar", args=[correo.pk])
        sa, sb = navegador(a), navegador(b)
        respuestas = a_la_vez(
            lambda s=sa: s.post(url, secure=True), lambda s=sb: s.post(url, secure=True)
        )
        quinientos += sum(r.status_code >= 500 for r in respuestas)
        correo.refresh_from_db()
        finales.add(correo.estado)
        ok += correo.estado != CorreoProveedor.PENDIENTE
    return ok, quinientos, f"estados finales: {sorted(finales)}"


def d4_03(veces):
    from django.urls import reverse
    from enviar_novedades import armar

    from apps.suppliers import services
    from apps.suppliers.models import CorreoProveedor

    a, _ = administradores()
    proveedor_correo = CorreoProveedor.objects.first().remitente
    ok = quinientos = 0
    for indice in range(veces):
        bruto = bytes(
            armar(
                proveedor_correo,
                "casilla@longbox.demo",
                [],
                date.today(),
                message_id=f"<idempotencia-{indice}-{time.time_ns()}@demo>",
            )
        )
        antes = CorreoProveedor.objects.count()
        primero = services.ingerir(bruto)
        segundo = services.ingerir(bruto)
        despues = CorreoProveedor.objects.count()
        ok += (
            despues == antes + 1
            and segundo.correo is not None
            and segundo.correo.pk == primero.correo.pk
        )
    # CO-019: reprocesar un Procesado vuelve a extraer y termina en Procesado o en
    # Falló el procesamiento; los borradores confirmados no se tocan.
    from apps.catalog.models import BorradorProducto

    procesados = list(CorreoProveedor.objects.filter(estado=CorreoProveedor.PROCESADO)[:veces])
    sesion = navegador(a)
    conformes = 0
    for correo in procesados:
        confirmados = set(
            BorradorProducto.objects.filter(
                correo=correo, estado=BorradorProducto.CONFIRMADO
            ).values_list("pk", flat=True)
        )
        respuesta = sesion.post(
            reverse("suppliers:correo_reprocesar", args=[correo.pk]), secure=True
        )
        quinientos += respuesta.status_code >= 500
        correo.refresh_from_db()
        siguen = set(
            BorradorProducto.objects.filter(
                correo=correo, estado=BorradorProducto.CONFIRMADO
            ).values_list("pk", flat=True)
        )
        conformes += (
            correo.estado in (CorreoProveedor.PROCESADO, CorreoProveedor.FALLIDO)
            and siguen == confirmados
        )
    return (
        min(ok, conformes),
        quinientos,
        f"ingesta repetida {ok}/{veces}, reproceso conforme a CO-019 "
        f"{conformes}/{len(procesados)}",
    )


def d4_04(veces):
    from django.urls import reverse

    from apps.catalog.models import Editorial

    a, b = administradores()
    url = reverse("catalog:editorial_crear")
    ok = quinientos = 0
    for indice in range(veces):
        nombre = f"Doble clic {indice} {time.time_ns()}"
        sa, sb = navegador(a), navegador(a)
        respuestas = a_la_vez(
            lambda s=sa: s.post(url, {"nombre": nombre}, secure=True),
            lambda s=sb: s.post(url, {"nombre": nombre}, secure=True),
        )
        quinientos += sum(r.status_code >= 500 for r in respuestas)
        ok += Editorial.objects.filter(nombre__iexact=nombre).count() == 1
    return ok, quinientos, ""


def d4_05(veces):
    from django.urls import reverse

    from apps.accounts.models import Usuario
    from apps.catalog.models import Producto
    from apps.tienda.models import LineaCarrito

    clientes = list(Usuario.objects.filter(rol=Usuario.CLIENTE, carrito__isnull=True)[:veces])
    productos = list(
        Producto.objects.filter(estado=Producto.ACTIVO, stock__gte=5, solo_adultos=False)[:veces]
    )
    ok = quinientos = 0
    for cliente, producto in zip(clientes, productos, strict=False):
        url = reverse("tienda:agregar", args=[producto.pk])
        pestana_1, pestana_2 = navegador(cliente), navegador(cliente)
        respuestas = a_la_vez(
            lambda s=pestana_1: s.post(url, {"cantidad": 1}, secure=True),
            lambda s=pestana_2: s.post(url, {"cantidad": 1}, secure=True),
        )
        quinientos += sum(r.status_code >= 500 for r in respuestas)
        lineas = list(LineaCarrito.objects.filter(carrito__usuario=cliente, producto=producto))
        ok += len(lineas) == 1 and lineas[0].cantidad == 2
    return ok, quinientos, ""


def d4_06(veces):
    from django.urls import reverse
    from django.utils import timezone

    from apps.catalog.models import Oferta, Producto

    a, b = administradores()
    url = reverse("catalog:oferta_alta")
    hoy = timezone.localdate()
    productos = list(Producto.objects.filter(estado=Producto.ACTIVO, ofertas__isnull=True)[:veces])
    ok = quinientos = 0
    for producto in productos:
        datos = {
            "descripcion": "Carrera",
            "fecha_inicio": (hoy + timedelta(days=1)).isoformat(),
            "fecha_vencimiento": (hoy + timedelta(days=5)).isoformat(),
            "tipo_descuento": Oferta.PORCENTAJE,
            "valor": "10",
            "alcance": Oferta.PRODUCTO,
            "producto": f"{producto.codigo} — {producto.titulo}",
        }
        sa, sb = navegador(a), navegador(b)
        respuestas = a_la_vez(
            lambda s=sa: s.post(url, datos, secure=True),
            lambda s=sb: s.post(url, datos, secure=True),
        )
        quinientos += sum(r.status_code >= 500 for r in respuestas)
        ok += Oferta.objects.filter(producto=producto).count() == 1
    return ok, quinientos, ""


CARRERAS = {
    "D4-02": ("Dos aprobaciones del mismo correo", d4_02),
    "D4-03": ("Ingesta repetida y reproceso de un procesado", d4_03),
    "D4-04": ("Doble clic en el alta de una editorial", d4_04),
    "D4-05": ("Dos pestañas suman el mismo producto al carrito", d4_05),
    "D4-06": ("Dos ofertas solapadas a la vez", d4_06),
}


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("codigos", nargs="*")
    argumentos.add_argument("--veces", type=int, default=20)
    opciones = argumentos.parse_args()
    preparar()
    for codigo in opciones.codigos or list(CARRERAS):
        que, funcion = CARRERAS[codigo]
        inicio = time.perf_counter()
        try:
            ok, quinientos, detalle = funcion(opciones.veces)
        except Exception as error:  # noqa: BLE001 - una carrera rota no tapa a las demás
            ok, quinientos, detalle = 0, 0, f"error: {type(error).__name__}: {error}"
        registrar(
            codigo, que, opciones.veces, ok, quinientos, detalle, time.perf_counter() - inicio
        )
    lineas = [
        "| Código | Carrera | Correctas | Respuestas 500 | Detalle | Tiempo |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for codigo, que, veces, ok, quinientos, detalle, segundos in RESULTADOS:
        lineas.append(
            f"| {codigo} | {que} | {ok}/{veces} | {quinientos} | {detalle} | {segundos:.1f} s |"
        )
    (SALIDA / "carreras.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return 0 if all(r[3] == r[2] and not r[4] for r in RESULTADOS) else 1


if __name__ == "__main__":
    sys.exit(main())
