"""D1-02 · Sabotaje controlado: rompe algo a propósito y muestra que la suite lo detecta.

    python scripts/demo/sabotaje.py acceso
    python scripts/demo/sabotaje.py dinero
    python scripts/demo/sabotaje.py invariante
    python scripts/demo/sabotaje.py todos

Cada sabotaje es un defecto conocido en una zona de foco reforzado de CLAUDE.md:

- **acceso**: el log de auditoría deja de exigir el rol de Administrador.
- **dinero**: el coeficiente de importación (CRE) se redondea a dos decimales
  antes de aplicarlo, en vez de conservar los suyos.
- **invariante**: el resguardo del último Administrador (I-12) deja de proteger.

**El directorio de trabajo real nunca recibe el defecto.** El sabotaje se aplica
en un `git worktree` temporal, al que se le copian encima los cambios todavía
no confirmados, para que refleje el estado actual del repositorio. Se corren
sólo las pruebas de esa zona, sobre su propia base de pruebas, y la copia se
descarta. Al terminar se verifica que el directorio real no cambió.

Éxito = las pruebas pasan en rojo. Si un sabotaje no hace fallar ninguna
prueba, encontramos un hueco en la suite.
"""

import argparse
import hashlib
import os
import shutil
import subprocess  # nosec B404 - git y pytest con argumentos fijos
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

SABOTAJES = {
    "acceso": {
        "que": "El log de auditoría deja de exigir el rol de Administrador (RNF-03).",
        "archivo": "apps/core/views_auditoria.py",
        "antes": "    roles_permitidos = (Usuario.ADMINISTRADOR,)\n    metodos_de_lectura",
        "despues": "    roles_permitidos = ()\n    metodos_de_lectura",
        "pruebas": [
            "apps/core/tests/test_contratos_16_auditoria.py",
            "apps/core/tests/test_auditoria.py",
        ],
    },
    "dinero": {
        "que": "El CRE se redondea a dos decimales antes de aplicarlo (RF-10).",
        "archivo": "apps/catalog/precios.py",
        "antes": "    return cre.quantize(PRECISION_CRE, rounding=ROUND_HALF_UP)",
        "despues": '    return cre.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)',
        "pruebas": ["apps/catalog/tests/test_precios.py", "apps/catalog/tests/test_inventario.py"],
    },
    "invariante": {
        "que": "El resguardo del último Administrador deja de proteger (I-12).",
        "archivo": "apps/accounts/services.py",
        "antes": "    return activos == [usuario.pk]\n",
        "despues": "    return False\n",
        "pruebas": [
            "apps/accounts/tests/test_contratos_13_gestion_de_usuarios.py",
            "apps/accounts/tests/test_baja_usuario.py",
            "apps/accounts/tests/test_modificacion_usuario.py",
        ],
    },
}


def git(*argumentos, cwd=RAIZ):
    return subprocess.run(  # nosec B603 B607
        ["git", *argumentos],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def huella_del_trabajo():
    """Lo que hay sin confirmar en el directorio real, resumido en un hash."""
    estado = git("status", "--porcelain") + git("diff")
    return hashlib.sha256(estado.encode()).hexdigest()[:12]


def preparar_copia(destino):
    git("worktree", "add", "--detach", str(destino), "HEAD")
    # Los cambios sin confirmar y los archivos nuevos, para que la copia sea el estado actual.
    for nombre in git("ls-files", "-m", "-o", "--exclude-standard").splitlines():
        origen = RAIZ / nombre
        if origen.is_file():
            (destino / nombre).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, destino / nombre)
    for nombre in git("ls-files", "-d").splitlines():
        (destino / nombre).unlink(missing_ok=True)
    # Los ajustes leen el .env de la raíz del proyecto; la copia también.
    shutil.copy2(RAIZ / ".env", destino / ".env")


def aplicar(destino, sabotaje):
    archivo = destino / sabotaje["archivo"]
    texto = archivo.read_text(encoding="utf-8")
    if sabotaje["antes"] not in texto:
        raise SystemExit(f"El código cambió: no encuentro el blanco en {sabotaje['archivo']}.")
    archivo.write_text(texto.replace(sabotaje["antes"], sabotaje["despues"], 1), encoding="utf-8")


def correr_pruebas(destino, pruebas):
    entorno = dict(os.environ)
    # Su propia base de pruebas: no choca con otra suite que esté corriendo.
    entorno["DB_NAME"] = "longbox_sabotaje"
    entorno["PYTHONIOENCODING"] = "utf-8"
    resultado = subprocess.run(  # nosec B603
        [
            sys.executable,
            "-m",
            "pytest",
            *pruebas,
            "-q",
            "--no-cov",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
            "--create-db",
            "-rf",
        ],
        cwd=destino,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return resultado.stdout + resultado.stderr


def sabotear(nombre):
    sabotaje = SABOTAJES[nombre]
    print(f"\n=== Sabotaje «{nombre}»: {sabotaje['que']}")
    print(f"    Archivo: {sabotaje['archivo']}")
    print(f"    - {sabotaje['antes'].strip().splitlines()[0]}")
    print(f"    + {sabotaje['despues'].strip().splitlines()[0]}")
    huella = huella_del_trabajo()
    destino = Path(tempfile.mkdtemp(prefix="longbox-sabotaje-")) / "copia"
    inicio = time.perf_counter()
    try:
        preparar_copia(destino)
        aplicar(destino, sabotaje)
        salida = correr_pruebas(destino, sabotaje["pruebas"])
    finally:
        subprocess.run(  # nosec B603 B607
            ["git", "worktree", "remove", "--force", str(destino)], cwd=RAIZ, capture_output=True
        )
        shutil.rmtree(destino.parent, ignore_errors=True)
    fallidas = [linea for linea in salida.splitlines() if linea.startswith("FAILED")]
    resumen = next((linea for linea in reversed(salida.splitlines()) if " in " in linea), "")
    print(f"    Resultado: {resumen.strip()} ({time.perf_counter() - inicio:.0f} s)")
    for linea in fallidas[:8]:
        print(f"      {linea.split(' - ')[0]}")
    if len(fallidas) > 8:
        print(f"      … y {len(fallidas) - 8} más")
    intacto = huella_del_trabajo() == huella
    print(f"    Directorio de trabajo real: {'sin cambios' if intacto else 'CAMBIÓ'}")
    if not fallidas:
        print("    ATENCIÓN: ninguna prueba falló. Es un hueco de la suite.")
    return bool(fallidas) and intacto


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("cual", choices=[*SABOTAJES, "todos"])
    opciones = argumentos.parse_args()
    elegidos = list(SABOTAJES) if opciones.cual == "todos" else [opciones.cual]
    resultados = {nombre: sabotear(nombre) for nombre in elegidos}
    print("\nDetectados:", ", ".join(f"{n}={'sí' if ok else 'NO'}" for n, ok in resultados.items()))
    return 0 if all(resultados.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
