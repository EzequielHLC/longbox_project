"""La pantalla de diagnóstico del modelo de lenguaje.

No corresponde a ningún caso de uso: es una herramienta de operación. Existe
porque el pipeline depende de un servicio que corre **afuera de Django** y que se
apaga sin avisar — sin ella, la única forma de enterarse es que un correo quede
fallido con un mensaje genérico.

Como todo lo demás, no llama al modelo de verdad: se parchea
`integraciones.pedir`, la única puerta HTTP del proyecto.
"""

import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.core import integraciones, llm
from apps.core.models import ConfiguracionSistema
from apps.suppliers import extraccion, muestras

pytestmark = pytest.mark.django_db

URL = reverse("suppliers:diagnostico_llm")

CATALOGO = {"data": [{"id": "qwen/qwen3.5-9b"}, {"id": "text-embedding-nomic"}]}

# La muestra de la pantalla se genera distinta en cada carga; para enviar algo
# desde un test alcanza con una fija y conocida.
MUESTRA = muestras.armar(semilla=1)
CONTENIDO = MUESTRA.contenido


def producto(**cambios):
    base = {
        "isbn": "9789878271583",
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "precio": "24900",
        "imagen": "tapa001@ivrea.test",
        "confianza": {},
    }
    base.update(cambios)
    return base


def extraccion_valida(productos=None, periodo=""):
    contenido = {
        "intencion": extraccion.NOVEDADES,
        "periodo": periodo,
        "productos": productos if productos is not None else [producto()],
    }
    return {"choices": [{"message": {"content": json.dumps(contenido)}}]}


def _como_respuesta(valor):
    """Envuelve lo que el servidor devolvería en el tipo que usa la puerta HTTP.

    Desde que `integraciones.pedir` distingue los modos de falla, devuelve una
    `Respuesta` y no un diccionario pelado. Los tests siguen escribiendo el JSON
    del servidor, que es lo legible, y esto lo lleva al contrato real — un test
    que parchea con la forma vieja probaría un camino que ya no existe.

    `None` se traduce a un fallo de conexión, que es lo que significaba antes.
    """
    if valor is None:
        return integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
    if isinstance(valor, integraciones.Respuesta):
        return valor
    return integraciones.Respuesta(datos=valor)


def contestando(*valores):
    """Parchea la puerta HTTP. Con varios valores, uno por llamada sucesiva.

    La pantalla hace **dos** pedidos distintos en un POST, en este orden:
    primero el catálogo de modelos para el indicador de estado, y solo si el
    servicio está en línea, la extracción.
    """
    envueltos = [_como_respuesta(valor) for valor in valores]
    if len(envueltos) == 1:
        return patch("apps.core.integraciones.pedir", return_value=envueltos[0])
    return patch("apps.core.integraciones.pedir", side_effect=envueltos)


# ---------------------------------------------------------------------------
# El estado del servicio
# ---------------------------------------------------------------------------


def test_muestra_el_servicio_en_linea_con_sus_modelos(client_admin):
    with contestando(CATALOGO):
        respuesta = client_admin.get(URL)

    estado = respuesta.context["estado"]
    assert estado.disponible
    assert "qwen/qwen3.5-9b" in estado.modelos
    assert "En línea" in respuesta.content.decode()


def test_muestra_el_servicio_caido_cuando_no_responde(client_admin):
    """`pedir` devuelve `None` sin conexión. La pantalla tiene que decirlo, no
    quedarse en blanco: es la pregunta que se viene a responder."""
    with contestando(None):
        respuesta = client_admin.get(URL)

    contenido = respuesta.content.decode()
    assert respuesta.context["estado"].disponible is False
    assert "Sin respuesta" in contenido
    # El mensaje dejó de ser solo de LM Studio: con un proveedor remoto la
    # causa es otra, y el texto ahora nombra las dos.
    assert "verifique que el servidor" in contenido


def test_el_estado_se_consulta_con_un_timeout_corto():
    """No con el del modelo. Generar puede tardar minutos y está bien, pero
    preguntar si está vivo tiene que contestar enseguida: con el timeout largo,
    la pantalla contra un servicio caído quedaría cargando cinco minutos."""
    with contestando(CATALOGO) as pedir:
        llm.estado()

    assert pedir.call_args.kwargs["timeout"] == llm.TIMEOUT_ESTADO
    assert llm.TIMEOUT_ESTADO <= 10


def test_el_catalogo_de_modelos_se_deduce_de_la_direccion_del_chat(settings):
    """Se deduce en vez de pedir otra variable de entorno: son del mismo
    servidor, y configurar las dos es una oportunidad más de que queden
    apuntando a lugares distintos."""
    settings.LLM_URL = "http://otra-maquina:8080/v1/chat/completions"

    with contestando(CATALOGO) as pedir:
        estado = llm.estado()

    assert pedir.call_args.args[0] == "http://otra-maquina:8080/v1/models"
    assert estado.url == "http://otra-maquina:8080/v1/models"


def test_una_direccion_que_no_parece_esa_api_lo_dice(settings):
    settings.LLM_URL = "http://cualquier/cosa"

    estado = llm.estado()

    assert estado.disponible is False
    assert "no parece una API compatible" in estado.detalle


def test_un_servicio_sin_modelos_cargados_se_distingue_de_uno_caido(client_admin):
    """Responde, así que no está caído — pero no va a poder generar nada."""
    with contestando({"data": []}):
        estado = client_admin.get(URL).context["estado"]

    assert estado.disponible is True
    assert "no declara ningún modelo" in estado.detalle


# ---------------------------------------------------------------------------
# La configuración
# ---------------------------------------------------------------------------


def test_muestra_con_que_esta_configurado(client_admin, settings):
    settings.LLM_MODELO = ""

    with contestando(CATALOGO):
        contenido = client_admin.get(URL).content.decode()

    assert settings.LLM_URL in contenido
    # Con el modelo sin declarar, la pantalla explica qué significa el vacío en
    # vez de mostrar un hueco.
    assert "el que esté cargado en el servidor" in contenido


# ---------------------------------------------------------------------------
# El banco de pruebas
# ---------------------------------------------------------------------------


def test_la_muestra_viene_cargada_y_es_editable(client_admin):
    """El valor de la pantalla no es correr una prueba fija sino poder pegar el
    contenido de un correo que salió mal y ver qué entiende."""
    with contestando(CATALOGO):
        respuesta = client_admin.get(URL)

    cargada = respuesta.context["form"].fields["contenido"].initial
    assert "| ISBN | Tapa |" in cargada
    assert cargada in respuesta.content.decode()


def test_cada_carga_trae_una_muestra_distinta(client_admin):
    """Mostrar siempre los mismos tres tomos deja la duda de si el modelo los
    está reconociendo en vez de leerlos. Con datos nuevos cada vez, lo que se ve
    es que lee."""
    with contestando(CATALOGO):
        primera = client_admin.get(URL).context["form"].fields["contenido"].initial
        segunda = client_admin.get(URL).context["form"].fields["contenido"].initial

    assert primera != segunda


def test_la_muestra_trae_un_isbn_corrupto_a_proposito():
    """Es la mitad interesante de la demostración: se ve que el sistema lo
    detecta, no solo que el modelo copia bien."""
    from apps.catalog import isbn as isbn_util

    muestra = muestras.armar(semilla=3)

    assert muestra.isbn_roto in muestra.contenido
    assert not isbn_util.es_valido(muestra.isbn_roto)


def test_probar_muestra_lo_que_el_modelo_entendio(client_admin):
    with contestando(CATALOGO, extraccion_valida()):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    resultado = respuesta.context["resultado"]
    assert resultado.intencion == extraccion.NOVEDADES
    assert resultado.productos[0].titulo == "Berserk Deluxe"
    assert "Berserk Deluxe" in respuesta.content.decode()


def test_la_prueba_declara_los_identificadores_de_portada_de_la_muestra(client_admin):
    """Sin declararlos, la comprobación de portada inexistente no tendría contra
    qué comparar y la demostración mostraría una validación que no valida."""
    inventada = extraccion_valida([producto(imagen="inventada@x.test")])

    with contestando(CATALOGO, inventada):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    extraido = respuesta.context["resultado"].productos[0]
    assert extraido.imagen == ""
    assert any("Portada inexistente" in reparo for reparo in extraido.reparos)
    assert "tapa001@editorial.test" in MUESTRA.cids


def test_los_reparos_se_muestran_en_pantalla(client_admin):
    """Es lo que hace visible que el sistema le desconfía al modelo."""
    con_isbn_malo = extraccion_valida([producto(isbn="9789878271584")])

    with contestando(CATALOGO, con_isbn_malo):
        contenido = client_admin.post(URL, {"contenido": CONTENIDO}).content.decode()

    assert "ISBN descartado" in contenido


def test_muestra_el_prompt_que_recibe_el_modelo(client_admin):
    """Con la versión, que es lo que vuelve comparable un resultado con otro. El
    prompt deja de ser algo que hay que creer y pasa a verse."""
    with contestando(CATALOGO, extraccion_valida()):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    contenido = respuesta.content.decode()
    assert respuesta.context["version_prompt"] == extraccion.VERSION_PROMPT
    assert "Sos un asistente que extrae datos" in contenido


def test_muestra_la_respuesta_en_crudo(client_admin):
    """Cuando algo sale raro es lo único que explica por qué."""
    with contestando(CATALOGO, extraccion_valida()):
        contenido = client_admin.post(URL, {"contenido": CONTENIDO}).content.decode()

    assert "Respuesta en crudo del modelo" in contenido


def test_informa_cuanto_tardo(client_admin):
    """Con un modelo local, la diferencia entre dos segundos y dos minutos
    decide si el pipeline necesita una cola de verdad."""
    with contestando(CATALOGO, extraccion_valida()):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert respuesta.context["resultado"].milisegundos >= 0
    assert "ms ·" in respuesta.content.decode()


def test_un_contenido_vacio_no_se_manda_al_modelo(client_admin):
    """Gastar una pasada del modelo en una caja vacía es tirar minutos de GPU."""
    with contestando(CATALOGO) as pedir:
        respuesta = client_admin.post(URL, {"contenido": ""})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["contenido"]
    assert "resultado" not in respuesta.context
    # Solo el pedido del estado, ninguno de extracción.
    assert pedir.call_count == 1


def test_si_el_servicio_esta_caido_ni_se_intenta_la_extraccion(client_admin):
    """Intentarla esperaría el timeout largo entero —minutos— para fallar por lo
    mismo que el chequeo de estado ya sabe. La pantalla que existe para avisar
    que el servicio no está no puede ser la que más tarda cuando no está."""
    with contestando(None) as pedir:
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    contenido = respuesta.content.decode()
    assert respuesta.context["resultado"].error == llm.SIN_SERVICIO
    assert "No se pudo consultar el modelo" in contenido
    # Un solo pedido: el del estado. La extracción no se llegó a intentar.
    assert pedir.call_count == 1


def test_una_respuesta_ilegible_se_distingue_del_servicio_caido(client_admin):
    """Se arreglan en lugares distintos: uno es infraestructura, el otro es el
    prompt o el modelo elegido."""
    ilegible = {"choices": [{"message": {"content": "no es json"}}]}

    with contestando(CATALOGO, ilegible):
        contenido = client_admin.post(URL, {"contenido": CONTENIDO}).content.decode()

    assert "no se pudo interpretar" in contenido


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_la_pantalla_es_solo_del_administrador(client, rol_sin_permiso):
    """Deja ver la configuración del servicio y permite gastarle tiempo de
    cómputo: no es información ni una acción para cualquier rol."""
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL).status_code == 403
    assert client.post(URL, {"contenido": CONTENIDO}).status_code == 403


def test_el_menu_la_enlaza_dentro_de_proveedores(client_admin):
    with contestando(CATALOGO):
        contenido = client_admin.get(URL).content.decode()

    assert URL in contenido
    assert "Diagnóstico del modelo" in contenido


# ---------------------------------------------------------------------------
# El período
#
# Es la parte más nueva y más frágil del prompt, y la que decide si los
# borradores nacen en Pre-venta o Activos. Que no se viera en esta pantalla era
# el defecto más grave que tenía: el operador no tenía forma de saber si el
# modelo lo encontró.
# ---------------------------------------------------------------------------


def test_la_pantalla_muestra_el_periodo_que_copio_el_modelo(client_admin):
    with contestando(CATALOGO, extraccion_valida(periodo="Novedades de marzo 2026")):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    contenido = respuesta.content.decode()
    assert "Período que copió el modelo" in contenido
    assert "Novedades de marzo 2026" in contenido


def test_la_pantalla_muestra_la_fecha_interpretada(client_admin):
    """Son dos valores encadenados y hay que ver los dos: un período que el
    modelo leyó bien y el intérprete no entendió se arregla en otro lugar que uno
    que el modelo no encontró."""
    with contestando(CATALOGO, extraccion_valida(periodo="marzo 2026")):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "01/03/2026" in respuesta.content.decode()


def test_un_periodo_ilegible_se_ve_en_la_pantalla(client_admin):
    """Su efecto —todos los borradores naciendo Activos— es de los que no dan
    ningún síntoma, así que tiene que decirse acá."""
    with contestando(CATALOGO, extraccion_valida(periodo="cuando salga")):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    contenido = respuesta.content.decode()
    assert "no se pudo interpretar" in contenido
    # Y el reparo del correo entero, que antes no se mostraba en ninguna parte.
    assert "Período ilegible" in contenido


def test_sin_periodo_la_pantalla_lo_dice_sin_alarmar(client_admin):
    """No anunciar fecha es el caso normal, no un problema."""
    with contestando(CATALOGO, extraccion_valida()):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "no encontró ninguno" in respuesta.content.decode()


def test_la_pantalla_dice_con_que_estado_nacerian_los_borradores(client_admin):
    """Es la consecuencia concreta del período, y es lo que se viene a mirar."""
    from datetime import timedelta

    from django.utils import timezone

    futuro = (timezone.localdate() + timedelta(days=60)).isoformat()

    with contestando(CATALOGO, extraccion_valida(periodo=futuro)):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "en Pre-venta" in respuesta.content.decode()


def test_un_periodo_pasado_deja_los_borradores_activos(client_admin):
    with contestando(CATALOGO, extraccion_valida(periodo="marzo 2020")):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "Activos" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# La confianza declarada, que es distinta de un reparo
# ---------------------------------------------------------------------------


def test_la_pantalla_muestra_la_confianza_que_no_es_alta(client_admin):
    confianza = {"isbn": "alta", "titulo": "alta", "precio": "baja"}

    with contestando(CATALOGO, extraccion_valida([producto(confianza=confianza)])):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    contenido = respuesta.content.decode()
    assert "precio" in contenido
    assert "baja" in contenido


def test_la_muestra_de_la_pantalla_anuncia_un_periodo_futuro(client_admin):
    """Si anunciara una fecha pasada, el banco de pruebas nunca ejercitaría la
    rama de Pre-venta, que es de la que hay que desconfiar."""
    from datetime import date

    with contestando(CATALOGO):
        respuesta = client_admin.get(URL)

    formulario = respuesta.context["form"]
    assert formulario.muestra.periodo > date.today()


# ---------------------------------------------------------------------------
# El modelo en uso, no el catálogo del servidor
#
# Acá se listaban todos los que el servidor declara. Con un servidor local eran
# dos o tres y parecía útil; con un proveedor remoto son cientos, y la pantalla
# se llenaba de nombres que a nadie le importan enterrando lo único que se vino
# a mirar.
# ---------------------------------------------------------------------------


def catalogo(*modelos):
    return {"data": [{"id": modelo} for modelo in modelos]}


def test_solo_se_muestra_el_modelo_configurado(client_admin):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modelo = "el/que/uso"
    configuracion.save()

    with contestando(catalogo("el/que/uso", "otro/cualquiera", "un/tercero")):
        contenido = client_admin.get(URL).content.decode()

    assert "el/que/uso" in contenido
    assert "otro/cualquiera" not in contenido
    assert "un/tercero" not in contenido


def test_se_avisa_si_el_servidor_no_ofrece_el_modelo_configurado(client_admin):
    """Adelanta el 404 más común —un identificador mal copiado— antes de gastar
    una corrida y recibirlo en medio de un procesamiento."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modelo = "un/modelo/que/no/existe"
    configuracion.save()

    with contestando(catalogo("otro/cualquiera")):
        contenido = client_admin.get(URL).content.decode()

    assert "No disponible en este servidor" in contenido


def test_con_el_modelo_disponible_se_dice_que_lo_ofrece(client_admin):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modelo = "el/que/uso"
    configuracion.save()

    with contestando(catalogo("el/que/uso")):
        contenido = client_admin.get(URL).content.decode()

    assert "Disponible" in contenido


def test_sin_modelo_declarado_se_muestran_los_cargados(client_admin):
    """Ahí sí la lista **es** la respuesta: es lo que el servidor va a contestar.
    Es el caso normal con un servidor local."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modelo = ""
    configuracion.save()

    with contestando(catalogo("el/unico/cargado")):
        contenido = client_admin.get(URL).content.decode()

    assert "el/unico/cargado" in contenido
    assert "se usa el que el servidor tenga cargado" in contenido


def test_el_total_de_modelos_se_dice_como_cifra(client_admin):
    """La cifra sirve —confirma que la dirección apunta a la API que se cree—;
    la lista de nombres, no."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modelo = "el/que/uso"
    configuracion.save()

    with contestando(catalogo("el/que/uso", "otro", "tercero")):
        contenido = client_admin.get(URL).content.decode()

    assert "ofrece 3 modelos en total" in contenido


def test_el_modo_no_nombra_proveedores(client_admin):
    """Los dos valores describen dónde corre el modelo; qué empresa lo hospeda es
    un dato de la dirección. Nombrar una en un desplegable la convierte en una
    recomendación que el proyecto no hace."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modo = ConfiguracionSistema.REMOTO
    configuracion.save()

    contenido = client_admin.get(URL).content.decode()

    assert "OpenRouter" not in contenido
    assert "LM Studio" not in contenido
