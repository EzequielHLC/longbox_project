"""`manage.py` con el entorno de la demostración.

    python scripts/demo/manejar.py migrate
    python scripts/demo/manejar.py collectstatic --noinput
    python scripts/demo/manejar.py servir
    python scripts/demo/manejar.py check --deploy --fail-level WARNING

Corre con los ajustes de producción (`ajustes_demo.py`, `DEBUG=False`) sobre `longbox_demo`.
"""

import subprocess  # nosec B404 - manage.py con argumentos fijos
import sys

from entorno import RAIZ, entorno_para_subproceso, preparar

if __name__ == "__main__":
    # Verifica la base antes de lanzar nada.
    preparar()
    comando = [sys.executable, str(RAIZ / "manage.py"), *sys.argv[1:]]
    codigo = subprocess.call(  # nosec B603 - manage.py, sin shell
        comando, env=entorno_para_subproceso(), cwd=RAIZ
    )
    sys.exit(codigo)
