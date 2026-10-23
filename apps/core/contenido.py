"""El contenido de la tienda: FAQ, banners e identidad visual (módulo 17, tanda 2).

Cada operación audita con su acción propia (B-17-005). Las imágenes ya llegan
procesadas por `imagenes.procesar` (RNF-05): una imagen inválida se rechaza
antes de tocar nada, así que `CO-133` E1 —«no se registra ningún cambio,
tampoco el de posición»— se cumple por construcción.
"""

from django.db import transaction
from django.utils import timezone
from markdown_it import MarkdownIt

from apps.core import colores
from apps.core.models import Banner, ContenidoFAQ, IdentidadVisual, RegistroAuditoria

# C-16: CommonMark sin HTML crudo. Lo que el Administrador puede escribir en
# Markdown no cambia; lo que no pasa es una etiqueta `<script>` escrita a mano.
# Los enlaces con esquemas peligrosos (`javascript:`) los descarta el propio
# validador de la biblioteca.
_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")


def markdown_a_html(texto):
    return _MARKDOWN.render(texto or "")


# ---------------------------------------------------------------------------
# FAQ — CO-135, CO-136
# ---------------------------------------------------------------------------


def publicar_faq(contenido, *, actor, ip=None, confirma_vacia=False):
    """Reemplaza el contenido publicado. Devuelve `False` si quedó pendiente.

    Un contenido vacío no se publica sin confirmación explícita (A2): dejaría
    la sección en blanco para los clientes. Con la confirmación es `CO-136`.
    """
    contenido = (contenido or "").strip()
    if not contenido and not confirma_vacia:
        return False

    with transaction.atomic():
        faq = ContenidoFAQ.objects.select_for_update().get(pk=ContenidoFAQ.obtener().pk)
        anterior = len(faq.contenido)
        faq.contenido = contenido
        faq.actualizado_en = timezone.now()
        faq.save()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PUBLICACION_FAQ,
            actor=actor,
            objetivo=faq,
            ip=ip,
            detalle=(
                "Se publicó la FAQ vacía: la sección queda en blanco"
                if not contenido
                else f"Se publicó la FAQ: {anterior} → {len(contenido)} caracteres"
            ),
        )
    return True


# ---------------------------------------------------------------------------
# Banners — CO-132, CO-133, CO-134
# ---------------------------------------------------------------------------


def _galeria_bloqueada():
    """La galería entera bajo bloqueo: cualquier cambio reordena a todos."""
    return list(Banner.objects.select_for_update().order_by("posicion", "pk"))


def _reajustar(banners):
    """Posiciones consecutivas desde 0, en el orden de la lista."""
    for posicion, banner in enumerate(banners):
        if banner.posicion != posicion:
            banner.posicion = posicion
            banner.save(update_fields=["posicion"])


def agregar_banner(imagen_procesada, *, actor, ip=None):
    """`CO-132`: al final de la galería, publicado de inmediato."""
    with transaction.atomic():
        galeria = _galeria_bloqueada()
        banner = Banner.objects.create(imagen=imagen_procesada, posicion=len(galeria))
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_BANNER,
            actor=actor,
            objetivo=banner,
            ip=ip,
            detalle=f"Banner agregado en la posición {banner.numero}",
        )
    return banner


def editar_banner(banner, *, actor, ip=None, imagen_procesada=None, numero=None):
    """`CO-133`: reemplaza la imagen, cambia la posición, o ambas cosas.

    `numero` es la posición como la ve el Administrador, desde 1. La imagen
    reemplazada se borra del almacenamiento: no se conserva.
    """
    with transaction.atomic():
        galeria = _galeria_bloqueada()
        actual = next(b for b in galeria if b.pk == banner.pk)
        anterior = actual.numero
        cambios = []

        if imagen_procesada is not None:
            vieja = actual.imagen.name
            actual.imagen = imagen_procesada
            actual.save(update_fields=["imagen"])
            transaction.on_commit(lambda: actual.imagen.storage.delete(vieja))
            cambios.append("imagen reemplazada")

        if numero is not None and numero != anterior:
            galeria.remove(actual)
            galeria.insert(numero - 1, actual)
            _reajustar(galeria)
            cambios.append(f"posición: {anterior} → {numero}")

        if cambios:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.MODIFICACION_BANNER,
                actor=actor,
                objetivo=actual,
                ip=ip,
                detalle="; ".join(cambios),
            )
    return actual


def eliminar_banner(banner, *, actor, ip=None):
    """`CO-134`: se elimina y los demás conservan su orden relativo."""
    with transaction.atomic():
        galeria = _galeria_bloqueada()
        actual = next((b for b in galeria if b.pk == banner.pk), None)
        if actual is None:
            return False
        numero, archivo = actual.numero, actual.imagen.name
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BAJA_BANNER,
            actor=actor,
            ip=ip,
            detalle=f"Banner eliminado de la posición {numero}",
        )
        actual.delete()
        galeria.remove(actual)
        _reajustar(galeria)
        transaction.on_commit(lambda: Banner.imagen.field.storage.delete(archivo))
    return True


# ---------------------------------------------------------------------------
# Identidad visual — CO-131
# ---------------------------------------------------------------------------

CAMPOS_DE_IDENTIDAD = (
    ("nombre_tienda", "nombre de la tienda"),
    ("correo_contacto", "correo de contacto"),
    ("telefono", "teléfono"),
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("tiktok", "TikTok"),
    ("x_twitter", "X / Twitter"),
    ("color_primario", "color primario"),
    ("color_secundario", "color secundario"),
    ("color_acento", "color de acento"),
    ("tipo_fondo", "fondo"),
    ("color_fondo", "color de fondo"),
    *((rol.campo, f"color de {rol.nombre.lower()}") for rol in colores.ROLES),
    ("descripcion_tienda", "descripción de la tienda"),
    ("portada_antetitulo", "antetítulo de la portada"),
    ("portada_titulo", "título de la portada"),
    ("portada_bajada", "bajada de la portada"),
    ("ticker_mensajes", "mensajes del ticker"),
)


def actualizar_identidad(
    formulario,
    *,
    actor,
    ip=None,
    logo=None,
    imagen_fondo=None,
    imagen_acceso=None,
    quitar=(),
):
    """`CO-131`: aplica los cambios a la tienda de inmediato.

    Se audita con los campos modificados y sus valores anteriores. Las
    imágenes llegan ya procesadas; la que reemplazan se borra.
    """
    with transaction.atomic():
        guardada = IdentidadVisual.objects.select_for_update().get(pk=IdentidadVisual.obtener().pk)
        anteriores = {campo: getattr(guardada, campo) for campo, _ in CAMPOS_DE_IDENTIDAD}

        identidad = formulario.save(commit=False)
        cambios = [
            f"{etiqueta}: «{anteriores[campo]}» → «{getattr(identidad, campo)}»"
            for campo, etiqueta in CAMPOS_DE_IDENTIDAD
            if anteriores[campo] != getattr(identidad, campo)
        ]
        for campo, nueva, etiqueta in (
            ("logo", logo, "logo"),
            ("imagen_fondo", imagen_fondo, "imagen de fondo"),
            ("imagen_acceso", imagen_acceso, "imagen del ingreso"),
        ):
            vieja = getattr(guardada, campo).name
            if nueva is not None:
                setattr(identidad, campo, nueva)
                cambios.append(f"{etiqueta} reemplazado" if vieja else f"{etiqueta} cargado")
            elif campo in quitar and vieja:
                # Sin imagen, la tienda vuelve a su vista predeterminada (B-07-025).
                setattr(identidad, campo, "")
                cambios.append(f"{etiqueta} quitado")
            else:
                continue
            if vieja:
                transaction.on_commit(
                    lambda nombre=vieja: IdentidadVisual.logo.field.storage.delete(nombre)
                )

        identidad.actualizado_en = timezone.now()
        identidad.actualizado_por = actor
        identidad.save()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL,
            actor=actor,
            objetivo=identidad,
            ip=ip,
            detalle="; ".join(cambios) or "Se guardó sin cambios",
        )
    return identidad
