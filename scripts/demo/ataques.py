"""Acto 3 · Ataques contra el sistema real, cada uno con su veredicto.

    python scripts/demo/ataques.py            # todos
    python scripts/demo/ataques.py D3-02 D3-05

Corre dentro del proceso, con los ajustes de producción sobre `longbox_demo` y
por HTTPS. **Escribe en la base** (intentos fallidos, una editorial con
`<script>`, banners): después de este acto se corre `restaurar.py`.

- D3-02 · 20 inicios de sesión fallidos: bloqueo en el quinto, entrada en
  auditoría, y ni la contraseña correcta entra (CO-114).
- D3-03 · Recuperar la contraseña de una cuenta que existe y de una que no:
  respuestas idénticas byte a byte, salvo el token CSRF (CO-117).
- D3-04 · SQL en búsquedas y `<script>` en un nombre: búsqueda 200, script escapado.
- D3-05 · POST sin token CSRF: 403 y nada cambia.
- D3-06 · Tocar la línea del carrito de otro: 404 y la línea ajena intacta.
- D3-07 · Ejecutable renombrado, imagen de 20 MB, SVG con script y nombre con
  `../`: rechazo con mensaje; lo válido se guarda procesado (RNF-05).
- D3-08 · Dos cuentas con la misma contraseña: hashes distintos (RNF-04).
- D3-09 · Cambiar el rol de una cuenta con sesión abierta: su próxima petición ya
  no está autenticada (CO-121).
"""

import io
import re
import sys
import time

from entorno import SALIDA, preparar

CONTRASENA = "Demo-2026!"
RESULTADOS = []


def navegador(**extra):
    from django.test import Client

    cliente = Client(**extra)
    cliente.defaults.update({"HTTP_HOST": "127.0.0.1", "wsgi.url_scheme": "https"})
    cliente.raise_request_exception = False
    return cliente


def veredicto(codigo, que, esperado, observado, ok):
    RESULTADOS.append((codigo, que, esperado, observado, ok))
    marca = "OK   " if ok else "FALLA"
    print(f"[{marca}] {codigo} · {que}")
    print(f"         esperado: {esperado}")
    print(f"         observado: {observado}")


def sesion_de(usuario):
    cliente = navegador()
    cliente.force_login(usuario)
    return cliente


# ---------------------------------------------------------------------------
def d3_02():
    from django.urls import reverse

    from apps.accounts.models import Usuario
    from apps.core.models import RegistroAuditoria

    victima = Usuario.objects.filter(rol=Usuario.CLIENTE).order_by("pk").last()
    atacante = navegador()
    url = reverse("accounts:login")
    bloqueado_en = None
    for intento in range(1, 21):
        respuesta = atacante.post(
            url, {"username": victima.email, "password": f"mala-{intento}"}, secure=True
        )
        if bloqueado_en is None and "bloquead" in respuesta.content.decode().lower():
            bloqueado_en = intento
    correcta = atacante.post(url, {"username": victima.email, "password": CONTRASENA}, secure=True)
    entro = "_auth_user_id" in atacante.session
    auditado = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BLOQUEO_POR_INTENTOS, actor_email=victima.email
    ).exists()
    veredicto(
        "D3-02",
        "Fuerza bruta contra una cuenta",
        "bloqueo al 5.º intento, auditado, la contraseña correcta no entra",
        f"bloqueado desde el intento {bloqueado_en}, auditado={auditado}, "
        f"entró con la correcta={entro} (respuesta {correcta.status_code})",
        bloqueado_en is not None and bloqueado_en <= 6 and auditado and not entro,
    )


def d3_03():
    from django.urls import reverse

    from apps.accounts.models import Usuario

    existe = Usuario.objects.filter(rol=Usuario.CLIENTE).order_by("pk").first().email
    url = reverse("accounts:password_reset")

    def pedir(correo):
        respuesta = navegador().post(url, {"email": correo}, secure=True, follow=True)
        cuerpo = respuesta.content.decode()
        cuerpo = re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "", cuerpo)
        return respuesta.status_code, respuesta.redirect_chain, cuerpo

    a = pedir(existe)
    b = pedir("nadie.existe.aca@longbox.demo")
    iguales = a == b
    veredicto(
        "D3-03",
        "Enumeración de cuentas por la recuperación de contraseña",
        "las dos respuestas iguales (estado, redirección y cuerpo)",
        f"estado {a[0]} / {b[0]}, redirecciones iguales={a[1] == b[1]}, "
        f"cuerpos iguales={a[2] == b[2]} ({len(a[2])} y {len(b[2])} bytes)",
        iguales,
    )


def d3_04():
    from django.urls import reverse

    from apps.accounts.models import Usuario
    from apps.catalog.models import Editorial

    admin = sesion_de(Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).first())
    publico = navegador()
    cadenas = [
        "' OR '1'='1",
        "%'; DROP TABLE catalog_producto; --",
        "\\' UNION SELECT password FROM accounts_usuario --",
    ]
    codigos = []
    for cadena in cadenas:
        codigos.append(
            admin.get(reverse("catalog:producto_lista"), {"q": cadena}, secure=True).status_code
        )
        codigos.append(
            publico.get(reverse("core:tienda_catalogo"), {"q": cadena}, secure=True).status_code
        )
    script = "<script>alert('longbox')</script>"
    admin.post(reverse("catalog:editorial_crear"), {"nombre": f"Editorial {script}"}, secure=True)
    creada = Editorial.objects.filter(nombre__contains="<script>").exists()
    listado = admin.get(reverse("catalog:editorial_lista"), secure=True).content.decode()
    crudo = script in listado
    escapado = "&lt;script&gt;" in listado
    veredicto(
        "D3-04",
        "Inyección SQL en búsquedas y <script> en un nombre",
        "búsquedas 200; el nombre se guarda como texto y se muestra escapado",
        f"códigos de búsqueda {sorted(set(codigos))}; guardada={creada}; "
        f"en el listado crudo={crudo}, escapado={escapado}",
        set(codigos) == {200} and not crudo and escapado,
    )


def d3_05():
    from django.urls import reverse

    from apps.accounts.models import Usuario
    from apps.catalog.models import Editorial

    antes = Editorial.objects.count()
    forjado = navegador(enforce_csrf_checks=True)
    forjado.force_login(Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).first())
    respuesta = forjado.post(reverse("catalog:editorial_crear"), {"nombre": "Forjada"}, secure=True)
    despues = Editorial.objects.count()
    veredicto(
        "D3-05",
        "POST sin token CSRF a una operación de escritura",
        "403 y ninguna editorial nueva",
        f"respuesta {respuesta.status_code}, editoriales {antes} → {despues}",
        respuesta.status_code == 403 and antes == despues,
    )


def d3_06():
    from django.urls import reverse

    from apps.accounts.models import Usuario
    from apps.tienda.models import LineaCarrito

    ajena = LineaCarrito.objects.select_related("carrito__usuario").first()
    otro = Usuario.objects.filter(rol=Usuario.CLIENTE).exclude(pk=ajena.carrito.usuario_id).first()
    intruso = sesion_de(otro)
    cantidad = intruso.post(
        reverse("tienda:cantidad", args=[ajena.pk]), {"cantidad": 9}, secure=True
    )
    quitar = intruso.post(reverse("tienda:quitar", args=[ajena.pk]), secure=True)
    ajena_despues = LineaCarrito.objects.filter(pk=ajena.pk).first()
    intacta = ajena_despues is not None and ajena_despues.cantidad == ajena.cantidad
    veredicto(
        "D3-06",
        "Modificar y quitar la línea del carrito de otro cliente",
        "404 en los dos pedidos y la línea ajena intacta",
        f"cantidad → {cantidad.status_code}, quitar → {quitar.status_code}, "
        f"línea {'intacta' if intacta else 'ALTERADA'}",
        cantidad.status_code == 404
        and quitar.status_code == 404
        and ajena_despues is not None
        and ajena_despues.cantidad == ajena.cantidad,
    )


def d3_07():
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.urls import reverse
    from PIL import Image

    from apps.accounts.models import Usuario
    from apps.core.models import Banner

    admin = sesion_de(Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).first())
    url = reverse("core:banner_crear")

    def subir(nombre, contenido, tipo="image/jpeg"):
        antes = Banner.objects.count()
        respuesta = admin.post(
            url, {"imagen": SimpleUploadedFile(nombre, contenido, tipo)}, secure=True
        )
        mensaje = re.findall(r'class="error-de-campo">Error: ([^<]+)<', respuesta.content.decode())
        return Banner.objects.count() - antes, mensaje

    def jpg(lado):
        salida = io.BytesIO()
        Image.new("RGB", (lado, lado), (255, 106, 19)).save(salida, "JPEG", quality=95)
        return salida.getvalue()

    exe = b"MZ\x90\x00" + b"\x00" * 2048
    grande = b"\xff\xd8\xff\xe0" + b"0" * (21 * 1024 * 1024)
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    casos = {
        "ejecutable como .jpg": subir("foto.jpg", exe),
        "20 MB": subir("grande.jpg", grande),
        "SVG con script": subir("logo.svg", svg, "image/svg+xml"),
    }
    rechazados = all(creados == 0 and mensaje for creados, mensaje in casos.values())
    creados, _ = subir("../../../../config/settings/evil.jpg", jpg(400))
    banner = Banner.objects.order_by("-pk").first()
    nombre = banner.imagen.name if creados and banner else ""
    seguro = (
        creados == 1 and nombre.endswith(".webp") and ".." not in nombre and "evil" not in nombre
    )
    detalle = "; ".join(f"{caso}: {m[0] if m else 'SIN MENSAJE'}" for caso, (_, m) in casos.items())
    veredicto(
        "D3-07",
        "Archivos hostiles en la carga de banners",
        "los tres hostiles rechazados con mensaje; el válido guardado en WebP con nombre propio",
        f"{detalle}; válido con nombre '../': guardado como «{nombre}»",
        rechazados and seguro,
    )


def d3_08():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT email, password FROM accounts_usuario WHERE email IN (%s, %s)",
            ["cliente001@longbox.demo", "cliente002@longbox.demo"],
        )
        filas = cursor.fetchall()
    hashes = [clave for _, clave in filas]
    distintos = len(set(hashes)) == 2
    sin_texto = all(CONTRASENA not in clave for clave in hashes)
    algoritmo = hashes[0].split("$", 1)[0] if hashes else "?"
    veredicto(
        "D3-08",
        "Dos cuentas con la misma contraseña, leídas directo de la base",
        "hashes distintos (cada uno con su sal) y sin la contraseña en claro",
        f"{len(filas)} cuentas, algoritmo {algoritmo}, distintos={distintos}, "
        f"sin texto plano={sin_texto}",
        len(filas) == 2 and distintos and sin_texto,
    )


def d3_09():
    from django.urls import reverse

    from apps.accounts.models import Usuario

    cajero = Usuario.objects.filter(rol=Usuario.CAJERO, estado=Usuario.ACTIVO).order_by("pk").last()
    admin = sesion_de(Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).first())
    sesion_cajero = sesion_de(cajero)
    antes = sesion_cajero.get(reverse("core:mostrador"), secure=True).status_code
    admin.post(
        reverse("accounts:usuario_edicion", args=[cajero.pk]),
        {
            "nombre_completo": cajero.get_full_name() or "Cajero",
            "email": cajero.email,
            "rol": Usuario.ADMINISTRADOR,
        },
        secure=True,
    )
    despues = sesion_cajero.get(reverse("core:mostrador"), secure=True)
    cortada = despues.status_code == 302 and reverse("accounts:login") in despues.url
    veredicto(
        "D3-09",
        "La sesión de una cuenta cuyo rol cambia",
        "la próxima petición de esa sesión va al inicio de sesión",
        f"antes {antes}; después {despues.status_code} → {getattr(despues, 'url', '')}",
        antes == 200 and cortada,
    )


ESCENARIOS = {
    "D3-02": d3_02,
    "D3-03": d3_03,
    "D3-04": d3_04,
    "D3-05": d3_05,
    "D3-06": d3_06,
    "D3-07": d3_07,
    "D3-08": d3_08,
    "D3-09": d3_09,
}


def main():
    preparar()
    elegidos = sys.argv[1:] or list(ESCENARIOS)
    inicio = time.perf_counter()
    for codigo in elegidos:
        try:
            ESCENARIOS[codigo]()
        except Exception as error:  # noqa: BLE001 - un escenario roto no tapa a los demás
            veredicto(
                codigo,
                "error al ejecutar el escenario",
                "—",
                f"{type(error).__name__}: {error}",
                False,
            )
    lineas = [
        "| Código | Ataque | Esperado | Observado | Veredicto |",
        "| --- | --- | --- | --- | --- |",
    ]
    for codigo, que, esperado, observado, ok in RESULTADOS:
        lineas.append(
            f"| {codigo} | {que} | {esperado} | {observado} | {'OK' if ok else 'FALLA'} |"
        )
    (SALIDA / "ataques.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    fallas = [r for r in RESULTADOS if not r[4]]
    segundos = time.perf_counter() - inicio
    print(f"\n{len(RESULTADOS) - len(fallas)} de {len(RESULTADOS)} OK en {segundos:.0f} s")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
