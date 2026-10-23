"""Los controles de formulario del modo operativo están todos vestidos.

Este archivo existe por un error concreto: la cáscara del backoffice estilaba
`input[type="text"]`, `email` y `password`, y nada más. El día que una pantalla
usó un número, una fecha y un área de texto, los tres salieron sin el estilo
del resto y el problema se descubrió mirando la pantalla, no corriendo la
batería. Con el estilo preliminar los controles viven en `static/css/longbox.css`.

La regla que se prueba acá es la que evita que vuelva a pasar: **todo tipo de
control que alguna pantalla operativa dibuje tiene que estar cubierto**. No
alcanza con acordarse; tiene que fallar el test.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from apps.catalog.tests.factories import EditorialFactory

RUTA_HOJA = Path(settings.BASE_DIR) / "static" / "css" / "longbox.css"

# Tipos que no se visten con las reglas generales: la casilla y la opción usan
# el control nativo con `accent-color`, y los ocultos y los botones no se ven.
TIPOS_CON_TRATAMIENTO_PROPIO = {"hidden", "submit", "button", "reset", "checkbox", "radio"}

# Pantallas operativas representativas: entre las tres aparecen todos los tipos
# de control que el backoffice usa hoy.
PANTALLAS = ["catalog:lote_nacional", "catalog:lote_importado", "accounts:usuario_alta"]


def tipos_cubiertos():
    """Los `input[type="…"]` que la hoja de estilo viste, leídos del propio archivo."""
    hoja = RUTA_HOJA.read_text(encoding="utf-8")
    return set(re.findall(r'input\[type="([a-z-]+)"\]', hoja))


def tipos_en(html):
    """Los `type` de los `<input>` que una pantalla dibuja de verdad."""
    return {
        tipo
        for etiqueta in re.findall(r"<input\b[^>]*>", html)
        for tipo in re.findall(r'type="([a-z-]+)"', etiqueta)
    }


def test_la_hoja_de_estilo_cubre_algo():
    """Si la lectura del archivo dejara de encontrar selectores, el test de
    abajo pasaría solo y no probaría nada."""
    assert len(tipos_cubiertos()) >= 5


@pytest.mark.django_db
@pytest.mark.parametrize("pantalla", PANTALLAS)
def test_ninguna_pantalla_operativa_dibuja_un_control_sin_estilo(client_admin, pantalla):
    EditorialFactory()

    html = client_admin.get(reverse(pantalla)).content.decode()

    sin_vestir = tipos_en(html) - tipos_cubiertos() - TIPOS_CON_TRATAMIENTO_PROPIO
    assert (
        not sin_vestir
    ), f"La pantalla {pantalla} dibuja controles que la hoja de estilo no viste: {sin_vestir}."


@pytest.mark.django_db
def test_la_pantalla_de_alta_usa_los_tipos_que_habian_quedado_sin_estilo(client_admin):
    """El caso que originó el problema: número, fecha y área de texto.

    Si alguna vez dejaran de aparecer en esta pantalla, el test de arriba
    seguiría en verde sin estar mirando nada.
    """
    EditorialFactory()

    html = client_admin.get(reverse("catalog:lote_importado")).content.decode()

    assert {"number", "date"} <= tipos_en(html)
    assert "<textarea" in html


@pytest.mark.django_db
def test_el_area_de_texto_tambien_esta_cubierta(client_admin):
    hoja = RUTA_HOJA.read_text(encoding="utf-8")

    assert "textarea" in hoja


@pytest.mark.django_db
@pytest.mark.parametrize("pantalla", PANTALLAS)
def test_las_pantallas_operativas_traen_los_componentes_propios(client_admin, pantalla):
    """La vista previa de la imagen elegida se arma con JavaScript y se conserva.

    El desplegable propio, en cambio, se retiró: vuelve el `<select>` nativo
    (`identidad_visual.md`, «Qué se retira»).
    """
    EditorialFactory()

    html = client_admin.get(reverse(pantalla)).content.decode()

    assert "function mejorarArchivos" in html
    assert "mejorarSelects" not in html


@pytest.mark.django_db
def test_los_campos_obligatorios_se_marcan_solos(client_admin):
    """El asterisco sale de `field.required`, no de un dato escrito a mano."""
    EditorialFactory()

    html = client_admin.get(reverse("catalog:lote_importado")).content.decode()

    assert 'class="obligatorio"' in html


# ---------------------------------------------------------------------------
# Los controles compuestos: que la pantalla dibuje el control **real**
#
# Estos tres salieron de un error del mismo tipo que el de arriba, pero peor:
# `_archivo.html` es solo el guion que mejora los `input[type=file]`, y tres
# pantallas lo incluian pasandole `campo=form.portada` creyendo que dibujaba el
# campo. No dibujaba nada, y la portada no se podia subir en ninguna de las tres.
#
# La bateria no lo atrapo porque verificaba `portada_pendiente`, que es
# exactamente lo que queda cuando no se sube ningun archivo.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_las_pantallas_de_producto_dibujan_el_campo_de_portada(client_admin):
    from apps.catalog.tests.factories import ProductoFactory

    producto = ProductoFactory()
    pantallas = [
        reverse("catalog:producto_no_editorial_alta"),
        reverse("catalog:producto_editar", args=[producto.pk]),
    ]

    for url in pantallas:
        contenido = client_admin.get(url).content.decode()
        assert 'type="file"' in contenido, url


@pytest.mark.django_db
def test_el_selector_de_etiquetas_dibuja_el_select_real(client_admin):
    """Lo que viaja en el POST es el `<select multiple>`: el buscador con fichas
    se arma encima. Sin el control real, el campo no envia nada."""
    contenido = client_admin.get(reverse("catalog:producto_no_editorial_alta")).content.decode()

    assert "data-selector-etiquetas" in contenido
    assert 'name="etiquetas"' in contenido
    assert "multiple" in contenido


@pytest.mark.django_db
def test_el_selector_de_etiquetas_trae_las_etiquetas_como_opciones(client_admin):
    """El `<select>` salía vacío en el alta no editorial y en las dos ediciones:
    el formulario le cambiaba el widget **después** de asignarle el queryset, y
    el widget nuevo quedaba sin opciones. El selector decía «Ya están todas
    elegidas» y no había forma de asignar ninguna etiqueta."""
    from apps.catalog.tests.factories import (
        EtiquetaFactory,
        ProductoFactory,
        ProductoNoEditorialFactory,
    )

    etiqueta = EtiquetaFactory(nombre="Marvel")
    pantallas = [
        reverse("catalog:producto_no_editorial_alta"),
        reverse("catalog:producto_editar", args=[ProductoFactory().pk]),
        reverse("catalog:producto_editar", args=[ProductoNoEditorialFactory().pk]),
    ]

    for url in pantallas:
        contenido = client_admin.get(url).content.decode()
        select = re.search(r'<select name="etiquetas"[^>]*>(.*?)</select>', contenido, re.S)
        assert select, url
        assert f'value="{etiqueta.pk}"' in select.group(1), url


@pytest.mark.django_db
def test_los_desplegables_son_nativos_y_el_propio_solo_falta_base_select(client_admin):
    """B-00-011: el formulario dibuja el `<select>` nativo, que es el que envía el
    valor y el que leen los guiones. La lista propia la arma un guion aparte, y
    sólo donde el navegador no tiene `appearance: base-select`."""
    EditorialFactory()

    html = client_admin.get(reverse("catalog:lote_nacional")).content.decode()
    guion = (settings.BASE_DIR / "static" / "js" / "desplegable.js").read_text(encoding="utf-8")

    assert "<select" in html
    assert "data-desplegable" not in html
    assert "js/desplegable.js" in html
    assert 'CSS.supports("appearance", "base-select")' in guion


# ---------------------------------------------------------------------------
# La jerarquia de botones
#
# La jerarquía de cuatro niveles es una regla de uso y sigue vigente con el
# estilo preliminar (`identidad_visual.md`, Botones). Son dos limites, no un
# gusto: **el primario es uno por pantalla** y **el nivel 3 vive solo en filas**.
# ---------------------------------------------------------------------------


# Pantallas con dos caminos de igual peso, que llevan los dos en el nivel 1.
# El invitado elige entre iniciar sesión y comprar como invitado (CU-TDA-INV paso 1).
DOS_CAMINOS = {"_decision_de_correo.html", "producto_lista.html", "_carrito.html"}

# La vista previa de la identidad visual dibuja el botón principal de la tienda
# como muestra de color (plan 00 de interfaz, cuarta parte, B): no es una acción.
MUESTRAS = {"identidad_visual.html"}

# Las plantillas que dibujan filas: son las unicas donde una acción de nivel 3
# se lee como "esta fila tiene acciones" y no como ruido.
CON_FILAS = {
    "_tabla_usuarios.html",
    "_tabla_proveedores.html",
    "_tabla_borradores.html",
    "precio_lista.html",
    "lote_formulario.html",
    "lote_resumen.html",
    "_estado_y_acciones.html",
    "etiqueta_lista.html",
    "auditoria_lista.html",
    "banner_lista.html",
    # Cada línea del carrito actualiza su cantidad (CU-TDA-CRM); sin guion, con
    # «Actualizar». Las líneas viven en el parcial desde B-07-028.
    "_carrito.html",
    # Cada línea del checkout se cubre con puntos o vuelve a pagarse (CO-103, CO-104).
    "checkout.html",
    # El mostrador: agregar cada coincidencia y canjear cada ítem del ticket (CU-VTA-REG).
    "mostrador.html",
    # Cada ítem de la propuesta de restock se guarda o se quita (plan 00 de interfaz).
    "propuesta.html",
}


def plantillas_operativas():
    """Las del backoffice, sin los parciales que definen los componentes."""
    raiz = Path(settings.BASE_DIR)
    rutas = list(raiz.glob("apps/*/templates/*/*.html")) + list(raiz.glob("templates/*.html"))
    return [ruta for ruta in rutas if ruta.name != "base_publico.html"]


def test_los_cuatro_niveles_estan_definidos():
    hoja = RUTA_HOJA.read_text(encoding="utf-8")

    for clase in (".boton-primario", ".boton-seccion", ".boton-menor", ".boton-texto"):
        assert clase in hoja, clase


def test_el_nivel_3_vive_solo_donde_hay_filas():
    """Su presencia comunica algo concreto. Repartido por toda la pantalla deja
    de comunicarlo y solo carga el diseno."""
    fuera_de_lugar = [
        ruta.name
        for ruta in plantillas_operativas()
        if "boton-menor" in ruta.read_text(encoding="utf-8") and ruta.name not in CON_FILAS
    ]

    assert fuera_de_lugar == []


# Plan 00 de interfaz, apartado 3: enviar es una acción. Salir de la sesión es
# navegación aunque viaje por POST, y la lista de acciones de la ficha de usuario
# dibuja todas sus acciones con el mismo nivel, enlaces y envíos.
ENVIO_COMO_NAVEGACION = {"usuario_ficha.html"}


def test_un_envio_no_se_dibuja_como_navegacion():
    hallazgos = []
    publico = Path(settings.BASE_DIR) / "templates" / "base_publico.html"
    for ruta in [*plantillas_operativas(), publico]:
        if ruta.name in ENVIO_COMO_NAVEGACION:
            continue
        for form in re.findall(r"<form\b.*?</form>", ruta.read_text(encoding="utf-8"), flags=re.S):
            # Salir de la sesión, y el «Cancelar» que cierra un `<dialog>`.
            if "accounts:logout" in form or 'method="dialog"' in form:
                continue
            for boton in re.findall(r"<button\b[^>]*>", form):
                if 'type="button"' not in boton and re.search(r'class="[^"]*boton-texto', boton):
                    hallazgos.append(f"{ruta.name}: {boton}")
    assert hallazgos == []


def test_ninguna_pantalla_repite_el_boton_principal():
    """Uno por pantalla. La excepcion son los dos caminos de igual peso: van los
    dos en el nivel 1 y los distingue el texto. Se cuentan por separado las
    ramas excluyentes de un `{% if %}`, que nunca se dibujan juntas."""
    repetidas = {}
    for ruta in plantillas_operativas():
        contenido = re.sub(
            r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}",
            "",
            ruta.read_text(encoding="utf-8"),
            flags=re.S,
        )
        ramas = re.split(r"\{%\s*(?:else|elif[^%]*)\s*%\}", contenido)
        mayor = max(rama.count('class="boton-primario') for rama in ramas)
        if mayor > 1 and ruta.name not in DOS_CAMINOS | MUESTRAS:
            repetidas[ruta.name] = mayor

    assert repetidas == {}


def test_el_boton_de_texto_no_lleva_copia_y_antepone_la_flecha_al_volver():
    """La copia en `data-texto` sólo servía para el barrido de color, que se
    retiró. Con `atras`, la etiqueta va precedida por «←»."""
    parcial = (Path(settings.BASE_DIR) / "templates" / "_boton_texto.html").read_text(
        encoding="utf-8"
    )

    assert "data-texto=" not in parcial
    assert '{% if atras %}<span aria-hidden="true">←</span>' in parcial


# Clases que no llevan estilo propio: ganchos de los guiones o de las pruebas.
GANCHOS_SIN_ESTILO = {
    "barra-envio",  # el guion del carrito la reemplaza al cambiar la cantidad
    "cifra-derivada",  # el guion del alta de lotes escribe ahí el valor calculado
    "linea-carrito__datos",  # columna de la línea: la reparte la grilla del padre
    "cuenta__principal",  # columna de «Mi cuenta»: la reparte la grilla del padre
}


def test_ninguna_plantilla_usa_una_clase_que_la_hoja_no_define():
    """`pila-4` se usó en 17 plantillas sin existir, y esas pantallas quedaron con
    los elementos pegados (plan 00 de interfaz). Una clase sin definir no falla:
    simplemente no dibuja nada."""
    raiz = Path(settings.BASE_DIR)
    hojas = [raiz / "static/css/longbox.css", raiz / "static/css/tokens.css"]
    hojas.append(raiz / "apps/core/templates/core/tienda.css")
    definidas = set(
        re.findall(r"\.([a-zA-Z][\w-]*)", "".join(h.read_text(encoding="utf-8") for h in hojas))
    )
    faltan = {}
    plantillas = [*raiz.glob("templates/**/*.html"), *raiz.glob("apps/*/templates/**/*.html")]
    for ruta in plantillas:
        if "correo" in ruta.parts:
            continue
        texto = re.sub(
            r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}",
            "",
            ruta.read_text(encoding="utf-8"),
            flags=re.S,
        )
        texto = re.sub(r"\{%.*?%\}|\{\{.*?\}\}", " ", texto)
        for valor in re.findall(r'class="([^"]*)"', texto):
            for clase in valor.split():
                if (
                    re.fullmatch(r"[a-z][\w-]*", clase)
                    and clase not in definidas | GANCHOS_SIN_ESTILO
                ):
                    faltan.setdefault(clase, ruta.name)
    assert faltan == {}
