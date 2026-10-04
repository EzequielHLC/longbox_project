"""D1-03 · Pruebas de mutación con mutmut, dentro de un contenedor Linux.

    python scripts/demo/mutacion.py precios     # apps/catalog/precios.py
    python scripts/demo/mutacion.py cuentas     # apps/accounts/services.py

mutmut no corre en Windows (plan 00, decisión 9). Se arma una copia del
repositorio con los cambios todavía no confirmados (como en `sabotaje.py`), se
monta en un contenedor `python:3.14-slim` y se corre mutmut ahí. Las pruebas usan
el PostgreSQL del contenedor de la demostración (`host.docker.internal:5433`),
sobre su propia base de pruebas.

Un mutante es una versión del módulo con un cambio chico (un `<` por un `<=`, un
`+` por un `-`). Si alguna prueba falla, el mutante quedó **muerto**: la suite lo
detectó. Si todas pasan, **sobrevivió**, y hay que mirar si es un hueco de las
pruebas o un mutante equivalente (que no cambia el comportamiento).

Tarda: se muestra el resultado guardado en `salida/mutacion_<módulo>.txt`.
"""

import io
import shutil
import subprocess  # nosec B404 - git y docker con argumentos fijos
import sys
import tarfile
import tempfile
import time
from pathlib import Path

from entorno import RAIZ, SALIDA
from sabotaje import preparar_copia

SALTO = chr(10)

OBJETIVOS = {
    "precios": {
        "modulo": "apps/catalog/precios.py",
        "pruebas": [
            "apps/catalog/tests/test_precios.py",
            "apps/catalog/tests/test_alta_lote_importado.py",
        ],
    },
    "cuentas": {
        "modulo": "apps/accounts/services.py",
        "pruebas": [
            "apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py",
            "apps/accounts/tests/test_bloqueo_intentos.py",
            "apps/accounts/tests/test_contratos_12_autenticacion.py",
        ],
    },
}

GUION = """
set -e
pip install --quiet --root-user-action=ignore -r requirements.txt mutmut==3.8.0 >/dev/null
cat > setup.cfg <<'CFG'
[mutmut]
paths_to_mutate={modulo}
pytest_add_cli_args_test_selection=
{pruebas}
pytest_add_cli_args=
    --no-cov
    -p
    no:cacheprovider
also_copy=
    apps/
    config/
    templates/
    static/
    manage.py
    pytest.ini
    conftest.py
CFG
mutmut run || true
mutmut results --all true 2>/dev/null | head -400 || true
echo "=== RESUMEN ==="
mutmut results 2>/dev/null | tail -60 || true
"""


def _sin_git(miembro):
    """Ni la historia de git ni el `.env`: el contenedor no necesita las credenciales."""
    nombre = miembro.name
    if "/.git" in nombre or nombre.endswith(".git") or nombre.endswith(".env"):
        return None
    return miembro


def main():
    cual = sys.argv[1] if len(sys.argv) > 1 else "precios"
    objetivo = OBJETIVOS[cual]
    copia = Path(tempfile.mkdtemp(prefix="longbox-mutacion-")) / "copia"
    inicio = time.perf_counter()
    try:
        preparar_copia(copia)
        guion = GUION.format(
            modulo=objetivo["modulo"],
            pruebas=SALTO.join(f"    {prueba}" for prueba in objetivo["pruebas"]),
        )
        # La copia viaja al contenedor como un tar por la entrada estándar: Docker
        # Desktop no comparte las carpetas del usuario, y así no hace falta tocar
        # su configuración.
        paquete = io.BytesIO()
        with tarfile.open(fileobj=paquete, mode="w") as tar:
            tar.add(copia, arcname=".", filter=_sin_git)
        resultado = subprocess.run(  # nosec B603 B607
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "-e",
                "DB_NAME=longbox_demo",
                "-e",
                "SECRET_KEY=mutacion-sin-secreto",  # nosec B105 - clave descartable
                "-e",
                "DB_HOST=host.docker.internal",
                "-e",
                "DB_PORT=5433",
                "-e",
                "DB_USER=longbox_demo",
                "-e",
                "DB_PASSWORD=demo-longbox",  # nosec B105 - contenedor descartable
                "python:3.14-slim",
                "bash",
                "-c",
                "mkdir -p /app && cd /app && tar -xf - && " + guion,
            ],
            input=paquete.getvalue(),
            capture_output=True,
        )
        salida = (resultado.stdout + resultado.stderr).decode("utf-8", "replace")
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(copia)], cwd=RAIZ, capture_output=True
        )  # nosec
        shutil.rmtree(copia.parent, ignore_errors=True)
    destino = SALIDA / f"mutacion_{cual}.txt"
    destino.write_text(salida, encoding="utf-8")
    print(salida[-3000:])
    print(f"\n({time.perf_counter() - inicio:.0f} s) Salida completa en {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
