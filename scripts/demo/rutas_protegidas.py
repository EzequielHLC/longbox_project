"""D3-01 · RNF-03: cada ruta protegida, pedida con el rol equivocado, responde 403.

    python scripts/demo/rutas_protegidas.py

Recorre **todas** las rutas del sistema, no una muestra, con tres visitantes:
sin sesión, Cliente y Cajero. Para cada ruta, el rol que puede entrar lo dice la
propia vista (`roles_permitidos` del `RolRequeridoMixin`); el resto tiene que
recibir 403 (o, sin sesión, la redirección al inicio de sesión).

Además mira el **cuerpo** de cada 403: no puede traer datos del sistema. Se
busca cualquier correo o código de producto que exista en la base.

Corre dentro del proceso, con los ajustes de producción sobre `longbox_demo` y
por HTTPS, sólo con pedidos GET: ninguno de estos pedidos tiene que escribir nada.
La tabla queda en `salida/rutas_protegidas.md` y `.json`.
"""

import json
import re
import sys

from entorno import SALIDA, preparar

CONVERSORES = {
    "int": "1",
    "str": "x",
    "slug": "x",
    "path": "x",
    "uuid": "00000000-0000-0000-0000-000000000000",
}


def rutas():
    """(ruta concreta, nombre, vista) para cada patrón, con los parámetros rellenados."""
    from django.urls import URLPattern, URLResolver, get_resolver

    salida = []

    def recorrer(patrones, prefijo="", espacio=""):
        for patron in patrones:
            texto = str(patron.pattern)
            if isinstance(patron, URLResolver):
                nombre = f"{patron.namespace}:" if patron.namespace else espacio
                recorrer(patron.url_patterns, prefijo + texto, nombre)
            elif isinstance(patron, URLPattern):
                completo = prefijo + texto
                if completo.startswith("^"):
                    continue  # los estáticos y archivos subidos
                concreta = re.sub(
                    r"<(?:(\w+):)?\w+>",
                    lambda m: CONVERSORES.get(m.group(1) or "str", "x"),
                    completo,
                )
                vista = getattr(patron.callback, "view_class", patron.callback)
                salida.append(("/" + concreta, f"{espacio}{patron.name or ''}", vista))

    recorrer(get_resolver().url_patterns)
    return salida


def roles_de(vista):
    return tuple(getattr(vista, "roles_permitidos", ()) or ())


def main():
    preparar()
    from django.test import Client

    from apps.accounts.models import Usuario
    from apps.catalog.models import Producto

    cliente = Usuario.objects.filter(rol=Usuario.CLIENTE, estado=Usuario.ACTIVO).first()
    cajero = Usuario.objects.filter(rol=Usuario.CAJERO, estado=Usuario.ACTIVO).first()
    if not (cliente and cajero):
        raise SystemExit("Hacen falta un Cliente y un Cajero activos: corré poblar.py.")
    sensibles = list(Usuario.objects.values_list("email", flat=True)[:200])
    sensibles += list(Producto.objects.values_list("codigo", flat=True)[:200])

    visitantes = {"sin sesión": Client(), "cliente": Client(), "cajero": Client()}
    visitantes["cliente"].force_login(cliente)
    visitantes["cajero"].force_login(cajero)
    for navegador in visitantes.values():
        navegador.defaults.update({"HTTP_HOST": "127.0.0.1", "wsgi.url_scheme": "https"})
        navegador.raise_request_exception = False

    filas, fallas = [], []
    for ruta, nombre, vista in rutas():
        permitidos = roles_de(vista)
        fila = {"ruta": ruta, "nombre": nombre, "roles": list(permitidos), "codigos": {}}
        for quien, navegador in visitantes.items():
            respuesta = navegador.get(ruta, secure=True)
            codigo = respuesta.status_code
            fila["codigos"][quien] = codigo
            if not permitidos:
                continue
            if quien == "sin sesión":
                esperado_ok = codigo in (302, 403)
            else:
                esperado_ok = quien in permitidos or codigo == 403
            cuerpo = respuesta.content.decode("utf-8", "replace") if codigo == 403 else ""
            filtra = [dato for dato in sensibles if dato and dato in cuerpo]
            if not esperado_ok or filtra or codigo >= 500:
                fallas.append(
                    {"ruta": ruta, "quien": quien, "codigo": codigo, "filtra": filtra[:3]}
                )
        filas.append(fila)

    protegidas = [f for f in filas if f["roles"]]
    lineas = [
        "| Ruta | Nombre | Roles | Sin sesión | Cliente | Cajero |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for fila in protegidas:
        c = fila["codigos"]
        lineas.append(
            f"| `{fila['ruta']}` | `{fila['nombre']}` | {', '.join(fila['roles'])} | "
            f"{c['sin sesión']} | {c['cliente']} | {c['cajero']} |"
        )
    (SALIDA / "rutas_protegidas.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    (SALIDA / "rutas_protegidas.json").write_text(
        json.dumps({"filas": filas, "fallas": fallas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Rutas recorridas: {len(filas)} · protegidas por rol: {len(protegidas)}")
    print(f"Pedidos: {len(filas) * len(visitantes)} · fallas: {len(fallas)}")
    for falla in fallas:
        print(f"  FALLA {falla['quien']:>10} {falla['codigo']} {falla['ruta']} {falla['filtra']}")
    print(f"Tabla completa: {SALIDA / 'rutas_protegidas.md'}")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
