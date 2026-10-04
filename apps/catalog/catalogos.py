"""Los catálogos de clasificación: alta, modificación, baja con informe y consulta.

Editoriales, tipos y formatos (módulo 17) y grupos y etiquetas (módulo 02)
recorren el mismo ciclo, que sus contratos declaran casi palabra por palabra:

- **El alta** (`CO-137`, `CO-141`, `CO-144`, `CO-038`, `CO-042`) nace activa.
- **La modificación** (`CO-138`, `CO-142`, `CO-145`, `CO-039`, `CO-043`)
  corrige y reactiva, pero **no da de baja**: la baja informa antes su impacto.
- **La baja es un par.** Primero se informa qué referencia al registro
  (`CO-139`, `CO-220`, `CO-147`, `CO-040`, `CO-044`), y sólo después se confirma
  (`CO-140`, `CO-221`, `CO-148`, `CO-041`, `CO-045`). La baja nunca toca lo que ya
  usa el registro: lo retira de los formularios.

Por eso el ciclo se escribe una sola vez (R-17-002). Lo que cambia de un
catálogo a otro —qué cuenta el informe, qué más alcanza la baja— lo declara
cada `Catalogo` de abajo, y nada más.
"""

from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    Oferta,
    Producto,
    Tipo,
)
from apps.core.models import RegistroAuditoria


@dataclass(frozen=True)
class Referencia:
    """Una de las cantidades del informe de baja. `None` es «No disponible»."""

    etiqueta: str
    cantidad: int | None

    @property
    def disponible(self):
        return self.cantidad is not None


class Catalogo:
    """Lo que distingue a un catálogo de los otros cuatro.

    Las subclases declaran el modelo, cómo se nombra y qué cuenta su informe.
    El resto —auditar, releer bajo bloqueo, no dar de baja dos veces— es igual
    para todos y vive en las funciones de este módulo.
    """

    clave = ""
    modelo = None
    campo_estado = "activo"
    singular = ""
    plural = ""
    # «la editorial», «el tipo»: los mensajes concuerdan en género.
    articulo = "el"
    # Los adjetivos del estado concuerdan igual: «Activa», «Inactivo».
    activo_texto = "Activo"
    inactivo_texto = "Inactivo"

    def esta_activo(self, objeto):
        return getattr(objeto, self.campo_estado)

    def informe(self, objeto):
        raise NotImplementedError

    def al_dar_de_baja(self, objeto):
        """Lo que la baja alcanza además del propio registro. Casi siempre nada."""

    def descripcion(self, objeto):
        return f"{self.singular.capitalize()} «{objeto}»"

    def listado(self):
        return self.modelo.objects.all()

    # -- Rutas ----------------------------------------------------------------

    def url_lista(self, objeto=None):
        return reverse(f"catalog:{self.clave}_lista")

    def url_editar(self, objeto):
        return reverse(f"catalog:{self.clave}_editar", args=[objeto.pk])

    def url_baja(self, objeto):
        return reverse(f"catalog:{self.clave}_baja", args=[objeto.pk])

    def url_alta(self):
        return reverse(f"catalog:{self.clave}_crear")


class CatalogoEditoriales(Catalogo):
    clave = "editorial"
    modelo = Editorial
    campo_estado = "activa"
    singular = "editorial"
    plural = "editoriales"
    articulo = "la"
    activo_texto = "Activa"
    inactivo_texto = "Inactiva"

    def informe(self, editorial):
        """`CO-139`: productos, filas de precio y proveedores."""
        return [
            Referencia("Productos", editorial.productos.count()),
            Referencia("Filas de la tabla de precios", editorial.precios_de_referencia.count()),
            Referencia("Proveedores", editorial.proveedores.count()),
        ]

    def listado(self):
        return Editorial.objects.annotate(cantidad_productos=Count("productos", distinct=True))


class CatalogoTipos(Catalogo):
    clave = "tipo"
    modelo = Tipo
    singular = "tipo de material"
    plural = "tipos de material"

    def informe(self, tipo):
        """`CO-220`: productos, filas de precio, proveedores y ofertas vigentes."""
        return [
            Referencia("Productos", tipo.productos.count()),
            Referencia("Filas de la tabla de precios", tipo.precios_de_referencia.count()),
            Referencia("Proveedores", tipo.proveedores.count()),
            # Las que referencian el tipo como alcance, vivas según sus fechas (R-17-003).
            Referencia(
                "Ofertas programadas o activas",
                Oferta.objects.vivas(timezone.localdate()).filter(tipo=tipo).count(),
            ),
        ]

    def listado(self):
        return Tipo.objects.annotate(
            cantidad_productos=Count("productos", distinct=True)
        ).prefetch_related("formatos")


class CatalogoFormatos(Catalogo):
    clave = "formato"
    modelo = Formato
    singular = "formato"
    plural = "formatos"

    def informe(self, formato):
        """`CO-147`: productos, filas de precio y tipos declarados."""
        return [
            Referencia("Productos", formato.productos.count()),
            Referencia("Filas de la tabla de precios", formato.precios_de_referencia.count()),
            Referencia("Tipos declarados", formato.tipos.count()),
        ]

    def listado(self):
        return Formato.objects.annotate(
            cantidad_productos=Count("productos", distinct=True)
        ).prefetch_related("tipos")


class CatalogoGrupos(Catalogo):
    clave = "grupo_etiqueta"
    modelo = GrupoEtiqueta
    singular = "grupo de etiquetas"
    plural = "grupos de etiquetas"

    def informe(self, grupo):
        """`CO-040`: las etiquetas del grupo y los productos que tienen alguna."""
        return [
            Referencia("Etiquetas", grupo.etiquetas.count()),
            Referencia(
                "Productos con alguna de sus etiquetas",
                Producto.objects.filter(etiquetas__grupo=grupo).distinct().count(),
            ),
        ]

    def al_dar_de_baja(self, grupo):
        """`CO-041`: la baja del grupo alcanza a cada una de sus etiquetas.

        Un solo `update()` y no un recorrido: un grupo puede tener cientos. Por
        eso mismo la reactivación del grupo no las reactiva (`CO-039`): ya no se
        distingue cuáles bajó el grupo y cuáles estaban dadas de baja antes.
        """
        grupo.etiquetas.update(activa=False)

    def listado(self):
        return GrupoEtiqueta.objects.annotate(cantidad_etiquetas=Count("etiquetas"))

    def url_lista(self, objeto=None):
        return reverse("catalog:etiquetas")


class CatalogoEtiquetas(Catalogo):
    clave = "etiqueta"
    modelo = Etiqueta
    campo_estado = "activa"
    singular = "etiqueta"
    plural = "etiquetas"
    articulo = "la"
    activo_texto = "Activa"
    inactivo_texto = "Inactiva"

    def informe(self, etiqueta):
        """`CO-044`: a cuántos productos alcanza."""
        return [Referencia("Productos", etiqueta.productos.count())]

    def descripcion(self, etiqueta):
        return f"Etiqueta «{etiqueta.nombre}» del grupo «{etiqueta.grupo}»"

    def url_lista(self, objeto=None):
        # Las etiquetas se listan por grupo (`CO-165`): se vuelve al grupo de
        # la etiqueta cuando se la conoce.
        if objeto is not None:
            return reverse("catalog:grupo_etiquetas", args=[objeto.grupo_id])
        return reverse("catalog:etiquetas")


EDITORIALES = CatalogoEditoriales()
TIPOS = CatalogoTipos()
FORMATOS = CatalogoFormatos()
GRUPOS = CatalogoGrupos()
ETIQUETAS = CatalogoEtiquetas()


# ---------------------------------------------------------------------------
# Las operaciones
# ---------------------------------------------------------------------------


def _si_no(valor):
    return "sí" if valor else "no"


def _texto(valor):
    """Un valor tal como se lee en el detalle de la auditoría."""
    if isinstance(valor, bool):
        return _si_no(valor)
    if valor in (None, ""):
        return "—"
    return f"«{valor}»"


def registrar(formulario, *, catalogo, actor, ip=None, campos_auditados=(), relaciones=()):
    """El alta: guarda lo que el formulario ya validó y la audita.

    Nace activo por la propia definición del modelo; el formulario de alta no
    ofrece el estado, así que no hay forma de crearlo dado de baja.
    """
    with transaction.atomic():
        objeto = formulario.save()
        valores = [
            f"{etiqueta}: {_texto(_valor(objeto, campo))}" for campo, etiqueta in campos_auditados
        ]
        valores += [f"{etiqueta}: {_nombres(objeto, campo)}" for campo, etiqueta in relaciones]
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_CATALOGO,
            actor=actor,
            objetivo=objeto,
            ip=ip,
            detalle="; ".join(
                [f"{catalogo.descripcion(objeto)}, {catalogo.activo_texto.lower()}", *valores]
            ),
        )
    return objeto


def _valor(objeto, ruta):
    """El valor de un campo, siguiendo relaciones escritas como `grupo__nombre`."""
    for paso in ruta.split("__"):
        objeto = getattr(objeto, paso, None)
    return objeto


def _nombres(objeto, relacion):
    """Los elementos de una relación de muchos a muchos, como texto ordenado."""
    if not objeto.pk:
        return "—"
    return ", ".join(sorted(str(elemento) for elemento in getattr(objeto, relacion).all())) or "—"


def cambios(anteriores, posteriores, campos, *, como_esta=False):
    """Los pares «campo: anterior → nuevo» de lo que efectivamente cambió.

    `como_esta` deja el valor sin comillas: las listas de una relación ya
    vienen escritas como se leen.
    """
    formato = (lambda valor: valor) if como_esta else _texto
    return [
        f"{etiqueta}: {formato(anteriores[campo])} → {formato(posteriores[campo])}"
        for campo, etiqueta in campos
        if anteriores[campo] != posteriores[campo]
    ]


def editar(formulario, *, catalogo, actor, ip=None, campos_auditados=(), relaciones=()):
    """La modificación: corrige, y reactiva si se pidió. Nunca da de baja.

    Se audita con los valores anterior y nuevo de lo que cambió. Una
    modificación sin cambios no deja entrada: no ocurrió nada que registrar.

    `campos_auditados` son pares de ruta y etiqueta (`("grupo__nombre",
    "grupo")`); `relaciones`, los muchos a muchos que guarda el formulario.
    """
    objeto = formulario.instance
    campos = [*campos_auditados, (catalogo.campo_estado, "activo")]
    # `ModelForm.is_valid()` ya volcó los datos sobre la instancia: los
    # anteriores se leen de la base, que es lo único que todavía los tiene.
    guardado = type(objeto).objects.get(pk=objeto.pk)
    anteriores = {campo: _valor(guardado, campo) for campo, _ in campos}
    anteriores.update({campo: _nombres(guardado, campo) for campo, _ in relaciones})

    with transaction.atomic():
        objeto = formulario.save(commit=False)
        if formulario.cleaned_data.get("reactivar"):
            setattr(objeto, catalogo.campo_estado, True)
        objeto.save()
        formulario.save_m2m()

        posteriores = {campo: _valor(objeto, campo) for campo, _ in campos}
        posteriores.update({campo: _nombres(objeto, campo) for campo, _ in relaciones})
        diferencias = cambios(anteriores, posteriores, campos) + cambios(
            anteriores, posteriores, relaciones, como_esta=True
        )
        if diferencias:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.MODIFICACION_CATALOGO,
                actor=actor,
                objetivo=objeto,
                ip=ip,
                detalle=f"{catalogo.descripcion(objeto)}: " + "; ".join(diferencias),
            )
    return objeto


def declarar_formatos(tipo, formatos, *, actor, ip=None):
    """`CO-146`: qué formatos se ofrecen en un tipo que se clasifica por formato.

    Es una operación propia y se audita aparte del alta o de la modificación
    del tipo, aunque la pantalla las envíe juntas. Los formatos que aplican a
    todos los tipos no se declaran tipo por tipo (T3), así que no se tocan.
    """
    anteriores = _nombres(tipo, "formatos")
    with transaction.atomic():
        universales = list(tipo.formatos.filter(aplica_a_todos=True))
        tipo.formatos.set([*formatos, *universales])
        posteriores = _nombres(tipo, "formatos")
        if anteriores != posteriores:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.MODIFICACION_CATALOGO,
                actor=actor,
                objetivo=tipo,
                ip=ip,
                detalle=(
                    f"{TIPOS.descripcion(tipo)}: formatos declarados: "
                    f"{anteriores} → {posteriores}"
                ),
            )


def confirmar_baja(objeto, *, catalogo, actor, ip=None):
    """La confirmación de la baja. Devuelve `False` si ya estaba dado de baja.

    Se relee bajo bloqueo y se vuelve a mirar el estado **adentro** de la
    transacción: dos administradores que confirman la misma baja a la vez no
    dejan dos entradas de auditoría, y una baja que llega después de que otro
    la reactivara no se aplica sobre un informe viejo sin que nadie lo vea.
    """
    with transaction.atomic():
        actual = type(objeto).objects.select_for_update().get(pk=objeto.pk)
        if not catalogo.esta_activo(actual):
            return False

        informe = catalogo.informe(actual)
        setattr(actual, catalogo.campo_estado, False)
        actual.save(update_fields=[catalogo.campo_estado])
        catalogo.al_dar_de_baja(actual)

        conservadas = ", ".join(
            f"{referencia.etiqueta.lower()}: "
            f"{referencia.cantidad if referencia.disponible else 'no disponible'}"
            for referencia in informe
        )
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BAJA_CATALOGO,
            actor=actor,
            objetivo=actual,
            ip=ip,
            detalle=f"{catalogo.descripcion(actual)}; se conservan {conservadas}",
        )
    return True
