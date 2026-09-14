"""Lectura de un correo de novedades: de bytes MIME a texto parseable.

No toca la base: `apps/suppliers/correos.py` no conoce Django. Lo que se prueba
acá es lo que decide si el pipeline entiende o no lo que le llega, y son las dos
correcciones que este módulo le hace a la fuente: que la tabla no se aplane
(15) y que las portadas vienen embebidas y no por URL (16).
"""

import pytest

from apps.suppliers import correos
from apps.suppliers.tests import correos_de_ejemplo as ejemplo

# El archivo no necesita base: son bytes entrando y texto saliendo.


def leer_novedades(**cambios):
    return correos.leer(ejemplo.correo_de_novedades(**cambios))


# ---------------------------------------------------------------------------
# Encabezados
# ---------------------------------------------------------------------------


def test_el_remitente_sale_pelado_aunque_venga_con_nombre_de_fantasia():
    """Un `From` real llega como `"Novedades Ivrea" <novedades@ivrea.test>` y el
    matcheo del proveedor compara direcciones, no cadenas enteras."""
    assert leer_novedades().remitente == "novedades@ivrea.test"


def test_el_remitente_se_normaliza_a_minuscula():
    """La caja de una dirección no la distingue, y el proveedor se guarda en
    minúscula: comparar en crudo dejaría afuera mensajes legítimos."""
    assert leer_novedades(remitente="Novedades@Ivrea.TEST").remitente == "novedades@ivrea.test"


def test_se_leen_asunto_identificador_y_fecha():
    leido = leer_novedades()

    assert leido.asunto == "Novedades marzo 2026"
    assert leido.message_id == "<marzo-2026@ivrea.test>"
    assert leido.fecha is not None


def test_un_correo_sin_identificador_lo_deja_vacio():
    """Sin `Message-ID` no hay forma de saber si un correo ya se leyó. Que salga
    vacío es lo que le permite al servicio descartarlo en vez de encolarlo de
    nuevo en cada pasada."""
    assert leer_novedades(message_id=None).message_id == ""


# ---------------------------------------------------------------------------
# La tabla — corrección 15
# ---------------------------------------------------------------------------


def test_cada_producto_queda_en_una_fila_con_sus_columnas():
    """Es la corrección 15: aplanar a texto plano rompe la asociación
    fila-columna y el modelo empieza a atribuirle a un tomo el precio del
    siguiente."""
    contenido = leer_novedades().contenido
    filas = [linea for linea in contenido.splitlines() if linea.startswith("|")]

    # El encabezado más los tres productos.
    assert len(filas) == 4
    assert "| 9789878271583 |" in contenido
    assert "| Berserk Deluxe | 5 | Tapa dura |" in contenido


def test_el_precio_queda_en_la_misma_fila_que_su_titulo():
    """El error que la corrección evita no da ningún síntoma: se descubre tres
    meses después mirando un precio raro."""
    filas = [linea for linea in leer_novedades().contenido.splitlines() if linea.startswith("|")]
    de_blue_period = next(fila for fila in filas if "Blue Period" in fila)

    assert "$11500" in de_blue_period
    assert "$24900" not in de_blue_period


def test_la_prosa_que_envuelve_la_tabla_no_se_pierde():
    """Las tablas vienen anidadas —el HTML de un correo maqueta con tablas— y
    ahí vive el período del envío, que es de donde los borradores van a heredar
    la fecha. Con una sola fila "actual", abrir la tabla interna pisaba la
    externa y esto desaparecía sin dejar rastro."""
    contenido = leer_novedades().contenido

    assert "Novedades de marzo 2026" in contenido
    assert "Los pedidos se reciben hasta el 20 de marzo." in contenido


def test_una_fila_de_una_sola_celda_no_parece_un_producto():
    """El encabezado con el logo es maquetado, no datos. Marcarlo con barras lo
    haría parecer un producto de una sola columna."""
    lineas = leer_novedades().contenido.splitlines()
    del_logo = next(linea for linea in lineas if "logo@ivrea.test" in linea)

    assert not del_logo.startswith("|")


def test_la_hoja_de_estilos_no_entra_al_contenido():
    assert ".x{color:red}" not in leer_novedades().contenido


def test_un_correo_de_prosa_se_lee_como_prosa():
    """Un aviso de demora no tiene tabla, y tiene que salir legible igual: es el
    otro tipo de correo que llega por la misma casilla."""
    leido = correos.leer(ejemplo.correo_de_demora())

    assert "se reprograma para mayo" in leido.contenido
    assert "|" not in leido.contenido


# ---------------------------------------------------------------------------
# Las portadas embebidas — corrección 16
# ---------------------------------------------------------------------------


def test_las_portadas_vienen_dentro_del_correo():
    """Es la corrección 16: CU-ALT-NOV supone una descarga por URL, y acá no hay nada
    que descargar."""
    imagenes = leer_novedades().imagenes

    # Las tres portadas más el logo.
    assert len(imagenes) == 4
    assert all(imagen.tipo == "image/webp" for imagen in imagenes)
    assert all(imagen.bytes_ > 0 for imagen in imagenes)


def test_cada_imagen_queda_marcada_dentro_de_la_fila_de_su_producto():
    """Sin el marcador habría que correlacionar por orden, y el logo del
    encabezado corre todo un lugar."""
    filas = [linea for linea in leer_novedades().contenido.splitlines() if linea.startswith("|")]
    de_berserk_5 = next(fila for fila in filas if "| 9789878271583 |" in fila)

    assert "[imagen:tapa001@ivrea.test]" in de_berserk_5
    assert "[imagen:tapa002@ivrea.test]" not in de_berserk_5


def test_los_marcadores_coinciden_con_las_partes_del_correo():
    """Si no coincidieran, la resolución fallaría en silencio y el borrador
    quedaría con "Imagen pendiente" sin que nadie entienda por qué."""
    leido = leer_novedades()
    marcados = {
        linea.split("[imagen:")[1].split("]")[0]
        for linea in leido.contenido.splitlines()
        if "[imagen:" in linea and "]" in linea
    }

    assert marcados <= leido.cids


@pytest.mark.parametrize(
    "escrito",
    ["tapa001@ivrea.test", "<tapa001@ivrea.test>", "tapa001%40ivrea.test", " tapa001@ivrea.test "],
)
def test_el_identificador_se_compara_venga_como_venga(escrito):
    """El `src` del HTML puede venir codificado y la cabecera de la parte llega
    entre ángulos: sin normalizar los dos lados, el marcador nunca encontraría
    su imagen."""
    assert correos.normalizar_cid(escrito) == "tapa001@ivrea.test"


def test_un_correo_sin_imagenes_se_lee_igual():
    leido = leer_novedades(con_imagenes=False, con_logo=False)

    assert leido.imagenes == []
    assert "| 9789878271583 |" in leido.contenido


# ---------------------------------------------------------------------------
# Robustez
# ---------------------------------------------------------------------------


def test_un_html_mal_cerrado_no_pierde_la_ultima_fila():
    """Los correos mal formados llegan, y perder el último producto en silencio
    es peor que fallar."""
    html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td>"

    assert correos.extraer_contenido(html).splitlines() == ["| A | B |", "| C | D |"]


def test_un_cuerpo_vacio_no_rompe():
    assert correos.extraer_contenido("") == ""
    assert correos.extraer_contenido(None) == ""


def test_una_fecha_ilegible_no_tumba_la_lectura():
    """La fecha es un dato de presentación; el orden de la cola lo da cuándo lo
    recibimos nosotros."""
    crudo = ejemplo.correo_de_novedades().replace(b"\nDate: ", b"\nDate: no-es-una-fecha ", 1)

    assert correos.leer(crudo).fecha is None


def test_una_imagen_por_enlace_tambien_deja_rastro_en_la_fila():
    """Las dos formas conviven en la práctica. Una imagen externa no se puede
    resolver contra ninguna parte del correo, pero si no dejara rastro la celda
    quedaría vacía y correría todas las columnas de esa fila."""
    html = (
        "<table><tr>"
        "<td>9789878271583</td>"
        '<td><img src="https://ivrea.test/tapa.webp" alt="Tapa Berserk"></td>'
        "<td>$24900</td>"
        "</tr></table>"
    )

    assert correos.extraer_contenido(html) == (
        "| 9789878271583 | [imagen: Tapa Berserk] | $24900 |"
    )


def test_una_imagen_sin_origen_ni_descripcion_se_ignora():
    """Un espaciador de un pixel no es un dato: meterlo en la fila agregaría una
    columna que no existe."""
    html = '<table><tr><td>A</td><td><img width="1"></td><td>B</td></tr></table>'

    # La celda queda vacía pero **sigue estando**: perder la columna correría
    # todas las siguientes, que es exactamente lo que la fila con barras evita.
    assert correos.extraer_contenido(html) == "| A |  | B |"


def test_una_celda_sin_fila_no_pierde_su_texto():
    """HTML roto, pero el texto que traía se conserva igual."""
    assert correos.extraer_contenido("<td>Suelto</td>") == "Suelto"


def test_un_correo_solo_de_texto_plano_se_lee_igual():
    """Estos proveedores mandan HTML, pero un correo sin parte HTML no puede
    quedar sin contenido: se trata su texto como párrafos."""
    from email.message import EmailMessage

    mensaje = EmailMessage()
    mensaje["From"] = "novedades@ivrea.test"
    mensaje["Subject"] = "Aviso"
    mensaje["Message-ID"] = "<solo-texto@ivrea.test>"
    mensaje.set_content("Primera linea." + chr(10) * 2 + "Segunda linea.")

    leido = correos.leer(mensaje.as_bytes())

    assert "Primera linea." in leido.contenido
    assert "Segunda linea." in leido.contenido
