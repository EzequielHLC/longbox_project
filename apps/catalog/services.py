"""Reglas de negocio del alta en lote (CU-ALT-NAC y CU-ALT-IMP).

Están acá y no en las vistas porque las dos vistas —nacional e importado— hacen
lo mismo con datos distintos, y porque el alta tiene que poder probarse sin
levantar un request.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from django.utils import timezone

from apps.catalog.models import (
    BorradorProducto,
    Etiqueta,
    LoteAlta,
    Producto,
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


def titulo_comparable(texto):
    """Sin mayúsculas, tildes ni espacios de más: «Frieren: Más Allá» es «frieren: mas alla»."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "")
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())


_SIN_LETRAS = re.compile(r"[^0-9a-z]+")
# La vocal larga japonesa se escribe de cuatro maneras: «Tankōbon» (que la
# normalización ya deja en «tankobon»), «Tankoubon», «Tankoobon», «Tankohbon».
_VOCAL_LARGA = re.compile(r"(?<=[a-z])(ou|oo|oh|uu)(?![aeiou])")


def nombre_comparable(texto):
    """Un nombre de catálogo —formato, tipo, editorial— listo para compararlo con lo
    que escribió una persona o copió el modelo (B-01-023).

    Encima de `titulo_comparable` saca lo que no es letra ni número («Tapa-dura» es
    «tapa dura», «B 6» es «B6») y junta las formas de escribir la vocal larga:
    «Tankōbon», «Tankobon» y «Tankoubon» son el mismo formato. Sólo para nombres
    de catálogo, que son pocos y cortos: un título se compara con `titulo_comparable`.
    """
    base = _VOCAL_LARGA.sub(lambda vocal: vocal.group(1)[0], titulo_comparable(texto))
    return _SIN_LETRAS.sub("", base)


def por_nombre(objetos, texto):
    """El de `objetos` cuyo `nombre` es `texto` según `nombre_comparable`, o `None`."""
    buscado = nombre_comparable(texto)
    if not buscado:
        return None
    return next((objeto for objeto in objetos if nombre_comparable(objeto.nombre) == buscado), None)


@dataclass
class Serie:
    """Lo que el catálogo ya sabe de una serie, para no volver a cargarlo (B-01-020)."""

    ultimo: object
    tomos: int
    autor: str = ""
    sinopsis: str = ""
    solo_adultos: bool = False
    etiquetas: list = field(default_factory=list)

    @property
    def tipo(self):
        return self.ultimo.tipo

    @property
    def formato(self):
        return self.ultimo.formato


def serie_de(titulo, editorial):
    """Los tomos que ya hay de esa serie en esa editorial, o `None`.

    La serie es el mismo título en la misma editorial, comparado sin mayúsculas
    ni tildes. El tipo y el formato son los del último tomo; el autor y la
    sinopsis, los del último que los tenga; «sólo adultos», si alguno lo es.
    """
    buscado = titulo_comparable(titulo)
    if not buscado or editorial is None:
        return None
    tomos = [
        producto
        for producto in ProductoEditorial.objects.filter(editorial=editorial)
        .select_related("tipo", "formato")
        .order_by("-volumen", "-pk")
        if titulo_comparable(producto.titulo) == buscado
    ]
    if not tomos:
        return None
    return Serie(
        ultimo=tomos[0],
        tomos=len(tomos),
        autor=next((p.autor for p in tomos if p.autor), ""),
        sinopsis=next((p.descripcion for p in tomos if p.descripcion), ""),
        solo_adultos=any(p.solo_adultos for p in tomos),
        # Las activas de cualquiera de sus tomos: describen la serie, no el tomo.
        etiquetas=list(
            Etiqueta.objects.filter(productos__in=tomos, activa=True)
            .select_related("grupo")
            .distinct()
            .order_by("grupo__nombre", "nombre")
        ),
    )


@dataclass
class Parecidos:
    """Lo que ya existe y se parece a un borrador (B-19-010).

    `producto` es el duplicado de verdad —el mismo ISBN, o la tupla completa de
    `buscar_duplicado`—, el que la confirmación rechazaría. `productos` son el mismo
    título y tomo en otra editorial, tipo o formato, comparados sin mayúsculas ni
    tildes: pueden ser otra edición o el mismo tomo mal cargado. `borradores` son los
    abiertos con el mismo título y tomo, o el mismo ISBN: el mismo producto que llegó
    por correo y por el chat, o cargado dos veces.
    """

    producto: object = None
    productos: list = field(default_factory=list)
    borradores: list = field(default_factory=list)

    def __bool__(self):
        return bool(self.producto or self.productos or self.borradores)


def parecidos_al_borrador(borrador, limite=3):
    producto = buscar_duplicado(
        borrador.titulo,
        borrador.volumen,
        borrador.tipo,
        borrador.formato,
        borrador.editorial,
        isbn=borrador.isbn,
    )
    buscado = titulo_comparable(borrador.titulo)
    productos = [
        candidato
        for candidato in ProductoEditorial.objects.filter(volumen=borrador.volumen)
        .exclude(pk=getattr(producto, "pk", None))
        .select_related("editorial", "formato")
        .order_by("-pk")
        if titulo_comparable(candidato.titulo) == buscado
    ][:limite]
    abiertos = BorradorProducto.objects.pendientes().exclude(pk=borrador.pk)
    borradores = [
        otro
        for otro in abiertos.filter(volumen=borrador.volumen).order_by("-pk")
        if titulo_comparable(otro.titulo) == buscado
    ]
    if borrador.isbn:
        borradores += [o for o in abiertos.filter(isbn=borrador.isbn) if o not in borradores]
    return Parecidos(producto=producto, productos=productos, borradores=borradores[:limite])


def editoriales_de_la_serie(titulo):
    """Las editoriales que ya tienen tomos con ese título (sin mayúsculas ni tildes)."""
    buscado = titulo_comparable(titulo)
    if not buscado:
        return []
    editoriales = {}
    for producto in ProductoEditorial.objects.select_related("editorial").only(
        "titulo", "editorial__nombre", "editorial__activa"
    ):
        if producto.editorial.activa and titulo_comparable(producto.titulo) == buscado:
            editoriales[producto.editorial_id] = producto.editorial
    return list(editoriales.values())


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
    # Plan 00 del circuito con los proveedores (B-01-016): una pre-venta nace sin
    # stock; lo declarado es lo que se pidió, y entra con la llegada.
    pedidas = []

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
            pedida = 0
            if datos.get("estado") == Producto.PRE_VENTA:
                pedida, datos["stock"] = datos.get("stock") or 0, 0

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
            if pedida:
                pedidas.append((producto, pedida))

        lote.rechazados = resultado.rechazados
        lote.save(update_fields=["rechazados"])
        _registrar_pedidos_del_lote(lote, pedidas, actor)

        # **Una sola** entrada por lote, no una por ítem (CU-ALT-NAC paso 8).
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL,
            actor=actor,
            objetivo=lote,
            ip=ip,
            detalle=_detalle_de_auditoria(lote, resultado),
        )

    return resultado


def _registrar_pedidos_del_lote(lote, pedidas, actor):
    """El pedido de las pre-ventas del lote, uno por proveedor y fecha de llegada.

    El pedido se hizo por fuera del sistema; el alta lo registra para que la
    pre-venta tenga cupo. El proveedor es el de la editorial del producto, o
    ninguno si no hay uno cargado (plan, ambigüedad 3).
    """
    from apps.suppliers import llegadas
    from apps.suppliers.models import PedidoProveedor, Proveedor

    grupos = {}
    for producto, cantidad in pedidas:
        proveedor = (
            Proveedor.objects.filter(editorial_id=producto.editorial_id).order_by("pk").first()
        )
        grupos.setdefault((proveedor, producto.fecha_llegada), []).append((producto, cantidad))
    for (proveedor, fecha), renglones in grupos.items():
        llegadas.registrar(
            proveedor, PedidoProveedor.LOTE, renglones, actor, fecha_estimada=fecha, lote=lote
        )


# ---------------------------------------------------------------------------
# CU-CAT-BAJ — el informe de impacto previo a la baja
# ---------------------------------------------------------------------------


@dataclass
class ImpactoDeBaja:
    """Lo que CU-CAT-BAJ tiene que informar antes de pedir la confirmacion (`CO-033`).

    Las cuatro categorias del CU —pedidos activos, suscripciones de reposicion,
    ofertas vigentes y carritos de clientes— se calculan desde que existen
    Pedidos, Restock, Pricing y Tienda (B-02-006). Se conserva el `None` para lo
    que no se pueda calcular: cero diria "no afecta a nadie", que es una
    afirmacion sobre datos que el propio CU considera parte de la decision.

    `stock` y `estado` no son categorias del CU. Van igual porque son lo unico
    verificable del producto mismo.
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


def _ofertas_del_producto(producto, hoy):
    """Las ofertas vivas que lo alcanzan: las de alcance producto, que lo
    referencian sólo a él, y las de su tipo, que referencian a varios."""
    from apps.catalog.models import Oferta

    vivas = Oferta.objects.vivas(hoy)
    return (
        vivas.filter(alcance=Oferta.PRODUCTO, producto=producto),
        vivas.filter(alcance=Oferta.TIPO, tipo_id=producto.tipo_id),
    )


def calcular_impacto_de_baja(producto):
    """`CO-033`: el informe de las cuatro categorias. Sólo lee."""
    from apps.pedidos.models import Pedido
    from apps.pedidos.servicios import ACTIVOS
    from apps.restock.models import SuscripcionReposicion
    from apps.tienda.models import LineaCarrito

    exclusivas, del_tipo = _ofertas_del_producto(producto, timezone.localdate())
    return ImpactoDeBaja(
        stock=producto.stock,
        estado=producto.get_estado_display(),
        pedidos_activos=Pedido.objects.filter(estado__in=ACTIVOS, lineas__producto=producto)
        .distinct()
        .count(),
        suscripciones_de_reposicion=SuscripcionReposicion.objects.filter(
            producto=producto, estado__in=SuscripcionReposicion.EN_ESPERA
        ).count(),
        ofertas_vigentes=exclusivas.count() + del_tipo.count(),
        carritos_con_el_producto=LineaCarrito.objects.filter(producto=producto)
        .values("carrito")
        .distinct()
        .count(),
    )


@dataclass
class BajaDeProducto:
    suscripciones: int = 0
    ofertas_dadas_de_baja: list = field(default_factory=list)
    ofertas_desvinculadas: int = 0
    carritos: int = 0


def confirmar_baja_de_producto(producto, *, actor, ip=None):
    """`CO-034`: la baja lógica y la resolución de lo que el producto tenía atado.

    - Las suscripciones en espera se cancelan (como `CO-076`, se eliminan).
    - Las ofertas que lo referenciaban sólo a él quedan Dadas de baja por
      `CO-058`, con su entrada en el log: no se borran (B-02-007, desvío decidido
      por el responsable). Las de su tipo, que referencian a varios, dejan de
      alcanzarlo porque un descatalogado no está en la tienda.
    - Las líneas de carrito quedan «Producto no disponible» por su estado (lo
      deriva la consulta del carrito) y sus clientes con cuenta reciben un aviso.
    - Los pedidos activos no se tocan: postcondición negativa del CU.
    """
    from apps.catalog import ofertas
    from apps.core.segundo_plano import despues_del_commit
    from apps.restock.models import SuscripcionReposicion
    from apps.tienda.models import LineaCarrito

    with transaction.atomic():
        producto = type(producto).objects.select_for_update().get(pk=producto.pk)
        anterior = producto.get_estado_display()
        producto.estado = Producto.DESCATALOGADO
        producto.save(update_fields=["estado"])

        hecho = BajaDeProducto()
        hecho.suscripciones = SuscripcionReposicion.objects.filter(
            producto=producto, estado__in=SuscripcionReposicion.EN_ESPERA
        ).delete()[0]
        exclusivas, del_tipo = _ofertas_del_producto(producto, timezone.localdate())
        hecho.ofertas_desvinculadas = del_tipo.count()
        for oferta in list(exclusivas):
            ofertas.confirmar_baja(oferta, actor=actor, ip=ip)
            hecho.ofertas_dadas_de_baja.append(str(oferta))
        clientes = list(
            LineaCarrito.objects.filter(producto=producto, carrito__usuario__isnull=False)
            .values_list("carrito__usuario__email", flat=True)
            .distinct()
        )
        hecho.carritos = (
            LineaCarrito.objects.filter(producto=producto).values("carrito").distinct().count()
        )

        RegistroAuditoria.registrar(
            RegistroAuditoria.BAJA_PRODUCTO,
            actor=actor,
            ip=ip,
            objetivo=producto,
            detalle=(
                f"{producto.codigo} · «{producto.titulo}» · estado anterior: {anterior} → "
                f"{producto.get_estado_display()} · stock al momento de la baja: "
                f"{producto.stock} · "
                f"suscripciones canceladas: {hecho.suscripciones} · ofertas dadas de baja: "
                f"{len(hecho.ofertas_dadas_de_baja)} · ofertas de su tipo que dejan de alcanzarlo: "
                f"{hecho.ofertas_desvinculadas} · carritos marcados: {hecho.carritos}"
            ),
        )
        if clientes:
            despues_del_commit(_avisar_carritos, producto.titulo, clientes)
    return hecho


def _avisar_carritos(titulo, correos):
    """`CO-034`: los clientes con el producto en el carrito se enteran."""
    from apps.core.mail import enviar_correo

    for correo in correos:
        enviar_correo(
            asunto=f"«{titulo}» ya no está disponible",
            cuerpo=(
                f"«{titulo}» salió del catálogo y quedó marcado como no disponible en tu "
                "carrito. Podés quitarlo y seguir con el resto de tu compra."
            ),
            destinatarios=[correo],
        )
