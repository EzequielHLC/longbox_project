"""Parámetros globales: clasificación del catálogo, precios y configuración."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    TablaPrecioReferencia,
    Tipo,
)
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import URL_PARAMETROS
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Catálogos sembrados con la instalación
# ---------------------------------------------------------------------------


def test_el_sistema_arranca_con_tipos_y_formatos_cargados():
    """Sin al menos un tipo no se puede dar de alta ningún producto: una
    instalación nueva no puede quedar trabada esperando que alguien adivine qué
    cargar primero."""
    assert Tipo.objects.filter(activo=True).exists()
    assert Formato.objects.filter(activo=True).exists()


@pytest.mark.parametrize("nombre", ["Manga", "Cómic"])
def test_los_tipos_con_grilla_de_tamanos_usan_formato(nombre):
    assert Tipo.objects.get(nombre=nombre).usa_formato is True


@pytest.mark.parametrize("nombre", ["Artbook", "Novela ligera", "Libro"])
def test_los_tipos_sin_grilla_de_tamanos_no_usan_formato(nombre):
    assert Tipo.objects.get(nombre=nombre).usa_formato is False


def test_el_sistema_arranca_con_los_grupos_de_etiqueta_sembrados():
    """No pretenden ser la taxonomía completa: existen para que la pantalla no
    arranque vacía y el primer producto se pueda describir sin inventar los ejes
    desde cero."""
    assert set(GrupoEtiqueta.objects.values_list("nombre", flat=True)) == {
        "Franquicia",
        "Género",
        "Colección",
        "Edición",
    }


def test_las_franquicias_sembradas_sobrevivieron_como_etiquetas():
    """La migración las trasladó en vez de borrarlas: RF-04 nombra estas tres al
    explicar por qué el universo es un discriminante independiente de la
    editorial, y eso sigue valiendo — cambió el mecanismo, no el dato."""
    franquicias = Etiqueta.objects.filter(grupo__nombre="Franquicia")

    assert set(franquicias.values_list("nombre", flat=True)) == {
        "Marvel",
        "Star Wars",
        "Universo DC",
    }


# ---------------------------------------------------------------------------
# La pantalla
# ---------------------------------------------------------------------------


def test_la_pantalla_muestra_los_cinco_catalogos(client_admin):
    """Los cinco se administran acá y no desde el admin de Django: es la
    pantalla que tiene el diseño del sistema y la que usa el personal."""
    PrecioReferenciaFactory(editorial=EditorialFactory(nombre="Ivrea"))
    EtiquetaFactory(nombre="Universo DC")

    contenido = client_admin.get(URL_PARAMETROS).content.decode()

    assert "Tipos de material" in contenido
    assert "Formatos" in contenido
    assert "Editoriales" in contenido
    assert "Etiquetas" in contenido
    assert "Tabla de precios de referencia" in contenido
    assert "Ivrea" in contenido
    assert "Universo DC" in contenido


def test_la_tabla_de_precios_se_puede_filtrar_por_editorial(client_admin):
    una = PrecioReferenciaFactory(editorial=EditorialFactory(nombre="Ivrea"))
    PrecioReferenciaFactory(editorial=EditorialFactory(nombre="Ovni Press"))

    respuesta = client_admin.get(URL_PARAMETROS, {"editorial": una.editorial.pk})

    assert list(respuesta.context["precios"]) == [una]


def test_se_avisa_cuando_una_editorial_no_tiene_precios(client_admin):
    EditorialFactory(nombre="Ivrea")

    contenido = client_admin.get(URL_PARAMETROS).content.decode()

    assert "sus productos van con precio a mano" in contenido


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_ve_los_parametros(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_PARAMETROS).status_code == 403


# ---------------------------------------------------------------------------
# Configuración: margen y stock por defecto
# ---------------------------------------------------------------------------


def test_la_configuracion_nace_con_los_valores_de_settings(settings):
    """Estrenar la pantalla no puede cambiar ningún cálculo."""
    ConfiguracionSistema.objects.all().delete()

    configuracion = ConfiguracionSistema.obtener()

    assert configuracion.margen_ganancia == settings.MARGEN_GANANCIA_GLOBAL
    assert configuracion.stock_inicial_por_defecto == settings.STOCK_INICIAL_POR_DEFECTO


def test_no_puede_haber_dos_configuraciones():
    """Si hubiera dos nadie sabría cuál rige, y el precio de los importados
    dependería de cuál se leyó primero.

    El intento falla de forma ruidosa, y así tiene que ser: quedarse callado y
    guardar la segunda dejaría el sistema con dos verdades sobre el margen.
    """
    from django.db import IntegrityError

    ConfiguracionSistema.obtener()

    with pytest.raises(IntegrityError):
        ConfiguracionSistema.objects.create(
            margen_ganancia=Decimal("0.9"), stock_inicial_por_defecto=3
        )


def test_la_configuracion_no_se_borra():
    configuracion = ConfiguracionSistema.obtener()

    with pytest.raises(Exception, match="no se borra"):
        configuracion.delete()


def test_guardar_el_margen_lo_deja_vigente_y_auditado(client_admin, administrador):
    respuesta = client_admin.post(
        URL_PARAMETROS, {"margen_ganancia": "0.55", "stock_inicial_por_defecto": "4"}
    )

    assert respuesta.status_code == 302
    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.margen_ganancia == Decimal("0.5500")
    assert configuracion.stock_inicial_por_defecto == 4
    assert configuracion.actualizado_por == administrador

    registro = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO
    ).latest("ocurrido_en")
    assert "margen" in registro.detalle


def test_un_margen_escrito_como_porcentaje_es_rechazado(client_admin):
    """40 en vez de 0,40 es el error más fácil de cometer, y multiplicaría por
    cuarenta el precio de todos los importados."""
    respuesta = client_admin.post(
        URL_PARAMETROS, {"margen_ganancia": "40", "stock_inicial_por_defecto": "1"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["margen_ganancia"]


def test_un_margen_negativo_es_rechazado(client_admin):
    respuesta = client_admin.post(
        URL_PARAMETROS, {"margen_ganancia": "-0.2", "stock_inicial_por_defecto": "1"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["margen_ganancia"]


def test_un_stock_por_defecto_absurdo_es_rechazado(client_admin):
    respuesta = client_admin.post(
        URL_PARAMETROS, {"margen_ganancia": "0.4", "stock_inicial_por_defecto": "999999"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["stock_inicial_por_defecto"]


# ---------------------------------------------------------------------------
# Alta y edición de los catálogos
# ---------------------------------------------------------------------------


def test_se_puede_dar_de_alta_una_editorial(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:editorial_crear"), {"nombre": "Ivrea", "activa": "on"}
    )

    assert respuesta.status_code == 302
    assert Editorial.objects.filter(nombre="Ivrea").exists()


def test_el_nombre_de_la_editorial_se_normaliza(client_admin):
    """Sin esto, en seis meses conviven tres editoriales con el mismo nombre y
    los productos quedan repartidos entre las tres."""
    client_admin.post(
        reverse("catalog:editorial_crear"), {"nombre": "  Ovni   Press  ", "activa": "on"}
    )

    assert Editorial.objects.get().nombre == "Ovni Press"


@pytest.mark.parametrize("repetido", ["ivrea", "IVREA", "  Ivrea "])
def test_una_editorial_repetida_es_rechazada(client_admin, repetido):
    EditorialFactory(nombre="Ivrea")

    respuesta = client_admin.post(
        reverse("catalog:editorial_crear"), {"nombre": repetido, "activa": "on"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre"]
    assert Editorial.objects.count() == 1


def test_se_puede_dar_de_alta_un_tipo_con_su_bandera(client_admin):
    """`usa_formato` es la única que quedó: es la que gobierna una restricción
    real, porque el formato entra en la tabla de precios. La de franquicia se
    fue con ella — las etiquetas aplican a todo tipo de material, así que la
    bandera habría valido siempre `True`."""
    respuesta = client_admin.post(
        reverse("catalog:tipo_crear"),
        {"nombre": "Fanzine", "usa_formato": "on", "activo": "on", "orden": "60"},
    )

    assert respuesta.status_code == 302
    assert Tipo.objects.get(nombre="Fanzine").usa_formato is True


def test_se_puede_editar_un_formato(client_admin):
    formato = FormatoFactory(nombre="B6")

    client_admin.post(
        reverse("catalog:formato_editar", args=[formato.pk]),
        {"nombre": "B6", "descripcion": "12,8 × 18,2 cm", "activo": "on", "orden": "20"},
    )

    formato.refresh_from_db()
    assert formato.descripcion == "12,8 × 18,2 cm"


def test_el_alta_de_un_parametro_queda_auditada(client_admin, administrador):
    client_admin.post(reverse("catalog:editorial_crear"), {"nombre": "Ivrea", "activa": "on"})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.PARAMETRO_MODIFICADO)
    assert registro.actor == administrador
    assert "Ivrea" in registro.detalle


# ---------------------------------------------------------------------------
# Tabla de precios
# ---------------------------------------------------------------------------


def test_se_puede_cargar_un_precio_de_referencia(client_admin):
    editorial = EditorialFactory(nombre="Ivrea")
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {"editorial": editorial.pk, "tipo": tipo.pk, "formato": formato.pk, "pvp": "12500"},
    )

    assert respuesta.status_code == 302
    assert TablaPrecioReferencia.objects.get().pvp == Decimal("12500.00")


def test_no_se_puede_repetir_la_misma_combinacion(client_admin):
    referencia = PrecioReferenciaFactory()

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {
            "editorial": referencia.editorial.pk,
            "tipo": referencia.tipo.pk,
            "formato": referencia.formato.pk,
            "pvp": "9999",
        },
    )

    assert respuesta.status_code == 200
    assert TablaPrecioReferencia.objects.count() == 1


def test_la_tabla_no_ofrece_tipos_que_no_usan_formato(client_admin):
    """Un artbook no tiene con qué completar la clave: su precio va a mano."""
    TipoFactory(nombre="Artbook", usa_formato=False)

    respuesta = client_admin.get(reverse("catalog:precio_crear"))

    ofrecidos = list(respuesta.context["form"].fields["tipo"].queryset)
    assert all(tipo.usa_formato for tipo in ofrecidos)


def test_un_precio_negativo_es_rechazado(client_admin):
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {"editorial": editorial.pk, "tipo": tipo.pk, "formato": formato.pk, "pvp": "-100"},
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["pvp"]


def test_eliminar_un_precio_no_toca_los_productos_ya_cargados(client_admin):
    """El producto guarda su precio: lo que se pierde es el pre-completado."""
    referencia = PrecioReferenciaFactory(pvp="12500")
    producto = ProductoFactory(
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
        precio=Decimal("12500.00"),
        precio_referencia=referencia,
    )

    respuesta = client_admin.post(reverse("catalog:precio_eliminar", args=[referencia.pk]))

    assert respuesta.status_code == 302
    assert not TablaPrecioReferencia.objects.exists()
    producto.refresh_from_db()
    assert producto.precio == Decimal("12500.00")
    assert producto.precio_referencia is None


def test_la_baja_de_un_precio_pide_confirmacion(client_admin):
    referencia = PrecioReferenciaFactory()

    respuesta = client_admin.get(reverse("catalog:precio_eliminar", args=[referencia.pk]))

    assert respuesta.status_code == 200
    assert TablaPrecioReferencia.objects.exists()


@pytest.mark.parametrize(
    "pantalla",
    [
        "catalog:editorial_crear",
        "catalog:tipo_crear",
        "catalog:formato_crear",
        "catalog:precio_crear",
    ],
)
def test_las_altas_de_parametros_son_solo_del_administrador(client, cajero, pantalla):
    client.force_login(cajero)

    assert client.get(reverse(pantalla)).status_code == 403


# ---------------------------------------------------------------------------
# Etiquetas y sus grupos
# ---------------------------------------------------------------------------


def test_se_puede_dar_de_alta_una_etiqueta(client_admin):
    grupo = GrupoEtiqueta.objects.get(nombre="Género")

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "Shonen", "grupo": grupo.pk, "activa": "on"},
    )

    assert respuesta.status_code == 302
    assert Etiqueta.objects.filter(nombre="Shonen", grupo=grupo, activa=True).exists()


def test_el_nombre_de_la_etiqueta_se_normaliza(client_admin):
    grupo = GrupoEtiqueta.objects.get(nombre="Género")

    client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "  Novela   gráfica  ", "grupo": grupo.pk, "activa": "on"},
    )

    assert Etiqueta.objects.filter(nombre="Novela gráfica").exists()


def test_una_etiqueta_repetida_en_el_mismo_grupo_es_rechazada(client_admin):
    """La comparación ignora mayúsculas: es la misma etiqueta escrita distinto."""
    grupo = GrupoEtiqueta.objects.get(nombre="Franquicia")

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "universo dc", "grupo": grupo.pk, "activa": "on"},
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre"]
    assert Etiqueta.objects.filter(nombre__iexact="universo dc").count() == 1


def test_el_mismo_nombre_en_otro_grupo_si_se_puede(client_admin):
    """La unicidad es por grupo: "Terror" puede ser un género y también el
    nombre de una colección, y son dos etiquetas distintas."""
    genero = GrupoEtiqueta.objects.get(nombre="Género")
    coleccion = GrupoEtiqueta.objects.get(nombre="Colección")
    EtiquetaFactory(nombre="Terror", grupo=genero)

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "Terror", "grupo": coleccion.pk, "activa": "on"},
    )

    assert respuesta.status_code == 302
    assert Etiqueta.objects.filter(nombre="Terror").count() == 2


def test_una_etiqueta_de_una_letra_es_rechazada(client_admin):
    """Una sola letra no describe nada y casi siempre es un enter de más."""
    grupo = GrupoEtiqueta.objects.get(nombre="Género")

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"), {"nombre": "S", "grupo": grupo.pk, "activa": "on"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre"]


def test_una_etiqueta_sin_grupo_es_rechazada(client_admin):
    """El grupo es lo que la hace filtrable: sin él no se sabe en qué faceta de
    la tienda tendría que aparecer."""
    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"), {"nombre": "Shonen", "activa": "on"}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["grupo"]
    assert not Etiqueta.objects.filter(nombre="Shonen").exists()


def test_el_alta_de_etiqueta_queda_auditada(client_admin):
    grupo = GrupoEtiqueta.objects.get(nombre="Género")

    client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "Shonen", "grupo": grupo.pk, "activa": "on"},
    )

    registro = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO
    ).latest("ocurrido_en")
    assert "Shonen" in registro.detalle


def test_se_puede_dar_de_alta_un_grupo_de_etiquetas(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:grupo_etiqueta_crear"),
        {"nombre": "Formato de lectura", "activo": "on", "orden": "50"},
    )

    assert respuesta.status_code == 302
    assert GrupoEtiqueta.objects.filter(nombre="Formato de lectura").exists()


def test_un_grupo_repetido_es_rechazado(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:grupo_etiqueta_crear"),
        {"nombre": "género", "activo": "on", "orden": "0"},
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre"]


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_administra_etiquetas(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(reverse("catalog:etiqueta_crear")).status_code == 403
    assert client.get(reverse("catalog:grupo_etiqueta_crear")).status_code == 403


# ---------------------------------------------------------------------------
# Formatos por tipo
# ---------------------------------------------------------------------------


def test_un_formato_sin_tipos_declarados_es_universal():
    """El vacío significa "en todos" y no "en ninguno": olvidarse de declararlos
    deja el comportamiento anterior a que el campo existiera, no un formato
    invisible."""
    formato = FormatoFactory(nombre="Tapa dura")

    assert formato.aplica_a(Tipo.objects.get(nombre="Manga"))
    assert formato.aplica_a(Tipo.objects.get(nombre="Cómic"))


def test_un_formato_con_tipos_declarados_solo_aplica_a_esos():
    manga = Tipo.objects.get(nombre="Manga")
    comic = Tipo.objects.get(nombre="Cómic")
    grapa = FormatoFactory(nombre="Grapa")
    grapa.tipos.add(comic)

    assert grapa.aplica_a(comic)
    assert not grapa.aplica_a(manga)


def test_el_alta_solo_ofrece_los_formatos_del_tipo_elegido(client_admin):
    """Es lo que baja el desplegable de quince opciones a las que aplican, en la
    pantalla que más campos pide."""
    manga = Tipo.objects.get(nombre="Manga")
    comic = Tipo.objects.get(nombre="Cómic")
    tankobon = FormatoFactory(nombre="Tankōbon")
    tankobon.tipos.add(manga)
    grapa = FormatoFactory(nombre="Grapa")
    grapa.tipos.add(comic)
    universal = FormatoFactory(nombre="Tapa dura")

    respuesta = client_admin.get(reverse("catalog:lote_nacional"))
    formatos = respuesta.context["reglas_de_tipo"][str(manga.pk)]["formatos"]

    assert str(tankobon.pk) in formatos
    assert str(universal.pk) in formatos
    assert str(grapa.pk) not in formatos


def test_un_precio_de_referencia_con_un_formato_que_no_aplica_es_rechazado(client_admin):
    """Una fila para una combinación imposible es una fila muerta: no va a
    coincidir nunca con ningún producto y confunde a quien la lea."""
    manga = Tipo.objects.get(nombre="Manga")
    grapa = FormatoFactory(nombre="Grapa")
    grapa.tipos.add(Tipo.objects.get(nombre="Cómic"))
    editorial = EditorialFactory(nombre="Ivrea")

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {"editorial": editorial.pk, "tipo": manga.pk, "formato": grapa.pk, "pvp": "12000"},
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["formato"]
    assert not TablaPrecioReferencia.objects.filter(formato=grapa).exists()


# ---------------------------------------------------------------------------
# El modelo de lenguaje (A16, extendido)
#
# Se configura desde acá y no desde el `.env` por una restricción que no es
# técnica: **el sistema se demuestra desplegado**, y el modelo local corre en una
# máquina que no viaja. Una de sus dos mitades es una credencial, y eso cambia
# las reglas de la pantalla.
# ---------------------------------------------------------------------------


def datos_del_modelo(**cambios):
    base = {
        "guardar_modelo": "1",
        "llm_modo": ConfiguracionSistema.LOCAL,
        "llm_url": "http://127.0.0.1:1234/v1/chat/completions",
        "llm_modelo": "",
        "api_key": "",
        "llm_timeout": "300",
        "llm_temperatura": "0",
    }
    base.update(cambios)
    return base


@pytest.mark.django_db
def test_se_puede_cambiar_a_un_proveedor_remoto(client_admin):
    client_admin.post(
        URL_PARAMETROS,
        datos_del_modelo(
            llm_modo=ConfiguracionSistema.REMOTO,
            llm_url="https://openrouter.ai/api/v1/chat/completions",
            llm_modelo="un/modelo:free",
            api_key="sk-or-secreta",
        ),
    )

    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.usa_modelo_remoto
    assert configuracion.llm_modelo == "un/modelo:free"
    assert configuracion.llm_api_key == "sk-or-secreta"


@pytest.mark.django_db
def test_un_proveedor_remoto_sin_clave_se_rechaza(client_admin):
    """Sin clave no va a contestar nunca, y el fallo aparecería recién en la
    pantalla de diagnóstico. Se avisa donde se puede arreglar.

    Se vacía primero la que trae la semilla del entorno: el formulario solo
    exige que **haya** una, y juzgar si sirve es tarea del diagnóstico — que
    ahora sabe leer un 401 como "la credencial no vale".
    """
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = ""
    configuracion.save()

    respuesta = client_admin.post(
        URL_PARAMETROS,
        datos_del_modelo(llm_modo=ConfiguracionSistema.REMOTO, llm_modelo="un/modelo", api_key=""),
    )

    assert respuesta.status_code == 200
    assert ConfiguracionSistema.obtener().llm_modo == ConfiguracionSistema.LOCAL


@pytest.mark.django_db
def test_un_proveedor_remoto_sin_modelo_se_rechaza(client_admin):
    """Los proveedores hospedan cientos: sin nombrarlo devuelven un error que
    cuesta interpretar."""
    respuesta = client_admin.post(
        URL_PARAMETROS,
        datos_del_modelo(
            llm_modo=ConfiguracionSistema.REMOTO, llm_modelo="", api_key="sk-or-secreta"
        ),
    )

    assert respuesta.status_code == 200
    assert ConfiguracionSistema.obtener().llm_modo == ConfiguracionSistema.LOCAL


@pytest.mark.django_db
def test_dejar_la_clave_vacia_no_la_borra(client_admin):
    """El campo llega vacío siempre, así que un vacío significa "no la cambies"
    y no "borrala". Sin esto, ajustar el timeout dejaría el sistema sin clave."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modo = ConfiguracionSistema.REMOTO
    configuracion.llm_api_key = "sk-or-original"
    configuracion.llm_modelo = "un/modelo"
    configuracion.save()

    client_admin.post(
        URL_PARAMETROS,
        datos_del_modelo(
            llm_modo=ConfiguracionSistema.REMOTO,
            llm_modelo="un/modelo",
            api_key="",
            llm_timeout="120",
        ),
    )

    configuracion.refresh_from_db()
    assert configuracion.llm_api_key == "sk-or-original"
    assert configuracion.llm_timeout == 120


@pytest.mark.django_db
def test_la_clave_nunca_se_dibuja_entera(client_admin):
    """La pantalla no puede ser un lugar del que copiar el secreto."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = "sk-or-v1-0123456789abcdef"
    configuracion.save()

    contenido = client_admin.get(URL_PARAMETROS).content.decode()

    assert "sk-or-v1-0123456789abcdef" not in contenido
    assert "…cdef" in contenido


@pytest.mark.django_db
def test_la_clave_no_entra_en_la_auditoria(client_admin):
    """El log es inmutable y consultable: un secreto que pasa por ahí queda ahí
    para siempre. Se registra **que** cambió, que es lo que hace falta saber."""
    client_admin.post(
        URL_PARAMETROS,
        datos_del_modelo(
            llm_modo=ConfiguracionSistema.REMOTO,
            llm_modelo="un/modelo",
            api_key="sk-or-secretisima",
        ),
    )

    detalles = " ".join(
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PARAMETRO_MODIFICADO).values_list(
            "detalle", flat=True
        )
    )
    assert "sk-or-secretisima" not in detalles
    assert "se reemplazó la clave" in detalles


@pytest.mark.django_db
def test_el_cambio_de_modelo_queda_auditado(client_admin):
    client_admin.post(URL_PARAMETROS, datos_del_modelo(llm_modelo="otro/modelo"))

    detalle = (
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PARAMETRO_MODIFICADO)
        .first()
        .detalle
    )
    assert "otro/modelo" in detalle


@pytest.mark.django_db
def test_guardar_el_modelo_no_toca_el_margen(client_admin):
    """Son dos formularios porque se tocan por motivos distintos: un error en
    uno no puede borrar lo escrito en el otro."""
    configuracion = ConfiguracionSistema.obtener()
    margen = configuracion.margen_ganancia

    client_admin.post(URL_PARAMETROS, datos_del_modelo(llm_modelo="otro/modelo"))

    configuracion.refresh_from_db()
    assert configuracion.margen_ganancia == margen


@pytest.mark.django_db
def test_una_direccion_sin_la_ruta_de_la_api_se_rechaza(client_admin):
    """Pegar la dirección base del servidor es el error más natural acá, y el
    formulario lo aceptaba: quedaba una configuración que no puede funcionar y
    el diagnóstico decía "no parece una API compatible", que es verdad pero no
    dice qué corregir."""
    respuesta = client_admin.post(URL_PARAMETROS, datos_del_modelo(llm_url="http://127.0.0.1:1234"))

    assert respuesta.status_code == 200
    assert "Falta la ruta de la API" in respuesta.content.decode()


@pytest.mark.django_db
def test_la_direccion_completa_se_acepta_en_los_dos_modos(client_admin):
    for url in (
        "http://127.0.0.1:1234/v1/chat/completions",
        "https://un-proveedor.test/api/v1/chat/completions",
    ):
        client_admin.post(URL_PARAMETROS, datos_del_modelo(llm_url=url))
        assert ConfiguracionSistema.obtener().llm_url == url


@pytest.mark.django_db
def test_la_barra_final_de_mas_no_molesta(client_admin):
    client_admin.post(
        URL_PARAMETROS, datos_del_modelo(llm_url="http://127.0.0.1:1234/v1/chat/completions/")
    )

    assert ConfiguracionSistema.obtener().llm_url.endswith("completions")
