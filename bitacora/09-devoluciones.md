> **Tipo: Bitácora.** Se anexa, no se reescribe. Una entrada resuelta se marca; no se borra.

# Bitácora — `09` Devoluciones

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-09-001 · El ciclo del cambio de producto tiene dos versiones en el documento

**Tipo:** Corrección · **Fecha:** 2026-10-16 · **Alcance:** `CU-DEV-RES` (opción A), `CO-100`, `DevolucionFisica`, DME-12, DME-16
**Estado:** Resuelta el 2026-10-16 — ver R-09-001

**Qué apareció.**
El documento describe dos veces lo que pasa después de autorizar un cambio, y las dos versiones
no coinciden. Además, la segunda usa cuatro operaciones que no tienen contrato.

**Qué dice la especificación.**

Primera versión, en la ficha, el contrato y el diagrama de clases:

> «El sistema registra el intercambio: decrementa el stock del producto de reemplazo en una
> unidad, marca el ítem devuelto como "Pendiente de retiro físico", actualiza el caso a Resuelto»
> (`CU-DEV-RES`, paso 5, opción A)

> «(a) Se creó una instancia df : DevolucionFisica. (b) Se formó la asociación df → cd. (c)
> df.estado quedó en Pendiente de retiro.» (`CO-100`, Postcondiciones)

> `DevolucionFisica` — `estado : {Pendiente de retiro, Retirado}` (modelo de dominio, área 5,
> SUP-08)

Segunda versión, en los diagramas de estados:

- **DME-12 (`ArticuloRetenido`):** `CO-100 resolverCasoConCambio` crea un artículo en «Reservado
  para cambio». Pasa a Disponible con `CO-225 aceptarPruebaDeDestruccion` o con
  `CO-223 confirmarRecepcionDeDevolucion`.
- **DME-16 (`CambioProducto`):** `CO-100` lleva a «Pendiente de prueba de destrucción» si el
  motivo es Defecto de fabricación o Error de imprenta, y a «Pendiente de recepción» si es
  Disconformidad. De la prueba: `CO-224 presentarPruebaDeDestruccion` → «Prueba presentada»;
  `CO-226 rechazarPruebaDeDestruccion` la devuelve; `CO-225 aceptarPruebaDeDestruccion` →
  «Completado». De la recepción: `CO-223 confirmarRecepcionDeDevolucion` → «Completado».

`CambioProducto` no aparece en el diagrama de clases. `CO-223` a `CO-226` no están en ningún
archivo de contratos: el generador ya los informa como hueco en la numeración (`docs/DEUDA.md`,
«Consistencia de la especificación consigo misma»). Tampoco hay ficha que diga quién presenta la
prueba de destrucción ni quién la acepta.

**Qué se hizo.**
Nada todavía. El plan del módulo (`docs/planes/09-devoluciones.md`, ambigüedad 1) deja la opción
del cambio para el final y propone tres caminos. El resto del módulo no depende de esto.

**Qué habría que cambiar.**
Depende de la decisión:
- **Si manda la primera versión:** quitar de DME-12 la transición de `CO-100` a «Reservado para
  cambio» y las de `CO-223` y `CO-225`; retirar DME-16 o rehacerlo sobre `DevolucionFisica`.
- **Si manda la segunda:** escribir los contratos `CO-223` a `CO-226` y la ficha que los usa;
  agregar `CambioProducto` al diagrama de clases (o reemplazar con él a `DevolucionFisica`);
  enmendar las postcondiciones de `CO-100` para que creen el `ArticuloRetenido` reservado y el
  `CambioProducto` en el estado que corresponde al motivo.

---

### B-09-002 · El plazo de devolución corre desde el despacho

**Tipo:** Corrección · **Fecha:** 2026-10-16 · **Alcance:** BR-14, `CU-DEV-SOL`, `CO-099`, `CO-185`
**Estado:** Abierta

**Qué apareció.**
El sistema no registra cuándo recibe el Cliente su pedido: el último estado de un pedido es
Despachado. Lo que se puede medir es cuándo salió.

**Qué dice la especificación.**
> «El tiempo transcurrido desde el despacho del pedido no supera el plazo máximo configurado»
> (`CU-DEV-SOL`, Precondiciones; `CO-099`, Precondiciones)

> «El plazo máximo para iniciar un caso de devolución […] es de diez días corridos desde la
> recepción del bien» (BR-14)

**Qué se hizo.**
El plazo se cuenta desde que el pedido pasó a Despachado, como dicen la ficha y el contrato. En una
venta de mostrador, el pedido nace despachado y el plazo corre desde la venta. El parámetro vive en
Parámetros, sección Comercial, con 10 días por defecto y el piso legal como restricción de la base.

**Qué habría que cambiar.**
BR-14: «desde el despacho del pedido», o aclarar que el despacho es la mejor aproximación que el
sistema tiene a la recepción.

---

### B-09-003 · Un reclamo cubre una unidad, y sólo de lo que salió con el pedido

**Tipo:** Agregado · **Fecha:** 2026-10-16 · **Alcance:** `CO-099`, `CO-100`, `CO-101`, I-19, `CU-DEV-SOL` paso 2
**Estado:** Abierta

**Qué apareció.**
Una línea puede tener varias unidades (dos tomos del mismo título), y un pedido despachado puede
tener líneas canceladas o artículos que quedaron retenidos en el local por despacho diferido.

**Qué dice la especificación.**
`Nada` sobre las unidades: I-19 hace único el caso por línea, y `CO-100` descuenta «una unidad»
del reemplazo. `Nada` sobre las líneas canceladas o diferidas: el selector ofrece «los artículos
del pedido».

**Qué se hizo.**
El caso cubre una unidad: el cambio repone una y el reembolso vale una. Una línea de dos tomos
admite un solo reclamo. El selector ofrece sólo las líneas que salieron con el pedido (estado
Despachado): ni las canceladas, que ya se reembolsaron, ni las de despacho diferido, que el Cliente
todavía no recibió con ese pedido.

**Qué habría que cambiar.**
`CU-DEV-SOL` paso 2: «selector de ítem afectado, entre los artículos despachados con el pedido».
`CO-101`: «el 100 % del valor original de una unidad del ítem». Si hace falta reclamar varias
unidades de una línea, es una enmienda de I-19.

---

### B-09-004 · Cómo se calcula el reembolso, y los puntos que se ganaron con la compra

**Tipo:** Corrección · **Fecha:** 2026-10-16 · **Alcance:** RF-19, `CO-101`
**Estado:** Resuelta el 2026-10-19 — manda RF-19: los puntos ganados se descuentan (B-10-012)

**Qué apareció.**
El reembolso en puntos necesita una regla de conversión, y RF-19 pide algo que `CO-101` no declara.

**Qué dice la especificación.**
> «En caso de devolución posterior, el sistema debe descontar del saldo del cliente los puntos
> correspondientes al monto reembolsado, si estos ya hubieran sido acreditados.» (RF-19)

> «Se creó un LotePuntos de origen Reembolso con el 100 % del valor original del ítem, con la
> caducidad estándar, y un MovimientoPuntos de tipo Acreditación» (`CO-101`, Postcondiciones)

**Qué se hizo.**
La conversión es la de los demás reembolsos (B-01-010): lo pagado en dinero pasa a puntos
redondeando hacia arriba; lo pagado con puntos devuelve los mismos puntos (la parte de una unidad,
también hacia arriba). **No se descuentan los puntos ganados con la compra**: manda el contrato
(criterio de C-08), y es lo que ya hacen la cancelación de pre-ventas y la del artículo demorado. El
movimiento de acreditación queda vinculado al caso, como declara el modelo.

**Qué habría que cambiar.**
RF-19: quitar la frase del descuento, o enmendar `CO-101` (y los contratos de las otras
cancelaciones) para que lo declaren. Lo decide el responsable.

---

### B-09-005 · No existe el «tiempo de respuesta estimado»

**Tipo:** Corrección · **Fecha:** 2026-10-16 · **Alcance:** `CU-DEV-SOL` paso 6, `CO-099` Salida, `CU-CFG-PAR`
**Estado:** Abierta

**Qué apareció.**
La confirmación del reclamo debería mostrar un tiempo de respuesta estimado, pero no hay de dónde
sacarlo.

**Qué dice la especificación.**
> «informa el tiempo de respuesta estimado (si está configurado en CU-CFG-PAR)» (`CU-DEV-SOL`,
> paso 6)

La ficha de `CU-CFG-PAR` no tiene ese parámetro en ninguna sección.

**Qué se hizo.**
La confirmación dice el número del caso y que se le avisa por correo cuando se revise. No muestra
un plazo.

**Qué habría que cambiar.**
Quitar la mención del paso 6 de `CU-DEV-SOL` y de la Salida de `CO-099`, o agregar el parámetro a
`CU-CFG-PAR` (sección Comercial) y al modelo.

---

### B-09-006 · Las fotos del reclamo: cuántas, de qué tipo y quién las ve

**Tipo:** Agregado · **Fecha:** 2026-10-16 · **Alcance:** `CO-099` E3 y E4, `CO-187`, RNF-05
**Estado:** Abierta

**Qué apareció.**
E4 habla de un «tamaño máximo admitido» y un «formato no aceptado» sin dar valores. Y una foto que
un Cliente sube de su compra no es contenido público como una portada.

**Qué dice la especificación.**
`Nada` sobre los valores ni sobre quién puede ver las fotos.

**Qué se hizo.**
De 1 a 5 fotos por reclamo, JPG, PNG o WebP de hasta 5 MB cada una, convertidas a WebP como el
resto de las imágenes. Si una no se admite, no se registra nada y se informa qué archivo falló y
por qué. **Las fotos se guardan fuera de la carpeta pública**: sólo las ven el Cliente que las
subió y el Administrador, con sesión. Otro Cliente recibe «no existe».

**Qué habría que cambiar.**
`CO-099`, Notas: los límites. `CO-187`: que las imágenes son visibles sólo para el titular y el
Administrador.

---

### B-09-007 · Lo que se ve y se avisa alrededor del caso

**Tipo:** Agregado · **Fecha:** 2026-10-16 · **Alcance:** `CU-DEV-SOL` paso 5, `CU-DEV-RES` paso 5, `CO-100` Salida
**Estado:** Abierta

**Qué apareció.**
Cuatro puntos que la ficha nombra sin decir cómo son.

**Qué dice la especificación.**
> «notifica al Administrador de la existencia del nuevo caso» (`CU-DEV-SOL`, paso 5)

> «busca y selecciona en el catálogo el producto de reemplazo (de valor igual o comparable)»;
> «las instrucciones de retiro o reenvío según corresponda» (`CU-DEV-RES`, paso 5)

`Nada` sobre dónde sigue el Cliente su reclamo después de abrirlo.

**Qué se hizo.**
- El aviso al Administrador es un correo a los Administradores activos, con enlace al caso, como
  los avisos de pre-venta.
- «Igual o comparable» no se valida: la pantalla muestra los dos precios y decide el
  Administrador. Sólo se puede elegir un producto Activo con stock; los demás se listan como «Sin
  stock», con acceso al reembolso (E1).
- Las instrucciones dependen del canal: en una compra online, se coordina el envío del reemplazo y
  el retiro del reclamado; en una venta de mostrador, el Cliente lo trae y se lleva el reemplazo.
- El Cliente sigue el reclamo en el detalle del pedido de «Mi cuenta», al lado de la línea: número,
  estado, resolución, reemplazo o motivo del rechazo.

**Qué habría que cambiar.**
`CU-DEV-RES` paso 5: «de valor igual o comparable, a criterio del Administrador». `CU-CLI-HIS`
paso 3: el estado del reclamo de cada línea.

---

### B-09-008 · Las devoluciones se reformulan en arrepentimiento y garantía

**Tipo:** Corrección · **Fecha:** 2026-10-19 · **Alcance:** RF-14, BR-14, `CU-DEV-SOL`, `CU-DEV-RES`, `CO-099` a `CO-102`, `CO-185`, `CasoDevolucion`, `DevolucionFisica`, `CU-CFG-PAR`
**Estado:** Abierta

**Qué apareció.**
Revisando el sistema contra la ley, la simplicidad y el riesgo para el negocio (plan 00, C1):

- El reembolso no exigía devolver el artículo: con «Disconformidad», el Cliente se quedaba con el
  tomo y su valor en puntos.
- La `DevolucionFisica` nunca se cerraba y el reemplazo de un cambio no tenía cómo llegar.
- La revocación de una venta a distancia (Ley 24.240, art. 34) obliga a reintegrar lo pagado; el
  botón de arrepentimiento (Res. 424/2020, según entiende el equipo) no puede pedir registración.
- Un defecto se reclama por la garantía legal, que dura meses, no en 10 días.

**Qué dice la especificación.**
> «procesar el reembolso del 100% del valor del artículo en puntos nativos de la tienda»;
> «el motivo (producto recibido con defecto de fabricación, error de imprenta o disconformidad)»
> (RF-14)

> «marca el ítem devuelto como "Pendiente de retiro físico"» (`CU-DEV-RES`, paso 5)

**Qué se hizo** (decisión del responsable del 2026-10-19).

- **Dos tipos de reclamo.** *Arrepentimiento* (reemplaza a «Disconformidad»): por el **botón de
  arrepentimiento**, visible en la cabecera y el pie de la tienda y **sin registración** (con
  sesión, o con el número de pedido y el correo de la compra; sirve al invitado), sólo en
  compras online, cubre la **línea entera**, sin fotos. *Garantía* (Defecto de fabricación, Error
  de imprenta): desde «Mi cuenta», con fotos, cubre una unidad.
- **Dos plazos.** El de arrepentimiento (el parámetro que existía, piso legal 10 días) y uno
  **nuevo de garantía**, 90 días por defecto. Los dos corren desde el despacho o el retiro.
- **Resoluciones.** Arrepentimiento: **reembolso por el medio de pago** (o en puntos, si se pagó
  con puntos), cuando el local recibe el artículo, que **vuelve al stock**; si es el pedido entero,
  se reintegra también el envío. Garantía: **cambio** por un tomo de la misma editorial y el mismo
  formato, que queda en el stock en local del Cliente con **envío sin costo**; reembolso en
  puntos; o por el medio de pago en pedidos online.
- **El reembolso por el medio de pago se registra**: el sistema anota el monto y el pago; el dinero
  se devuelve desde el panel de la pasarela. No hay reembolso por la API ni transacciones
  negativas en la caja (I-09). En una compra de mostrador no se ofrece.
- **Lo que no es registrar se coordina por fuera del sistema**, por correo o teléfono: la ficha
  muestra el contacto. Así se pide la prueba de destrucción y se acuerda la devolución.
- **Se retiran `DevolucionFisica`** y el estado «Reservado para cambio» de `ArticuloRetenido`.
- El Cliente recibe **por correo el código de su caso** al abrirlo.

**Qué habría que cambiar.**
RF-14 y `CU-DEV-SOL`: los dos tipos, sus motivos, su base legal y el botón sin registración.
`CU-DEV-RES` y `CO-100` a `CO-102`: las resoluciones de cada tipo, el reembolso por el medio de
pago registrado (es una operación nueva o una variante de `CO-101`, a decidir) y la coordinación
por fuera. `CasoDevolucion`: «correo», «unidades», «monto reembolsado», cliente opcional, el motivo
Arrepentimiento y la resolución nueva; quitar `DevolucionFisica`. `CU-CFG-PAR` (Comercial): el
plazo de garantía. BR-14: los dos plazos. Que el tutor confirme los valores legales.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado.

### R-09-001 · Resolución de B-09-001

**Fecha:** 2026-10-16 · **Enmienda al documento:** pendiente, en DME-12 y DME-16

**Qué se decidió.**
Manda la primera versión: la ficha de `CU-DEV-RES`, `CO-100` y `DevolucionFisica` en el diagrama
de clases. Los diagramas de estados no están actualizados. `CambioProducto` y `CO-223` a `CO-226`
no forman parte de la especificación.

**Qué se hizo.**
`CO-100` se construye como lo declara su contrato: descuenta una unidad del reemplazo y crea la
`DevolucionFisica` en Pendiente de retiro. No crea ningún `ArticuloRetenido`. El estado «Reservado
para cambio», que el módulo 18 dejó declarado a partir de DME-12, queda sin uso: ninguna operación
especificada lo produce.

**Qué habría que cambiar.**
DME-12: quitar «Reservado para cambio» y sus tres transiciones (`CO-100`, `CO-223`, `CO-225`).
DME-16: retirarlo, o rehacerlo como el ciclo de `DevolucionFisica` (Pendiente de retiro →
Retirado). El modelo de dominio, área 5: quitar la asociación `Producto 0..1 — 0..* ArticuloRetenido
: sustituto en cambio`, que sólo tiene sentido con la segunda versión.

---

### Nota de cierre · 2026-10-16

`CU-DEV-SOL` y `CU-DEV-RES` quedan verificados con sus siete contratos, y `CO-130` gana el plazo de
devolución (sigue parcial por la sección Seguridad). Las siete puertas pasan. Quedan abiertas las
enmiendas de B-09-002 a B-09-007 y las de R-09-001 sobre DME-12 y DME-16. Lo que el módulo no
hace: confirmar el retiro físico del artículo cambiado, que ningún caso de uso especifica.
