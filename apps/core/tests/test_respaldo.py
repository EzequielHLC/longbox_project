"""El comando de respaldo de la base.

`pg_dump` no se llama de verdad acá. No es por velocidad: el ejecutable puede no
estar en la máquina que corre los tests —en el CI la base es un contenedor y el
cliente no viene instalado— y un test que dependa de eso falla por el entorno y
no por el código. Lo que se prueba es la lógica que rodea al volcado, que es
donde están las decisiones:

- que un respaldo ilegible **se descarte** en vez de contarse como bueno,
- que la contraseña no viaje en los argumentos del proceso,
- que la limpieza por antigüedad no toque lo que el comando no generó,
- que un `pg_dump` más viejo que el servidor se detecte antes y no después.

El camino completo contra PostgreSQL real —volcar, restaurar en otra base y
verificar que los datos y las restricciones vuelven— está descrito en el plan de
pruebas como verificación manual, porque necesita permisos de creación de bases
que el usuario de los tests no tiene por qué tener.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core.management.commands import respaldar_base

pytestmark = pytest.mark.django_db


def resultado(codigo=0, salida="; Archive created at 2026-09-02\n", error=""):
    """Lo que devuelve `subprocess.run` para el comando."""
    return subprocess.CompletedProcess(args=[], returncode=codigo, stdout=salida, stderr=error)


def llamada_al_volcado(doble):
    """La invocación de `pg_dump` que escribe el archivo.

    No es la primera de la lista: antes va la que le pregunta la versión, y
    tomar la primera a ciegas prueba el `--version` creyendo que prueba el
    volcado.
    """
    for llamada in doble.call_args_list:
        if any(str(parte).startswith("--file=") for parte in llamada.args[0]):
            return llamada
    raise AssertionError("El comando nunca llamo a pg_dump con --file=")


def con_contrasena(clave):
    """Cambia la contraseña sin tocar el diccionario que comparte la sesión.

    Mutar `settings.DATABASES["default"]` in situ no se deshace al terminar el
    test —la fixture repone el diccionario de afuera, no el de adentro— y la
    conexión queda rota para todo lo que venga después.
    """
    return patch.dict(settings.DATABASES["default"], {"PASSWORD": clave})


@pytest.fixture
def herramientas():
    """Da por encontrados `pg_dump` y `pg_restore`, sin tocar el disco."""
    with patch.object(respaldar_base, "ubicar", side_effect=lambda p: Path(f"/bin/{p}")):
        yield


@pytest.fixture
def volcado_falso(herramientas):
    """`subprocess.run` que escribe un archivo y dice que todo salió bien.

    Escribe de verdad porque el comando mide el tamaño del resultado y la
    limpieza cuenta archivos: un doble que no deje nada en disco probaría otra
    cosa.
    """

    def correr(orden, **kwargs):
        for parte in orden:
            if str(parte).startswith("--file="):
                Path(str(parte)[len("--file=") :]).write_bytes(b"PGDMP falso")
        return resultado()

    with patch.object(respaldar_base.subprocess, "run", side_effect=correr) as doble:
        yield doble


# ---------------------------------------------------------------------------
# El camino feliz
# ---------------------------------------------------------------------------


def test_deja_un_respaldo_con_la_fecha_en_el_nombre(tmp_path, volcado_falso):
    call_command("respaldar_base", destino=str(tmp_path))

    respaldos = list(tmp_path.iterdir())
    assert len(respaldos) == 1
    assert respaldar_base.RECONOCE.match(respaldos[0].name)


def test_crea_la_carpeta_si_no_existe(tmp_path, volcado_falso):
    """Una tarea programada corre sin nadie mirando: si el destino no existe,
    tiene que crearlo y no fallar."""
    destino = tmp_path / "todavia" / "no" / "existe"

    call_command("respaldar_base", destino=str(destino))

    assert destino.is_dir()


def test_el_formato_es_el_propio_de_postgresql(tmp_path, volcado_falso):
    """`custom` viene comprimido y permite restaurar una tabla sola; un `.sql`
    plano no permite ni lo uno ni lo otro."""
    call_command("respaldar_base", destino=str(tmp_path))

    assert "--format=custom" in llamada_al_volcado(volcado_falso).args[0]


def test_no_espera_una_contrasena_por_teclado(tmp_path, volcado_falso):
    """Sin `--no-password`, un respaldo mal configurado no falla: se cuelga
    esperando a alguien que en una tarea programada no está."""
    call_command("respaldar_base", destino=str(tmp_path))

    assert "--no-password" in llamada_al_volcado(volcado_falso).args[0]


# ---------------------------------------------------------------------------
# La contraseña
# ---------------------------------------------------------------------------


def test_la_contrasena_no_va_en_los_argumentos(tmp_path, volcado_falso):
    """Los argumentos de un proceso los lee cualquiera que liste procesos."""
    with con_contrasena("secreto-que-no-debe-verse"):
        call_command("respaldar_base", destino=str(tmp_path))

    orden = llamada_al_volcado(volcado_falso).args[0]
    assert "secreto-que-no-debe-verse" not in " ".join(str(p) for p in orden)


def test_la_contrasena_va_por_el_entorno(tmp_path, volcado_falso):
    with con_contrasena("secreto-que-no-debe-verse"):
        call_command("respaldar_base", destino=str(tmp_path))

    entorno = llamada_al_volcado(volcado_falso).kwargs["env"]
    assert entorno["PGPASSWORD"] == "secreto-que-no-debe-verse"


# ---------------------------------------------------------------------------
# Lo que separa un respaldo de un archivo
# ---------------------------------------------------------------------------


def test_un_respaldo_ilegible_se_descarta(tmp_path, herramientas):
    """`pg_dump` puede terminar en 0 y dejar el archivo truncado. Contarlo como
    bueno es peor que no tenerlo: se descubre el día que hace falta."""

    def correr(orden, **kwargs):
        if "--list" in orden:
            return resultado(codigo=1, salida="", error="no es un archivo valido")
        for parte in orden:
            if str(parte).startswith("--file="):
                Path(str(parte)[len("--file=") :]).write_bytes(b"basura")
        return resultado()

    with patch.object(respaldar_base.subprocess, "run", side_effect=correr):
        with pytest.raises(CommandError, match="no se puede leer"):
            call_command("respaldar_base", destino=str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_si_pg_dump_falla_no_queda_un_archivo_a_medias(tmp_path, herramientas):
    def correr(orden, **kwargs):
        for parte in orden:
            if str(parte).startswith("--file="):
                Path(str(parte)[len("--file=") :]).write_bytes(b"a medias")
        return resultado(codigo=1, error="se acabo el disco")

    with patch.object(respaldar_base.subprocess, "run", side_effect=correr):
        with pytest.raises(CommandError, match="se acabo el disco"):
            call_command("respaldar_base", destino=str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_un_pg_dump_mas_viejo_que_el_servidor_se_rechaza(tmp_path, herramientas):
    """Se niega a volcar y el mensaje aparece justo cuando hace falta el
    respaldo. Mejor enterarse acá, que dice qué actualizar."""
    with patch.object(respaldar_base, "version_mayor", return_value=9):
        with pytest.raises(CommandError, match="mas viejo que el servidor"):
            call_command("respaldar_base", destino=str(tmp_path))


def test_sin_pg_restore_no_se_respalda(tmp_path):
    """Sin con qué verificar, el comando no genera nada: un respaldo sin
    verificar es la mitad del trabajo y toda la falsa tranquilidad."""
    with patch.object(respaldar_base, "ubicar", return_value=None):
        with pytest.raises(CommandError, match="pg_restore"):
            call_command("respaldar_base", destino=str(tmp_path))


# ---------------------------------------------------------------------------
# La limpieza por antigüedad
# ---------------------------------------------------------------------------


def test_conserva_los_mas_nuevos_y_borra_el_resto(tmp_path, volcado_falso):
    for marca in ("20260101-000000", "20260102-000000", "20260103-000000"):
        (tmp_path / f"longbox-{marca}.dump").write_bytes(b"viejo")

    call_command("respaldar_base", destino=str(tmp_path), conservar=2)

    quedan = sorted(a.name for a in tmp_path.iterdir())
    assert len(quedan) == 2
    assert "longbox-20260101-000000.dump" not in quedan


def test_conservar_cero_no_borra_nada(tmp_path, volcado_falso):
    (tmp_path / "longbox-20260101-000000.dump").write_bytes(b"viejo")

    call_command("respaldar_base", destino=str(tmp_path), conservar=0)

    assert len(list(tmp_path.iterdir())) == 2


def test_no_toca_lo_que_no_genero(tmp_path, volcado_falso):
    """Borrar por antigüedad archivos ajenos es la peor forma de fallar que
    tiene un limpiador, y la carpeta puede tener cualquier cosa."""
    ajeno = tmp_path / "notas-importantes.txt"
    ajeno.write_text("no me borres")
    (tmp_path / "longbox-20260101-000000.dump").write_bytes(b"viejo")

    call_command("respaldar_base", destino=str(tmp_path), conservar=1)

    assert ajeno.exists()


# ---------------------------------------------------------------------------
# La revisión de lo ya guardado
# ---------------------------------------------------------------------------


def test_verificar_solo_no_genera_un_respaldo_nuevo(tmp_path, volcado_falso):
    (tmp_path / "longbox-20260101-000000.dump").write_bytes(b"viejo")

    call_command("respaldar_base", destino=str(tmp_path), verificar_solo=True)

    assert len(list(tmp_path.iterdir())) == 1


def test_verificar_solo_avisa_si_alguno_esta_roto(tmp_path, herramientas):
    (tmp_path / "longbox-20260101-000000.dump").write_bytes(b"roto")

    with patch.object(respaldar_base.subprocess, "run", return_value=resultado(codigo=1)):
        with pytest.raises(CommandError, match="ilegibles"):
            call_command("respaldar_base", destino=str(tmp_path), verificar_solo=True)


def test_verificar_solo_con_la_carpeta_vacia_no_es_un_error(tmp_path, herramientas):
    """Es el estado del primer día, y una tarea programada que devuelve error
    ese día manda a buscar un problema que no existe."""
    call_command("respaldar_base", destino=str(tmp_path), verificar_solo=True)


# ---------------------------------------------------------------------------
# La salida, que va a un archivo de registro sin nadie mirando
# ---------------------------------------------------------------------------


def test_la_salida_es_ascii(tmp_path, volcado_falso, capsys):
    """La consola de Windows corre en cp1252: un acento la hace reventar con el
    trabajo ya hecho y sin decir cuánto se procesó."""
    call_command("respaldar_base", destino=str(tmp_path), conservar=1)

    salida = capsys.readouterr().out
    salida.encode("ascii")
