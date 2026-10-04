"""D6-01 y D6-02 · El modelo de lenguaje caído o respondiendo basura.

    python scripts/demo/modelo_caido.py

Sobre `longbox_demo`, con tres situaciones del modelo:

1. **Caído** (nada escucha en la URL configurada). El diagnóstico de
   `CU-CFG-LLM` tipifica el error; un correo aprobado queda en «Falló el
   procesamiento», con su motivo, y se puede reprocesar.
2. **JSON roto** (`llm_falso.py roto`). Igual: falla con motivo, sin borradores.
3. **Datos inventados con forma válida** (`llm_falso.py inventado`). Cada dato
   verificable se descarta con su reparo; el título inventado queda como
   borrador pendiente de revisión. **No se crea ningún producto**: el modelo
   propone, nunca aplica (regla 4).

Escribe en la base: después de este acto se corre `restaurar.py`. Al terminar
deja la URL del modelo como estaba.
"""

import subprocess  # nosec B404 - el modelo falso, con argumentos fijos
import sys
import time
from pathlib import Path

from entorno import entorno_para_subproceso, preparar

AQUI = Path(__file__).resolve().parent


def aprobar_uno(actor):
    from apps.suppliers import services
    from apps.suppliers.models import CorreoProveedor

    correo = CorreoProveedor.objects.filter(estado=CorreoProveedor.PENDIENTE).order_by("pk").first()
    try:
        services.aprobar_correo(correo.pk, actor=actor)
    except Exception as error:  # noqa: BLE001 - lo que se muestra es que no se rompe
        return correo, f"LEVANTÓ {type(error).__name__}: {error}"
    correo.refresh_from_db()
    return correo, None


def main():
    preparar()
    from apps.accounts.models import Usuario
    from apps.catalog.models import BorradorProducto, Producto
    from apps.core import llm
    from apps.core.models import ConfiguracionSistema
    from apps.suppliers.models import CorreoProveedor

    actor = Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).first()
    configuracion = ConfiguracionSistema.obtener()
    url_original = configuracion.llm_url
    productos_antes = Producto.objects.count()
    ok = True

    try:
        print("1. Modelo caído")
        configuracion.llm_url = "http://127.0.0.1:1299/v1/chat/completions"
        configuracion.save()
        print(f"   diagnóstico: {llm.estado()}")
        correo, error = aprobar_uno(actor)
        extra = f" · {error}" if error else ""
        print(f"   correo {correo.pk}: {correo.estado} · {correo.motivo[:90]}{extra}")
        ok &= not error and correo.estado == CorreoProveedor.FALLIDO and bool(correo.motivo)

        for modo in ("roto", "inventado"):
            print(f"{2 if modo == 'roto' else 3}. Modelo que responde «{modo}»")
            servidor = subprocess.Popen(  # nosec B603
                [sys.executable, str(AQUI / "llm_falso.py"), modo],
                env=entorno_para_subproceso(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                time.sleep(1.5)
                configuracion.llm_url = "http://127.0.0.1:1235/v1/chat/completions"
                configuracion.save()
                correo, error = aprobar_uno(actor)
                borradores = list(BorradorProducto.objects.filter(correo=correo))
                print(f"   correo {correo.pk}: {correo.estado}{' · ' + error if error else ''}")
                if modo == "roto":
                    print(f"   motivo: {correo.motivo[:120]}")
                    ok &= not error and correo.estado == CorreoProveedor.FALLIDO and not borradores
                else:
                    for borrador in borradores:
                        print(f"   borrador «{borrador.titulo}» · {borrador.get_estado_display()}")
                        for reparo in borrador.reparos or []:
                            print(f"     reparo: {reparo}")
                    ok &= (
                        not error
                        and bool(borradores)
                        and all(
                            not b.isbn and b.estado != BorradorProducto.CONFIRMADO
                            for b in borradores
                        )
                    )
            finally:
                servidor.terminate()
    finally:
        configuracion.llm_url = url_original
        configuracion.save()

    productos_despues = Producto.objects.count()
    print(f"Productos en el catálogo: {productos_antes} → {productos_despues}")
    ok &= productos_antes == productos_despues
    print("Resultado:", "OK" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
