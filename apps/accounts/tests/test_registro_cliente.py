"""CU-CLI-ALT — Registrar Cuenta de Cliente."""

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.forms import (
    MENSAJE_CORREO_YA_REGISTRADO,
    MENSAJE_NOMBRE_CORTO,
    MENSAJE_NOMBRE_INVALIDO,
    MENSAJE_POLITICA_OBLIGATORIA,
)
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_REGISTRO = reverse("accounts:registro_cliente")
URL_RECUPERACION = reverse("accounts:password_reset")
URL_TIENDA = reverse("core:tienda")

CONTRASENA = "ComicRojo2026"

DATOS_REGISTRO = {
    "nombre_completo": "Lucía Gómez",
    "email": "lucia@correo.test",
    "password1": CONTRASENA,
    "password2": CONTRASENA,
    "acepta_politica": "on",
}

# Los dos bloques opcionales, cada uno completo. Se agregan solo en los tests
# que los necesitan: el registro tiene que andar igual sin ellos.
TELEFONO = {
    "telefono_pais": "+54",
    "telefono_area": "376",
    "telefono_numero": "4112233",
}

DIRECCION = {
    "direccion": "Av. Mitre 1234",
    "localidad": "Posadas",
    "codigo_postal": "N3300ABC",
    "provincia": "Misiones",
}


def registrar(client, **cambios):
    return client.post(URL_REGISTRO, {**DATOS_REGISTRO, **cambios})


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------


def test_el_registro_crea_una_cuenta_de_cliente_activa(client):
    respuesta = registrar(client)

    assert respuesta.status_code == 302
    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.rol == Usuario.CLIENTE
    assert usuario.estado == Usuario.ACTIVO
    # A diferencia del alta de personal (CU-USR-ALT), la cuenta puede entrar ya.
    assert usuario.is_active is True
    assert usuario.get_full_name() == "Lucía Gómez"


def test_la_contrasena_se_guarda_hasheada(client):
    """RNF-04: en la base no puede quedar la contraseña en texto plano."""
    registrar(client)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.password != CONTRASENA
    assert CONTRASENA not in usuario.password
    assert usuario.check_password(CONTRASENA)


def test_el_registro_inicia_sesion_automaticamente(client):
    respuesta = registrar(client)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert client.session["_auth_user_id"] == str(usuario.pk)
    # Paso 5: queda adentro, en el módulo que le corresponde a su rol.
    assert respuesta.url == URL_TIENDA


def test_el_registro_envia_el_correo_de_bienvenida(client):
    registrar(client)

    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == ["lucia@correo.test"]
    assert "bienvenid" in correo.subject.lower()


def test_el_registro_queda_en_el_log_de_auditoria(client):
    registrar(client)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REGISTRO_CLIENTE)
    assert registro.actor == usuario
    assert registro.objetivo_email == "lucia@correo.test"


def test_el_inicio_de_sesion_automatico_tambien_se_audita(client):
    """El `login()` de la vista pasa por la misma signal que el CU-AUT-INI."""
    registrar(client)

    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.INICIO_SESION).count() == 1


def test_los_datos_opcionales_se_guardan(client):
    registrar(client, **TELEFONO, **DIRECCION)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.telefono_pais == "+54"
    assert usuario.telefono_area == "376"
    assert usuario.telefono_numero == "4112233"
    assert usuario.direccion == "Av. Mitre 1234"
    assert usuario.codigo_postal == "N3300ABC"
    assert usuario.provincia == "Misiones"


def test_los_datos_opcionales_pueden_quedar_vacios(client):
    registrar(client)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.telefono == ""
    assert usuario.direccion_completa == ""


# ---------------------------------------------------------------------------
# Consentimiento informado (Ley 25.326)
# ---------------------------------------------------------------------------


def test_la_aceptacion_de_la_politica_queda_persistida(client):
    registrar(client)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    # No alcanza con validar el checkbox y descartarlo: es la evidencia del
    # consentimiento, y tiene que quedar fechada junto con la cuenta.
    assert usuario.acepto_politica_privacidad is True
    assert usuario.fecha_aceptacion_politica is not None


def test_sin_aceptar_la_politica_no_se_crea_la_cuenta(client):
    respuesta = registrar(client, acepta_politica="")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["acepta_politica"]
    assert MENSAJE_POLITICA_OBLIGATORIA in respuesta.content.decode()
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()
    assert mail.outbox == []


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------


def test_un_correo_ya_registrado_es_rechazado_y_ofrece_recuperar_la_contrasena(client):
    UsuarioFactory(email="lucia@correo.test", rol=Usuario.CLIENTE)

    respuesta = registrar(client)

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert MENSAJE_CORREO_YA_REGISTRADO in contenido
    # Excepción 1 del CU: el rechazo viene con enlace a recuperación (CU-AUT-REC).
    assert URL_RECUPERACION in contenido
    # Y no se crea un duplicado.
    assert Usuario.objects.filter(email="lucia@correo.test").count() == 1


def test_el_correo_repetido_se_detecta_aunque_cambie_la_capitalizacion(client):
    """El modelo normaliza a minúsculas: "Lucia@" y "lucia@" son la misma cuenta."""
    UsuarioFactory(email="lucia@correo.test", rol=Usuario.CLIENTE)

    respuesta = registrar(client, email="LUCIA@correo.test")

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_YA_REGISTRADO in respuesta.content.decode()
    assert Usuario.objects.filter(email__iexact="lucia@correo.test").count() == 1


def test_contrasenas_distintas_conservan_los_datos_ya_ingresados(client):
    respuesta = registrar(client, password2="OtraClave2026", **TELEFONO)

    assert respuesta.status_code == 200
    formulario = respuesta.context["form"]
    assert formulario.errors["password2"]
    # Excepción 2 del CU: el formulario no se reinicia vacío.
    assert formulario["nombre_completo"].value() == "Lucía Gómez"
    assert formulario["email"].value() == "lucia@correo.test"
    assert formulario["telefono_numero"].value() == "4112233"
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


def test_una_contrasena_que_no_cumple_los_requisitos_minimos_es_rechazada(client):
    """Los requisitos los ponen los `AUTH_PASSWORD_VALIDATORS`, no reglas propias."""
    respuesta = registrar(client, password1="123", password2="123")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["password2"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


def test_un_campo_obligatorio_vacio_no_crea_la_cuenta(client):
    respuesta = registrar(client, nombre_completo="")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre_completo"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


# ---------------------------------------------------------------------------
# Nombre: largo mínimo y caracteres permitidos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ["An", "A", "A.B", "  x  "])
def test_un_nombre_de_menos_de_tres_letras_es_rechazado(client, nombre):
    """Se cuentan letras, no caracteres: "A.B" tiene tres pero no es un nombre."""
    respuesta = registrar(client, nombre_completo=nombre)

    assert respuesta.status_code == 200
    # Contra la lista de errores y no contra su HTML: al renderizarse, el
    # apóstrofo del mensaje se escapa a `&#x27;` y la comparación fallaría.
    assert MENSAJE_NOMBRE_CORTO in respuesta.context["form"].errors["nombre_completo"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


@pytest.mark.parametrize(
    "nombre",
    ["Lucía2", "Lucía <script>", "Lucía_Gómez", "Lucía@casa", "Lucía #1", "María/José"],
)
def test_un_nombre_con_caracteres_especiales_es_rechazado(client, nombre):
    respuesta = registrar(client, nombre_completo=nombre)

    assert respuesta.status_code == 200
    assert MENSAJE_NOMBRE_INVALIDO in respuesta.context["form"].errors["nombre_completo"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


@pytest.mark.parametrize(
    "nombre",
    [
        "Lucía Gómez",
        "María José D'Angelo",  # apóstrofo
        "Ana María Pérez-Sánchez",  # guion en el apellido compuesto
        "Juan C. Rodríguez",  # abreviatura con punto
        "Nicolás Müller",  # diéresis
        "Ñuñez",  # eñe inicial
    ],
)
def test_los_nombres_reales_se_aceptan(client, nombre):
    """La validación no puede dejar afuera apellidos que existen de verdad."""
    respuesta = registrar(client, nombre_completo=nombre)

    assert respuesta.status_code == 302
    assert Usuario.objects.get(email="lucia@correo.test").get_full_name() == nombre


def test_los_espacios_de_mas_se_limpian_antes_de_validar(client):
    registrar(client, nombre_completo="  Lucía   Gómez  ")

    assert Usuario.objects.get(email="lucia@correo.test").get_full_name() == "Lucía Gómez"


# ---------------------------------------------------------------------------
# Teléfono: código de país + código de área + número
# ---------------------------------------------------------------------------


def test_el_pais_viene_predeterminado_en_argentina(client):
    respuesta = client.get(URL_REGISTRO)

    assert respuesta.context["form"]["telefono_pais"].value() == "+54"


def test_los_codigos_de_pais_salen_del_catalogo_externo(client):
    """No hay una lista escrita a mano: viene del servicio (o de su respaldo)."""
    opciones = dict(client.get(URL_REGISTRO).context["form"].fields["telefono_pais"].choices)

    assert len(opciones) > 100
    assert opciones["+54"] == "Argentina (+54)"


def test_un_codigo_de_pais_fuera_del_catalogo_es_rechazado(client):
    respuesta = registrar(client, **{**TELEFONO, "telefono_pais": "+999"})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_pais"]


@pytest.mark.parametrize("numero", ["-1", "0", "no tengo", "4112233a", "12345", "41122334455"])
def test_un_numero_de_telefono_invalido_es_rechazado(client, numero):
    """El caso que motivó desarmar el teléfono: un "-1" no es un teléfono."""
    respuesta = registrar(client, **{**TELEFONO, "telefono_numero": numero})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_numero"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


@pytest.mark.parametrize("area", ["-1", "abc", "1", "1234567"])
def test_un_codigo_de_area_invalido_es_rechazado(client, area):
    respuesta = registrar(client, **{**TELEFONO, "telefono_area": area})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_area"]


@pytest.mark.parametrize("pais", ["54", "+", "+abc", "+1234"])
def test_un_codigo_de_pais_invalido_es_rechazado(client, pais):
    respuesta = registrar(client, **{**TELEFONO, "telefono_pais": pais})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_pais"]


@pytest.mark.parametrize(
    ("area_tipeada", "numero_tipeado"),
    [
        # La gente tiene anotado su teléfono con el 0 y el 15 adelante, y lo
        # escribe con espacios o guiones. Todo eso se limpia, no se rechaza:
        # el dato que quiso dar es correcto, solo viene con adornos.
        ("0376", "154112233"),
        ("376", "411 2233"),
        ("376", "411-2233"),
        (" 376 ", " 4112233 "),
    ],
)
def test_el_telefono_se_normaliza_en_vez_de_rechazarse(client, area_tipeada, numero_tipeado):
    registrar(client, telefono_area=area_tipeada, telefono_numero=numero_tipeado)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.telefono_area == "376"
    assert usuario.telefono_numero == "4112233"
    assert usuario.telefono == "+54 376 4112233"


def test_un_numero_sin_codigo_de_area_es_rechazado(client):
    """Medio teléfono no se puede discar: o van las dos partes o ninguna."""
    respuesta = registrar(client, telefono_numero="4112233")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_area"]


def test_un_codigo_de_area_sin_numero_es_rechazado(client):
    respuesta = registrar(client, telefono_area="376")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono_numero"]


def test_el_pais_vacio_vuelve_al_predeterminado(client):
    registrar(client, **{**TELEFONO, "telefono_pais": ""})

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.telefono_pais == "+54"


# ---------------------------------------------------------------------------
# Dirección de envío
# ---------------------------------------------------------------------------


def test_la_direccion_completa_se_guarda_con_todos_sus_campos(client):
    registrar(
        client,
        **DIRECCION,
        direccion_linea2="Barrio Villa Sarita",
        depto="3.º B",
        comentarios_envio="Timbre 4, entregar por la tarde",
    )

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.direccion_linea2 == "Barrio Villa Sarita"
    assert usuario.depto == "3.º B"
    assert usuario.localidad == "Posadas"
    assert usuario.comentarios_envio == "Timbre 4, entregar por la tarde"
    assert usuario.direccion_completa == (
        "Av. Mitre 1234, 3.º B, Barrio Villa Sarita, N3300ABC Posadas, Misiones"
    )


@pytest.mark.parametrize("faltante", ["direccion", "localidad", "codigo_postal", "provincia"])
def test_una_direccion_incompleta_es_rechazada(client, faltante):
    """Sin calle, localidad, código postal o provincia no se puede despachar nada."""
    respuesta = registrar(client, **{**DIRECCION, faltante: ""})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors[faltante]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


def test_los_campos_accesorios_solos_tampoco_alcanzan(client):
    """Un depto sin dirección no es una dirección."""
    respuesta = registrar(client, depto="3.º B")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["direccion"]


@pytest.mark.parametrize("codigo", ["330", "33000", "ABC", "N33ABC"])
def test_un_codigo_postal_invalido_es_rechazado(client, codigo):
    respuesta = registrar(client, **{**DIRECCION, "codigo_postal": codigo})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["codigo_postal"]


def test_el_codigo_postal_se_guarda_en_mayusculas(client):
    registrar(client, **{**DIRECCION, "codigo_postal": "n3300abc"})

    assert Usuario.objects.get(email="lucia@correo.test").codigo_postal == "N3300ABC"


def test_una_provincia_inventada_es_rechazada(client):
    """El desplegable no es la restricción: el servidor valida contra el catálogo."""
    respuesta = registrar(client, **{**DIRECCION, "provincia": "Tokio"})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["provincia"]
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


def test_la_provincia_arranca_sin_elegir(client):
    respuesta = client.get(URL_REGISTRO)

    assert respuesta.context["form"]["provincia"].value() in ("", None)


def test_las_provincias_del_formulario_salen_del_catalogo_oficial(client):
    """No hay una lista escrita a mano: viene de georef (o de su respaldo)."""
    opciones = dict(client.get(URL_REGISTRO).context["form"].fields["provincia"].choices)

    # 24 jurisdicciones más la opción vacía "Seleccionar…".
    assert len(opciones) == 25
    assert "Misiones" in opciones
    assert "Tierra del Fuego, Antártida e Islas del Atlántico Sur" in opciones


def test_el_registro_funciona_aunque_la_api_de_provincias_este_caida(client):
    """La fixture `sin_red` ya simula la caída: esto verifica que no bloquea."""
    respuesta = registrar(client, **DIRECCION)

    assert respuesta.status_code == 302
    assert Usuario.objects.get(email="lucia@correo.test").provincia == "Misiones"


# ---------------------------------------------------------------------------
# Coherencia entre el código postal y la provincia
# ---------------------------------------------------------------------------


def test_un_cpa_de_otra_provincia_es_rechazado(client):
    """La N de N3300ABC es de Misiones: con Corrientes elegida, algo está mal."""
    respuesta = registrar(client, **{**DIRECCION, "provincia": "Corrientes"})

    assert respuesta.status_code == 200
    assert "Misiones" in str(respuesta.context["form"].errors["codigo_postal"])
    assert not Usuario.objects.filter(email="lucia@correo.test").exists()


def test_el_codigo_postal_de_cuatro_digitos_no_se_contradice(client):
    """Sin letra no declara provincia, así que no hay nada que cruzar."""
    corrientes = {**DIRECCION, "codigo_postal": "3300", "provincia": "Corrientes"}

    respuesta = registrar(client, **corrientes)

    assert respuesta.status_code == 302
    assert Usuario.objects.get(email="lucia@correo.test").provincia == "Corrientes"


def test_un_cpa_que_coincide_con_la_provincia_pasa(client):
    corrientes = {**DIRECCION, "codigo_postal": "W3400ABC", "provincia": "Corrientes"}

    respuesta = registrar(client, **corrientes)

    assert respuesta.status_code == 302


# ---------------------------------------------------------------------------
# Accesibilidad de los errores
# ---------------------------------------------------------------------------


def test_un_campo_con_error_queda_marcado_para_el_lector_de_pantalla(client):
    """El borde rojo no existe para quien no ve la pantalla."""
    contenido = registrar(client, telefono_numero="-1").content.decode()

    assert 'aria-invalid="true"' in contenido
    assert 'aria-describedby="id_telefono_numero_error_1"' in contenido
    assert 'id="id_telefono_numero_error_1"' in contenido


def test_un_campo_sin_error_no_lleva_la_marca(client):
    contenido = client.get(URL_REGISTRO).content.decode()

    assert "aria-invalid" not in contenido


# ---------------------------------------------------------------------------
# Precondiciones y seguridad (RNF-03)
# ---------------------------------------------------------------------------


def test_el_formulario_es_de_acceso_publico(client):
    respuesta = client.get(URL_REGISTRO)

    assert respuesta.status_code == 200


def test_quien_ya_tiene_sesion_no_vuelve_al_registro(client, cliente):
    """Precondición del CU: el registro es para quien no tiene sesión previa."""
    client.force_login(cliente)

    respuesta = client.get(URL_REGISTRO)

    assert respuesta.status_code == 302
    assert respuesta.url == URL_TIENDA


def test_el_rol_no_se_puede_elegir_desde_el_formulario(client):
    """El rol lo fija el servidor: un POST con `rol` no puede escalar permisos."""
    registrar(client, rol=Usuario.ADMINISTRADOR)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.rol == Usuario.CLIENTE
    assert usuario.is_staff is False
    assert usuario.is_superuser is False


def test_el_estado_no_se_puede_elegir_desde_el_formulario(client):
    registrar(client, estado=Usuario.INACTIVO)

    usuario = Usuario.objects.get(email="lucia@correo.test")
    assert usuario.estado == Usuario.ACTIVO
