"""Cómo una extracción se convierte en borradores (CU-ALT-NOV pasos 5, 6, 7 y 9).

Es el punto donde lo que el modelo **propuso** se cruza contra lo que el sistema
**sabe**: el catálogo real, la cabecera del proveedor y los topes del negocio.
Nada de acá crea un producto — eso lo hace CU-ALT-REV, con una persona confirmando.

**Trabaja sobre la extracción ya guardada, no sobre el modelo.** Regenerar los
borradores de un correo no vuelve a llamar al modelo de lenguaje: lee
`CorreoProveedor.extraccion`, que es la foto que quedó de esa corrida. No es una
optimización, es la regla de que nada caro se ejecuta sin aprobación explícita —
corregirle la editorial a un proveedor y rehacer sus borradores no debería
costar otra tanda de minutos de GPU.

**Por qué vive en `catalog` y no en `suppliers`:** todo lo que decide acá es
conocimiento de catálogo —qué cuenta como duplicado, qué formato aplica a qué
tipo, con qué estado nace un producto según su fecha—. Lo único que aporta
proveedores es el origen del correo y la cabecera heredada, y eso llega como
datos. La flecha de dependencia sigue la que ya existía: `suppliers` conoce a
`catalog`, no al revés.
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.catalog import services
from apps.catalog.models import BorradorProducto, ConfianzaCampo, Formato, Producto
from apps.core import imagenes
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

logger = logging.getLogger(__name__)

# Los motivos por los que un producto anunciado no llega a ser borrador. Son
# constantes y no cadenas sueltas porque la pantalla los cuenta por separado y
# el resumen del comando los enumera: escritos a mano en tres lugares, el día
# que se cambie uno los otros dos siguen diciendo lo viejo.
YA_EXISTE = "ya_existe"
REPETIDO_EN_EL_CORREO = "repetido_en_el_correo"
SIN_TITULO = "sin_titulo"

MOTIVOS = {
    YA_EXISTE: "Ya está en el catálogo",
    REPETIDO_EN_EL_CORREO: "Repetido dentro del mismo correo",
    SIN_TITULO: "El modelo no pudo leerle el título",
}


@dataclass
class Omitido:
    """Un producto anunciado que no generó borrador, y por qué."""

    titulo: str
    volumen: int | None
    isbn: str
    motivo: str
    producto_existente: int | None = None

    @property
    def motivo_legible(self):
        return MOTIVOS.get(self.motivo, self.motivo)


@dataclass
class ResultadoGeneracion:
    """Lo que CU-ALT-NOV paso 9 pide registrar y el paso 10 pide notificar."""

    creados: list = field(default_factory=list)
    omitidos: list = field(default_factory=list)

    @property
    def incompletos(self):
        return [b for b in self.creados if b.estado == BorradorProducto.INCOMPLETO]

    @property
    def duplicados(self):
        return [o for o in self.omitidos if o.motivo == YA_EXISTE]

    @property
    def resumen(self):
        return {
            "generados": len(self.creados),
            "incompletos": len(self.incompletos),
            "omitidos": len(self.omitidos),
            "duplicados": len(self.duplicados),
        }


def generar(correo, *, portadas=None, actor=None, ip=None):
    """Convierte la extracción guardada de un correo en borradores.

    `portadas` es un diccionario de identificador a bytes, tal como lo arma
    `suppliers.services.portadas_de`. Se recibe hecho en vez de leerse acá para
    que la lectura del `.eml` —que es cara y es asunto de proveedores— pase una
    sola vez por correo y no una por producto.

    **Regenerar un correo reemplaza sus borradores abiertos, no los duplica.**
    Los ya confirmados o rechazados se conservan: son historia, y volver a
    proponerlos sería reabrir una decisión que alguien ya tomó.

    Nunca levanta por un producto malo: uno que no se pueda armar se omite con
    su motivo y el resto sigue. Es la misma distinción de CU-ALT-NAC entre una
    exclusión esperada y un fallo transaccional.
    """
    extraccion = correo.extraccion or {}
    resultado = ResultadoGeneracion()

    configuracion = ConfiguracionSistema.obtener()
    editorial = correo.proveedor.editorial
    tipo = correo.proveedor.tipo_por_defecto
    periodo = _fecha_desde_iso(extraccion.get("periodo"))
    reparos_del_correo = list(extraccion.get("reparos") or [])

    # Lo ya visto en este mismo correo, para atrapar el repetido de A11. Se
    # llevan las dos claves porque son las dos formas en que el mismo tomo
    # aparece dos veces: con el mismo ISBN, o sin ISBN y con la misma tupla.
    isbn_vistos = set()
    claves_vistas = set()

    with transaction.atomic():
        # Los abiertos se van; los resueltos quedan. Sin esto, reprocesar un
        # correo para corregir una extracción dejaría las dos tandas en la cola
        # y alguien tendría que rechazar la vieja a mano, una por una.
        BorradorProducto.objects.filter(
            correo=correo, estado__in=BorradorProducto.ESTADOS_ABIERTOS
        ).delete()

        for crudo in extraccion.get("productos") or []:
            omitido = _omitir(crudo, tipo, editorial, isbn_vistos, claves_vistas)
            if omitido:
                resultado.omitidos.append(omitido)
                continue

            borrador = _armar(
                crudo,
                correo=correo,
                editorial=editorial,
                tipo=tipo,
                periodo=periodo,
                reparos_del_correo=reparos_del_correo,
                stock=configuracion.stock_inicial_por_defecto,
            )
            borrador.save()
            borrador.etiquetas.set(getattr(borrador, "etiquetas_de_la_serie", []))
            _guardar_confianzas(
                borrador,
                crudo.get("confianza") or {},
                fecha_propia=bool(_fecha_desde_iso(crudo.get("fecha"))),
            )
            _adjuntar_portada(borrador, portadas or {})

            if borrador.isbn:
                isbn_vistos.add(borrador.isbn)
            claves_vistas.add(_clave(borrador.titulo, borrador.volumen, tipo, editorial))
            resultado.creados.append(borrador)

    _auditar(correo, resultado, actor=actor, ip=ip)
    return resultado


# ---------------------------------------------------------------------------
# Paso 5 — validar contra el catálogo
# ---------------------------------------------------------------------------


def _omitir(crudo, tipo, editorial, isbn_vistos, claves_vistas):
    """El motivo por el que este producto no llega a borrador, o `None`.

    El orden no es casual. Primero lo que no se puede identificar, después lo
    repetido dentro del envío —que todavía se puede arreglar corrigiendo el
    correo— y al final el duplicado contra el catálogo, que es el único que
    obliga a consultar la base.
    """
    titulo = (crudo.get("titulo") or "").strip()
    isbn = (crudo.get("isbn") or "").strip()
    volumen = crudo.get("volumen")

    if not titulo:
        # Sin título no hay con qué buscarlo ni con qué mostrarlo en la cola.
        # Un borrador así solo se podría rechazar, así que no llega a existir.
        return Omitido(titulo="", volumen=volumen, isbn=isbn, motivo=SIN_TITULO)

    # A11, aplicado al correo en vez de al formulario: dos filas del mismo tomo
    # son el mismo producto aunque le hayan escrito el título distinto. Se marca
    # **la segunda**, que es la que llega cuando la primera ya está.
    clave = _clave(titulo, volumen, tipo, editorial)
    if (isbn and isbn in isbn_vistos) or clave in claves_vistas:
        return Omitido(titulo=titulo, volumen=volumen, isbn=isbn, motivo=REPETIDO_EN_EL_CORREO)

    # El duplicado contra lo ya cargado (CU-ALT-NOV paso 5). Reusa la misma función
    # que el alta manual: si hubiera dos definiciones de "el mismo producto",
    # tarde o temprano dirían cosas distintas.
    formato = _resolver_formato(crudo.get("formato"), tipo)
    existente = services.buscar_duplicado(
        titulo=titulo,
        volumen=volumen,
        tipo=tipo,
        formato=formato,
        editorial=editorial,
        isbn=isbn,
    )
    if existente:
        return Omitido(
            titulo=titulo,
            volumen=volumen,
            isbn=isbn,
            motivo=YA_EXISTE,
            producto_existente=existente.pk,
        )
    return None


def _clave(titulo, volumen, tipo, editorial):
    """La identidad de un producto dentro de un mismo correo.

    Normaliza el título igual que la restricción de la base: "Batman " un
    martes y "batman" el jueves son el mismo tomo.
    """
    return (
        " ".join((titulo or "").split()).lower(),
        volumen,
        tipo.pk if tipo else None,
        editorial.pk if editorial else None,
    )


def _resolver_formato(nombre, tipo):
    """El `Formato` que corresponde a lo que el modelo copió, o `None`.

    Solo se busca si el tipo lo usa (A12): en un artbook o una novela ligera el
    tamaño no fija el precio y no hay nada que resolver. Y se respeta A20 —el
    formato tiene que estar ofrecido para ese tipo—, porque un B6 asignado a un
    cómic sería un dato que el alta manual nunca habría dejado cargar.
    """
    nombre = " ".join(str(nombre or "").split())
    if not nombre or not tipo or not tipo.usa_formato:
        return None
    # Sin tildes ni signos (B-01-023): «Tankobon» es el «Tankōbon» del catálogo.
    candidato = services.por_nombre(Formato.objects.filter(activo=True), nombre)
    if candidato and candidato.aplica_a(tipo):
        return candidato
    return None


# ---------------------------------------------------------------------------
# Paso 6 — armar el borrador y derivarle el estado
# ---------------------------------------------------------------------------


def _armar(crudo, *, correo, editorial, tipo, periodo, reparos_del_correo, stock, proveedor=None):
    """El borrador todavía sin guardar, con todo lo derivado ya resuelto."""
    formato = _resolver_formato(crudo.get("formato"), tipo)
    fecha_propia = _fecha_desde_iso(crudo.get("fecha"))
    fecha = fecha_propia or periodo
    estado_sugerido, fecha_llegada = _estado_por_fecha(fecha)

    reparos = list(crudo.get("reparos") or [])
    # Los del correo entero se copian a cada borrador: la cola de CU-ALT-REV se mira
    # de a un borrador por vez, y un reparo que solo viva en el correo no lo
    # vería nadie desde ahí.
    reparos.extend(reparos_del_correo)
    reparos.extend(_reparos_derivados(crudo, tipo, formato, fecha, estado_sugerido))

    borrador = BorradorProducto(
        correo=correo,
        proveedor=correo.proveedor if correo else proveedor,
        titulo=" ".join((crudo.get("titulo") or "").split()),
        volumen=crudo.get("volumen"),
        isbn=(crudo.get("isbn") or "").strip(),
        editorial=editorial,
        tipo=tipo,
        formato=formato,
        precio=_precio_desde_texto(crudo.get("precio"))
        or _precio_de_la_tabla(editorial, tipo, formato),
        fecha_llegada=fecha_llegada,
        estado_sugerido=estado_sugerido,
        stock_inicial=stock,
        reparos=reparos,
        cid_portada=(crudo.get("imagen") or "").strip(),
    )
    # `incompleto` no es un estado peor: es el indicador "Extracción incompleta"
    # que CU-ALT-NOV pide para los productos que el modelo identificó pero no pudo
    # completar. Van a la **misma** cola que los demás.
    _completar_con_la_serie(borrador)
    borrador.estado = (
        BorradorProducto.INCOMPLETO
        if borrador.campos_bloqueantes_vacios
        else BorradorProducto.PENDIENTE
    )
    return borrador


def _completar_con_la_serie(borrador):
    """B-01-020: si la serie ya está en el catálogo, lo que el correo no trae.

    Sólo lo vacío —autor y sinopsis, que el correo nunca trae— y «sólo
    adultos», que únicamente se enciende: un tomo nuevo de una serie para adultos
    no puede nacer a la vista de todos por omisión. El tipo y el formato no se
    tocan: los leyó el modelo, y si difieren de los de la serie la ficha lo
    señala para que decida una persona.
    """
    serie = services.serie_de(borrador.titulo, borrador.editorial)
    if serie is None:
        return
    borrador.autor = borrador.autor or serie.autor
    borrador.sinopsis = borrador.sinopsis or serie.sinopsis
    borrador.solo_adultos = borrador.solo_adultos or serie.solo_adultos
    # Las etiquetas son una relación: se asignan después de guardar el borrador.
    borrador.etiquetas_de_la_serie = serie.etiquetas


def _precio_de_la_tabla(editorial, tipo, formato):
    """B-01-018: si el correo no trae precio, el de la tabla de referencia.

    Es lo que el Administrador pondría a mano, y el borrador deja de nacer
    incompleto por un dato que el sistema ya tiene. Un precio que el correo sí
    trae se respeta, aunque no coincida: la pantalla muestra el de la tabla al
    lado.
    """
    fila = services.precio_de_referencia(editorial, tipo, formato)
    return fila.pvp if fila else None


def _estado_por_fecha(fecha):
    """Con qué estado nace el borrador, y con qué fecha (CU-ALT-NOV paso 6).

    La regla del CU es "futura → Pre-venta; semana en curso o ausente → Activo",
    y A10 le agrega la condición que la hace consistente: **una fecha pasada no
    se conserva**. Si el material ya llegó, el producto va Activo y sin fecha;
    arrastrarla dejaría un producto activo con fecha de llegada del mes pasado,
    que no significa nada y ensucia la vigilancia de pre-ventas de CU-ALT-TRA.
    """
    if fecha and fecha > timezone.localdate():
        return Producto.PRE_VENTA, fecha
    return Producto.ACTIVO, None


def _reparos_derivados(crudo, tipo, formato, fecha, estado_sugerido):
    """Lo que el sistema le descartó al modelo al cruzarlo con el catálogo.

    Son reparos y no confianzas bajas: esto no lo dudó el modelo, lo rechazamos
    nosotros. Que se vean es lo que evita que un dato caído en el camino
    aparezca como un campo vacío sin explicación.
    """
    reparos = []
    nombre_formato = " ".join(str(crudo.get("formato") or "").split())
    if nombre_formato and tipo and tipo.usa_formato and formato is None:
        reparos.append(
            f"Formato descartado («{nombre_formato}»): no existe o no se ofrece " f"para {tipo}."
        )
    if fecha and estado_sugerido == Producto.ACTIVO:
        reparos.append(
            f"Fecha anunciada ({fecha:%d/%m/%Y}) ya pasó: el borrador nace Activo y sin fecha."
        )
    return reparos


def _precio_desde_texto(crudo):
    """El precio ya viene validado por la extracción; acá solo se reconstruye."""
    texto = str(crudo or "").strip()
    if not texto:
        return None
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def _fecha_desde_iso(crudo):
    texto = str(crudo or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _guardar_confianzas(borrador, declaradas, *, fecha_propia=False):
    """Una fila por campo que el modelo calificó.

    **La fecha es la excepción y no es un detalle.** El modelo declara su
    confianza mirando la fila, y una fila de novedades casi nunca trae fecha
    propia: el período lo anuncia el correo entero. Con lo cual el modelo
    contesta "baja" —correctamente, según el prompt— sobre un campo que el
    borrador después hereda del período, igual que hereda la editorial.

    Guardarla así rompería CU-ALT-REV entero: la confirmación en lote excluye a
    todo borrador con algún campo de confianza baja, así que **ningún
    borrador sería nunca confirmable en lote**, que es exactamente el trabajo
    que el pipeline venía a eliminar. Es el mismo modo de falla que A7 de
    proveedores vino a evitar con la editorial y el rubro.

    Por eso `fecha` solo lleva confianza **cuando la fecha salió de la fila**.
    Heredada del período no hay juicio del modelo que registrar, igual que no
    lo hay para la editorial.

    Una confianza que no es uno de los tres valores válidos ya viene convertida
    a "baja" desde la extracción; acá se vuelve a filtrar por si el JSON
    guardado es de una versión vieja del prompt. Al alza sería peor: un valor
    raro leído como "alta" haría que un dato dudoso se confirme en lote sin que
    nadie lo mire.
    """
    niveles = dict(ConfianzaCampo.NIVEL_CHOICES)
    if not fecha_propia:
        declaradas = {campo: nivel for campo, nivel in declaradas.items() if campo != "fecha"}
    ConfianzaCampo.objects.bulk_create(
        [
            ConfianzaCampo(
                borrador=borrador,
                campo=campo,
                nivel=nivel if nivel in niveles else ConfianzaCampo.BAJA,
            )
            for campo, nivel in declaradas.items()
            if isinstance(campo, str) and isinstance(nivel, str)
        ]
    )


# ---------------------------------------------------------------------------
# Paso 7 — la portada
# ---------------------------------------------------------------------------


def _adjuntar_portada(borrador, portadas):
    """Saca la imagen de las partes del correo y la deja como archivo.

    Se extrae **al generar el borrador y no al confirmarlo** porque la pantalla
    de revisión tiene que mostrar la tapa: revisar un borrador sin poder ver la
    portada es revisar la mitad, y la portada equivocada es justamente uno de
    los errores que la revisión existe para atrapar.

    Que falte no interrumpe nada (CU-ALT-NOV): el borrador queda con la portada
    pendiente y se adjunta a mano después.

    **Se procesa con RNF-05 al adjuntarla** (plan 00 de cierre de deuda, D2): la
    revisión ve la misma imagen que se va a guardar con el producto, y el
    adjunto original no llega al almacenamiento. Uno que no es JPG, PNG o WebP
    deja el mismo reparo que uno ilegible.
    """
    imagen = portadas.get(borrador.cid_portada) if borrador.cid_portada else None
    if not imagen:
        return
    try:
        procesada = imagenes.procesar(ContentFile(imagen.contenido, name=imagen.nombre or ""))
        borrador.portada.save(f"borrador-{borrador.pk}-{procesada.name}", procesada, save=True)
    except (imagenes.ImagenInvalida, OSError):
        # Una portada ilegible no puede tumbar el procesamiento del correo
        # entero. Queda el reparo, que es lo que se mira en la revisión.
        logger.warning("No se pudo guardar la portada del borrador %s", borrador.pk)
        borrador.reparos.append("La portada del correo no se pudo guardar.")
        borrador.save(update_fields=["reparos"])


# ---------------------------------------------------------------------------
# B-19-006 · `CU-AVI-BOR`: un borrador cargado desde Telegram
# ---------------------------------------------------------------------------


def desde_telegram(crudo, *, editorial, usuario, portada=None, reparos=(), tipo=None):
    """Un borrador con lo que el modelo leyó del mensaje: el mismo armado que el de un
    correo —precio de la tabla, datos de la serie, estado por la fecha, confianzas—,
    sin correo de origen. El proveedor es el de la editorial, si hay uno cargado.
    El tipo es el que dijo el mensaje; si no dijo, el del proveedor o el de la serie.

    `crudo` tiene la forma de un producto de `Extraccion.como_json()`. `portada`
    son los bytes de la foto, si vino una. Nunca crea un producto (regla 4).
    """
    from apps.suppliers.models import Proveedor

    proveedor = (
        Proveedor.objects.activos().filter(editorial=editorial).order_by("pk").first()
        if editorial
        else None
    )
    if tipo is None and proveedor is not None:
        tipo = proveedor.tipo_por_defecto
    if tipo is None and editorial is not None:
        serie = services.serie_de(crudo.get("titulo"), editorial)
        tipo = serie.tipo if serie else None
    with transaction.atomic():
        borrador = _armar(
            crudo,
            correo=None,
            editorial=editorial,
            tipo=tipo,
            periodo=None,
            reparos_del_correo=list(reparos),
            stock=ConfiguracionSistema.obtener().stock_inicial_por_defecto,
            proveedor=proveedor,
        )
        borrador.origen = BorradorProducto.TELEGRAM
        borrador.cargado_por = usuario
        borrador.save()
        borrador.etiquetas.set(getattr(borrador, "etiquetas_de_la_serie", []))
        _guardar_confianzas(
            borrador,
            crudo.get("confianza") or {},
            fecha_propia=bool(_fecha_desde_iso(crudo.get("fecha"))),
        )
    if portada:
        try:
            procesada = imagenes.procesar(ContentFile(portada, name="telegram.jpg"))
            borrador.portada.save(f"borrador-{borrador.pk}-{procesada.name}", procesada, save=True)
        except (imagenes.ImagenInvalida, OSError):
            borrador.reparos.append("La foto que llegó por Telegram no se pudo guardar.")
            borrador.save(update_fields=["reparos"])
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.BORRADORES_GENERADOS,
        actor=usuario,
        objetivo=borrador,
        detalle=f"«{borrador}» cargado desde Telegram: un borrador para revisar.",
    )
    return borrador


# ---------------------------------------------------------------------------
# Paso 9 — auditoría
# ---------------------------------------------------------------------------


def _auditar(correo, resultado, *, actor, ip):
    """Una entrada consolidada por correo, no una por borrador.

    Es el mismo criterio que la del alta en lote de CU-ALT-NAC: lo que se quiere
    poder reconstruir después es *qué produjo este correo*, y treinta filas
    sueltas esconderían justamente eso.
    """
    partes = [
        f"correo #{correo.pk} de {correo.proveedor}",
        f"{len(resultado.creados)} borrador(es) generado(s)",
        f"{len(resultado.incompletos)} incompleto(s)",
        f"{len(resultado.duplicados)} omitido(s) por duplicado",
    ]
    otros = len(resultado.omitidos) - len(resultado.duplicados)
    if otros:
        partes.append(f"{otros} omitido(s) por otros motivos")
    version = (correo.extraccion or {}).get("version_prompt") or correo.version_prompt
    if version:
        partes.append(f"prompt v{version}")

    RegistroAuditoria.registrar(
        RegistroAuditoria.BORRADORES_GENERADOS,
        actor=actor,
        ip=ip,
        objetivo=correo,
        detalle="; ".join(partes),
    )
