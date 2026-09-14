"""Reglas de negocio del alta en lote (CU-ALT-NAC y CU-ALT-IMP).

Están acá y no en las vistas porque las dos vistas —nacional e importado— hacen
lo mismo con datos distintos, y porque el alta tiene que poder probarse sin
levantar un request.
"""

from dataclasses import dataclass, field

from django.db import IntegrityError, transaction
from django.db.models.functions import Lower

from apps.catalog.models import (
    LoteAlta,
    ProductoEditorial,
    ProductoNoEditorial,
    TablaPrecioReferencia,
)
from apps.core.models import RegistroAuditoria


@dataclass
class ResultadoLote:
    """Lo que el CU pide informar en el resumen final (CU-ALT-NAC paso 9, CU-ALT-IMP paso 11)."""

    lote: LoteAlta
    creados: list = field(default_factory=list)
    rechazados: list = field(default_factory=list)

    @property
    def con_precio_manual(self):
        return [producto for producto in self.creados if producto.precio_manual]


def buscar_duplicado(titulo, volumen, tipo, formato, editorial, isbn="", excluir=None):
    """El producto que ya ocupa esa identidad, o `None`.

    Hay **dos criterios y uno manda sobre el otro**:

    1. **El ISBN, cuando el ítem lo declara.** Identifica una edición y nada
       más, así que si ya existe un producto con ese ISBN es el mismo producto,
       aunque le hayan escrito el título distinto —"Berserk Deluxe 5" contra
       "Berserk edición deluxe vol. 5"— o lo hayan cargado bajo otro formato.
       Es justamente el caso que la tupla no atrapa.
    2. **La tupla completa** —título + volumen + tipo + formato + editorial—
       para todo lo demás. Comparar solo el título rechazaría el tomo 2 de una
       serie cuyo tomo 1 ya está cargado; sacar el formato juntaría en un solo
       producto la edición B6 y la Deluxe del mismo tomo, que tienen precio y
       stock distintos.

    El orden importa: si el ISBN encuentra algo, no hace falta mirar la tupla.
    Al revés no vale, porque un producto viejo cargado sin ISBN puede ser el
    mismo tomo que uno nuevo que sí lo trae.

    El título se compara sin distinguir mayúsculas y sin espacios sobrantes,
    igual que la restricción de la base: quien carga "Batman " un martes y
    "batman" el jueves está cargando el mismo tomo dos veces.

    `excluir` es la clave del producto que se está editando (CU-CAT-EDI). Sin eso,
    guardar una ficha sin tocarle la identidad la haría chocar consigo misma y
    ningún producto se podría editar dos veces.
    """
    candidatos = ProductoEditorial.objects.all()
    if excluir is not None:
        candidatos = candidatos.exclude(pk=excluir)

    if isbn:
        por_isbn = candidatos.filter(isbn=isbn).first()
        if por_isbn:
            return por_isbn

    return (
        candidatos.annotate(titulo_normalizado=Lower("titulo"))
        .filter(
            titulo_normalizado=titulo.strip().lower(),
            volumen=volumen,
            tipo=tipo,
            formato=formato,
            editorial=editorial,
        )
        .first()
    )


def buscar_duplicado_no_editorial(titulo, tipo, excluir=None):
    """El artículo que ya ocupa ese nombre en esa categoría, o `None`.

    Es la clave que CU-CAT-ALT paso 6 declara. **Pero no bloquea el alta**, a
    diferencia de la del material editorial: el catálogo no editorial real tiene
    merch genérico, sin marca y no oficial, y dos llaveros de Naruto de
    proveedores distintos son dos productos. Ver la corrección 21 y el agregado
    A4. Lo que hace este resultado es alimentar una advertencia que el
    Administrador confirma.

    Compara sin distinguir mayúsculas y con los espacios internos colapsados,
    igual que el resto de los catálogos que se identifican por su nombre.

    `excluir` es la clave del producto que se está editando (CU-CAT-EDI): sin eso, un
    artículo chocaría consigo mismo apenas se abra y se guarde su ficha.
    """
    if not tipo:
        return None
    candidatos = ProductoNoEditorial.objects.all()
    if excluir is not None:
        candidatos = candidatos.exclude(pk=excluir)
    return (
        candidatos.annotate(titulo_normalizado=Lower("titulo"))
        .filter(titulo_normalizado=" ".join((titulo or "").split()).lower(), tipo=tipo)
        .first()
    )


def buscar_parecidos_no_editoriales(titulo, tipo=None, tope=5):
    """Artículos con un nombre parecido, para avisar **antes** de guardar.

    No es una segunda validación: es la mitad cómoda de la advertencia. Sin
    esto, el Administrador se entera de que estaba cargando algo repetido recién
    al apretar guardar, con el formulario entero escrito — que es exactamente el
    problema que la consulta de precio de referencia ya resuelve del otro lado
    del módulo.

    Busca en **todas** las categorías a propósito: que "Llavero Naruto" exista
    en Merchandising es información útil aunque se lo esté cargando en TCG, y
    puede ser justamente el aviso de que la categoría elegida es la equivocada.
    """
    titulo = " ".join((titulo or "").split())
    if len(titulo) < 2:
        return ProductoNoEditorial.objects.none()

    parecidos = ProductoNoEditorial.objects.filter(titulo__icontains=titulo)
    if tipo:
        # El choque exacto se informa aparte y con otro peso; acá van los demás.
        parecidos = parecidos.exclude(titulo__iexact=titulo, tipo=tipo)
    return parecidos.select_related("tipo")[:tope]


def precio_de_referencia(editorial, tipo, formato):
    """La fila de la tabla de precios para esa combinación, o `None`.

    Que no exista **no bloquea el alta**: el precio simplemente no se
    pre-completa y se carga a mano. La precondición del caso de uso exige que la
    tabla tenga *alguna* combinación cargada, no la de este ítem en particular.
    """
    if not (editorial and tipo and formato):
        return None
    return TablaPrecioReferencia.objects.filter(
        editorial=editorial, tipo=tipo, formato=formato
    ).first()


def _colision(datos, existente):
    """El detalle de un duplicado, tal como se guarda en el lote y se muestra."""
    return {
        "titulo": datos["titulo"],
        "volumen": datos["volumen"],
        "tipo": str(datos["tipo"]),
        "formato": str(datos["formato"]) if datos.get("formato") else "",
        "editorial": str(datos["editorial"]),
        "producto_existente": existente.pk if existente else None,
    }


def _detalle_de_auditoria(lote, resultado):
    """El texto de la entrada consolidada del lote.

    En importados incluye el CRE y el margen aplicados, que es lo que pide la
    postcondición de CU-ALT-IMP: el margen global cambia con el tiempo y sin esto no
    habría forma de reconstruir con qué números se fijaron estos precios.
    """
    partes = [
        f"lote {lote.get_origen_display().lower()} #{lote.pk}",
        f"{len(resultado.creados)} ítem(s) creado(s)",
        f"{len(resultado.rechazados)} rechazado(s) por duplicado",
    ]
    if lote.es_mixto:
        partes.append("cabecera mixta")
    else:
        cabecera = f"cabecera: {lote.editorial} / {lote.tipo}"
        if lote.formato_id:
            cabecera += f" / {lote.formato}"
        partes.append(cabecera)
    if lote.origen == LoteAlta.IMPORTADO:
        partes.append(f"CRE aplicado: {lote.cre}")
        partes.append(f"margen vigente: {lote.margen_aplicado}")
        if lote.tiene_conversion:
            partes.append(f"cotización: 1 {lote.moneda_origen} = ${lote.cotizacion}")
    manuales = resultado.con_precio_manual
    if manuales:
        partes.append(f"{len(manuales)} con precio fijado a mano")
    return "; ".join(partes)


def registrar_lote(*, lote, items, actor=None, ip=None):
    """Da de alta los ítems válidos de un lote y lo deja auditado.

    `lote` llega sin guardar, con la cabecera y —si es importado— el CRE y el
    margen ya calculados. `items` son diccionarios con los campos del producto
    ya resueltos: lo que la cabecera aporta ya vino mezclado desde el
    formulario, así que acá no hay que volver a preguntarse si el lote es mixto.

    **Sobre la atomicidad (RNF-06):** todo el bloque es una sola transacción,
    así un fallo técnico no deja medio lote cargado. Pero un duplicado *no* es
    un fallo: es una exclusión esperada (E1) que saltea ese ítem y deja seguir a
    los demás. Confundir las dos cosas haría que un tomo repetido tire abajo el
    alta entera de las novedades de la semana.
    """
    resultado = ResultadoLote(lote=lote)

    with transaction.atomic():
        lote.creado_por = actor
        lote.save()

        for datos in items:
            existente = buscar_duplicado(
                datos["titulo"],
                datos["volumen"],
                datos["tipo"],
                datos.get("formato"),
                datos["editorial"],
                datos.get("isbn", ""),
            )
            if existente is not None:
                resultado.rechazados.append(_colision(datos, existente))
                continue

            # Las etiquetas viajan aparte de los campos: son una relación de
            # muchos a muchos y no se pueden asignar hasta que el producto
            # exista. Se sacan del diccionario antes de crearlo.
            etiquetas = datos.pop("etiquetas", ())

            try:
                # Punto de guardado propio: si la restricción de la base rechaza
                # el ítem, se descarta solo ese insert y la transacción del lote
                # sigue viva. Sin esto, un `IntegrityError` deja la transacción
                # entera en estado de error y no se puede continuar.
                with transaction.atomic():
                    producto = ProductoEditorial.objects.create(lote=lote, **datos)
                    if etiquetas:
                        producto.etiquetas.set(etiquetas)
            except IntegrityError:
                # Carrera: entre la consulta de arriba y este insert, otra alta
                # creó el mismo producto. La restricción de la base es la que
                # realmente garantiza que no haya duplicados.
                #
                # **Pero solo se trata como duplicado si de verdad hay uno.**
                # Antes se asumía que todo `IntegrityError` era una colisión, y
                # eso escondió un fallo real: cuando un campo obligatorio nuevo
                # dejó de completarse, el alta empezó a informar "duplicado" en
                # vez de romper, y los productos dejaron de crearse en silencio.
                # Un error de integridad que no es una colisión es un defecto
                # nuestro y tiene que salir a la superficie.
                choque = buscar_duplicado(
                    datos["titulo"],
                    datos["volumen"],
                    datos["tipo"],
                    datos.get("formato"),
                    datos["editorial"],
                    datos.get("isbn", ""),
                )
                if choque is None:
                    raise
                resultado.rechazados.append(_colision(datos, choque))
                continue

            resultado.creados.append(producto)

        lote.rechazados = resultado.rechazados
        lote.save(update_fields=["rechazados"])

        # **Una sola** entrada por lote, no una por ítem (CU-ALT-NAC paso 8).
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL,
            actor=actor,
            objetivo=lote,
            ip=ip,
            detalle=_detalle_de_auditoria(lote, resultado),
        )

    return resultado


# ---------------------------------------------------------------------------
# CU-CAT-BAJ — el informe de impacto previo a la baja
# ---------------------------------------------------------------------------


@dataclass
class ImpactoDeBaja:
    """Lo que CU-CAT-BAJ tiene que informar antes de pedir la confirmacion.

    El CU enumera cuatro categorias, y **hoy ninguna de las cuatro se puede
    calcular**: pedidos activos, suscripciones de reposicion, ofertas vigentes y
    carritos de clientes pertenecen a Pedidos, Restock, Pricing y Tienda, que no
    existen todavia.

    Las cuatro se declaran igual y en `None`, no en cero, por el mismo criterio
    con el que la baja de proveedor no inventa la cifra que no puede calcular
    (CU-PRV-BAJ). Cero significaria "revise: no afecta a nadie", que es una afirmacion
    sobre datos que el propio CU considera parte de la decision.

    Dejar las cuatro declaradas tiene una consecuencia practica: cuando aparezca
    cada modulo, sumar su cifra es llenar un hueco y no rediseniar la pantalla.

    `stock` y `estado` no son categorias del CU. Van igual porque son lo unico
    verificable en la pantalla, y sin ellos la decision se tomaria sin ningun
    dato del producto.
    """

    stock: int
    estado: str
    pedidos_activos: int | None = None
    suscripciones_de_reposicion: int | None = None
    ofertas_vigentes: int | None = None
    carritos_con_el_producto: int | None = None

    # Las cuatro categorias del CU, en el orden en que las enumera, con el
    # nombre que la pantalla muestra. Vive aca y no en la plantilla para que
    # agregar una cifra sea tocar un solo lugar.
    CATEGORIAS = (  # noqa: RUF012
        ("pedidos_activos", "Pedidos activos que lo incluyen"),
        ("suscripciones_de_reposicion", "Suscripciones de reposición"),
        ("ofertas_vigentes", "Ofertas vigentes"),
        ("carritos_con_el_producto", "Carritos de clientes"),
    )

    @property
    def categorias(self):
        """`[(etiqueta, valor)]` para la pantalla. `None` se dibuja distinto."""
        return [(etiqueta, getattr(self, campo)) for campo, etiqueta in self.CATEGORIAS]

    @property
    def todo_sin_determinar(self):
        """Ninguna categoria se pudo calcular. Es el estado de hoy."""
        return all(valor is None for _, valor in self.categorias)


def calcular_impacto_de_baja(producto):
    """El mapeo de impacto que CU-CAT-BAJ exige antes de la confirmacion."""
    return ImpactoDeBaja(stock=producto.stock, estado=producto.get_estado_display())
