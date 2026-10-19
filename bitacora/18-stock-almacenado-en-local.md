# Bitácora — `18` Stock Almacenado en Local

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-18-001 · Sesenta y cuatro contratos de otros módulos quedan archivados bajo el módulo 18

**Tipo:** Corrección · **Fecha:** 2026-09-14 · **Alcance:** `CO-155` a `CO-218`, todos los módulos
**Estado:** Resuelta — el diagnóstico era incorrecto; corregido el generador el 2026-09-22

**Qué apareció.**
`.contexto-ia/contratos/18-stock-almacenado-en-local.md` contiene 68 contratos. Sólo cuatro son del
módulo: `CO-151` a `CO-154`. Los otros 64 —de `CO-155` a `CO-218`— son operaciones de consulta y
de apertura de pantalla que pertenecen a todos los módulos del sistema:

| Contrato | A qué módulo pertenece |
| --- | --- |
| `CO-155 sincronizarCotizaciones` | 01 Alta Editorial (lo consume `CO-007`) |
| `CO-157 consultarColaDeCorreos` | 04 Proveedores |
| `CO-162 consultarInventario` | 02 Catálogo |
| `CO-172 consultarProveedores` | 04 Proveedores |
| `CO-176 consultarCatalogoPublico` | 07 Tienda Online |
| `CO-194 consultarCuentasDeCliente` | 11 Cuenta de Cliente |
| `CO-205 consultarLogDeAuditoria` | 16 Auditoría |
| … | … |

La causa es de estructura del documento, no del generador: en el documento de análisis esos
contratos vienen **después** del último encabezado de módulo, así que `generar_contexto.py` los
atribuye al módulo que estaba abierto, que es el 18. El script hace lo correcto con lo que recibe.

Lo que sí conviene saber es que **la verificación del generador no lo detecta**. Busca fichas sin
contrato, contratos sin ficha, módulos vacíos y huecos en la numeración. Acá no hay hueco alguno
—la numeración corre de `CO-001` a `CO-218` sin saltos— y la corrida del 2026-09-14 informó «Sin
observaciones».

**Qué dice la especificación.**
El documento agrupa los contratos por módulo con encabezados de la forma «Módulos NN: Nombre». A
partir de `CO-155` no hay encabezado nuevo, así que el capítulo de contratos de consulta queda
dentro del módulo 18 por posición y no por contenido. Cada contrato **sí** declara a qué caso de
uso pertenece, en su campo «Referencias Cruzadas»: la información está, pero no en el lugar por el
que se busca.

**Qué se hizo.**
Nada. `.contexto-ia/` no se edita a mano y la corrección no se aplica ahí: lo que hay que cambiar
es el documento. Se anotó acá, y el recuento por archivo de `docs/DEUDA.md` lleva la aclaración
para que nadie lea «68 contratos del módulo 18».

**Qué habría que cambiar.**
En el documento de análisis, abrir un encabezado de capítulo propio antes de `CO-155` —las
operaciones de consulta son transversales y no pertenecen a ningún módulo— o repartir cada
contrato bajo el encabezado del módulo que le corresponde. La primera opción es menos trabajo y
más fiel: `CO-156 cancelarOperacion` aparece referenciado por 15 casos de uso de 8 módulos
distintos, así que no hay un módulo al que mudarlo.

Como consecuencia, convendría que `generar_contexto.py` avise cuando un contrato se archiva en un
módulo que ninguno de sus casos de uso referenciados habita. Hoy eso no se chequea y es
exactamente el error que se coló.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-18-001 · Resolución de B-18-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
**El diagnóstico de la entrada era incorrecto.** Afirma que la causa es de estructura del
documento —que a partir de `CO-155` no hay encabezado nuevo— y que «el script hace lo correcto con
lo que recibe». Las dos mitades son falsas: el documento **sí** tiene encabezados antes de
`CO-155` («Transversales») y antes de `CO-157` («Contratos de Operaciones de Solo Lectura»).

Quien falla es el generador. `RE_MODULO` sólo reconoce encabezados de la forma «Módulos NN:
Nombre»; los dos encabezados de capítulo no tienen número de módulo, no abren módulo nuevo, y los
64 contratos que vienen debajo se archivan bajo el último módulo numerado que quedó abierto, que
es el 18.

Es una lección sobre la entrada misma: la explicación estaba construida sobre una suposición
—«a partir de `CO-155` no hay encabezado»— que no se verificó contra el documento.

**Qué se hizo.**
Tres cambios en `scripts/generar_contexto.py`:

1. **Cada contrato se archiva según los casos de uso de su campo Referencias Cruzadas**, no según
   la posición que ocupa en el documento. La información estaba: era cuestión de leerla de donde
   está y no de donde se la buscaba.
2. Los contratos cuyas referencias cruzan **más de un módulo** van a
   `contratos/00-transversales.md`. Es el caso de `CO-156 cancelarOperacion`, referenciado por 15
   casos de uso de 8 módulos: no hay un módulo al que mudarlo.
3. **El chequeo que la entrada proponía**, que es lo único de ella que queda en pie: avisar cuando
   un contrato termina en un archivo de módulo que ninguno de sus casos de uso habita.

---

### B-18-002 · Un artículo retenido por unidad

**Tipo:** Corrección · **Fecha:** 2026-10-14 · **Alcance:** `ArticuloRetenido`, `CO-095`, `CO-154`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 1)

**Qué apareció.**
Una línea de pedido puede tener varias unidades del mismo tomo, y cada unidad puede tener un destino distinto: una se despacha, otra se retira, otra vence.

**Qué dice la especificación.**
> «ArticuloRetenido "0..1" -- "0..1" LineaPedido : se originó en» (Área 5)

> «Producto.stock pasó de su valor anterior a ese valor más una unidad» (`CO-154`)

**Qué se hizo.**
Cada unidad es un artículo retenido, con el precio unitario de la línea como valor. Una línea de dos tomos con despacho diferido da dos artículos.

**Qué habría que cambiar.**
Área 5: `ArticuloRetenido "0..*" -- "0..1" LineaPedido`.

---

### B-18-003 · La línea del pedido no cambia cuando su artículo queda retenido

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-PED-OPC` paso 6, `CU-PED-CON`, `CU-CLI-HIS`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 2)

**Qué apareció.**
Cuando el artículo de despacho diferido llega, su seguimiento pasa al stock almacenado. DME-08 no tiene un estado de línea para «en el local a nombre del Cliente».

**Qué dice la especificación.**
Nada.

**Qué se hizo.**
La línea conserva «Disponible · Despacho diferido». El detalle del pedido lo muestra como «En el local a tu nombre», con el enlace a Stock en Local, y el listado del Administrador deja de contarlo entre los demorados.

**Qué habría que cambiar.**
`CU-PED-OPC` paso 6, opción 2: «el seguimiento del artículo continúa en el stock almacenado».

---

### B-18-004 · La solicitud de despacho es un concepto propio

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-STK-DES`, `CO-151`, `TransaccionPago`, `CU-CAJ-CIE`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 3)

**Qué apareció.**
`CO-151` «genera la solicitud de despacho» y, si el envío es pago, crea una `TransaccionPago`. Toda transacción pertenece hoy a un pedido, y un pedido es una venta.

**Qué dice la especificación.**
> «(a) Si el envío fue pago, se creó una TransaccionPago con estado = Aprobado por el costo de envío.» (`CO-151`, Postcondiciones)

Qué concepto agrupa la solicitud: `Nada`.

**Qué se hizo.**
La **Solicitud de despacho** agrupa los artículos pedidos juntos, la dirección copiada, el costo de envío y, si fue pago, su `TransaccionPago`. Una transacción es de un pedido o de una solicitud, nunca de los dos. El cierre de caja cuenta los cobros de envío como canal Online.

**Qué habría que cambiar.**
Área 5: `SolicitudDespacho` (dirección, costo de envío, fecha) con `ArticuloRetenido "1..*"` y `TransaccionPago "0..1"`.

---

### B-18-005 · Un envío pendiente nunca vuelve solo al stock

**Tipo:** Corrección · **Fecha:** 2026-10-14 · **Alcance:** RF-25 (5), `CO-154` A1
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 4)

**Qué apareció.**
Un artículo con despacho solicitado puede tener el envío pagado. RF-25 lo devuelve al stock si pasa la extensión de tres días sin despacho.

**Qué dice la especificación.**
> «Si transcurre el período de extensión sin confirmación de despacho, el sistema reintegra el artículo al stock general y notifica al Cliente.» (RF-25, punto 5)

> «Por cada artículo vencido en estado Pendiente de despacho: ArticuloRetenido.fecha de vencimiento pasó de su valor anterior a esa fecha más 3 días.» (`CO-154`)

**Qué se hizo.**
Cada vez que un artículo pendiente de despacho vence, se le extienden tres días y se alerta al Administrador. No vuelve al stock sin una acción del local.

**Qué habría que cambiar.**
RF-25 punto 5: quitar el reintegro tras la extensión.

---

### B-18-006 · El aviso de vencimiento sale con «N días o menos», una vez por fecha

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CO-154`, `CU-STK-VEN` paso 3
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 5 y 8)

**Qué apareció.**
El Temporizador puede no correr un día. Con «exactamente 7 días antes», el aviso de ese artículo no saldría nunca.

**Qué dice la especificación.**
> «Para cada artículo cuya fecha de vencimiento sea exactamente 7 días desde la fecha actual» (`CU-STK-VEN`, paso 3)

**Qué se hizo.**
Se avisa cuando faltan los días configurados o menos, una sola vez por artículo y por fecha de vencimiento: si el Administrador cambia el plazo, el aviso vuelve a salir para la fecha nueva. El ciclo sin artículos elegibles no deja entrada en el log, como dice `CO-154` (la ficha dice lo contrario).

**Qué habría que cambiar.**
`CU-STK-VEN` paso 3: «faltan N días o menos y todavía no se avisó para esa fecha». E2: quitar la entrada en el log.

---

### B-18-007 · Envío gratis desde el monto mínimo y despacho por solicitud

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-STK-DES` paso 2, `CO-151`, `CO-152`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 18, amb. 6 y 7)

**Qué apareció.**
La compra online da envío gratis «desde» el monto mínimo y `CU-STK-DES` dice «supera». Y una solicitud suele tener varios artículos que salen en el mismo paquete.

**Qué dice la especificación.**
> «Si el valor total supera el monto mínimo: el envío es gratuito.» (`CU-STK-DES`, paso 4)

**Qué se hizo.**
El envío es gratis desde el monto mínimo, igual que en la compra. La ficha de la solicitud confirma todos sus artículos pendientes de una vez; cada uno cumple las postcondiciones de `CO-152`.

**Qué habría que cambiar.**
`CU-STK-DES` paso 4: «alcanza o supera». `CU-STK-FIS`: el despacho de la solicitud entera.

---

### Nota de cierre · 2026-10-14

Los seis casos de uso están construidos. El artículo de despacho diferido queda retenido al llegar;
el Cliente lo ve en «Mi cuenta» y pide el envío, gratis o pago por la pasarela; el local lo despacha
o lo entrega en el mostrador; el Administrador ajusta el plazo y el Temporizador avisa y vence.
Queda: el origen «Reservado para cambio», que llega con el módulo 09, y la baja de cuenta del
Cliente (`CU-CLI-BAJ`), que ahora puede calcular su informe.

---

### B-18-008 · El stock en local tiene dos procedencias, y una vence con reembolso

**Tipo:** Corrección · **Fecha:** 2026-10-19 · **Alcance:** RF-25, `CO-154`, `CO-215`, `CO-217`, `CO-218`, `CO-227`, `ArticuloRetenido`, `CU-DEV-SOL`
**Estado:** Abierta

**Qué apareció.**
Con el retiro en el local (B-07-038), el stock en local deja de recibir sólo el artículo de
despacho diferido: también guarda las unidades de un pedido para retirar. El responsable decidió
que, a diferencia del despacho diferido, lo no retirado vuelve con su valor en puntos (D3).

**Qué dice la especificación.**
> «Cuando el Cliente seleccione la opción de despacho diferido ante un artículo demorado (opción 2
> de RF-15), el artículo queda retenido en el local a nombre del Cliente» (RF-25)

> «el sistema reintegra automáticamente el artículo al stock general sin reembolso» (RF-25 (4))

**Qué se hizo.**

- `ArticuloRetenido` gana la **procedencia**: Despacho diferido o Pedido para retirar. Las
  consultas la muestran («Pedido 000123 · pedido para retirar»). Un artículo demorado de un pedido
  para retirar entra con esa procedencia.
- Al vencer, un artículo de un pedido para retirar vuelve al stock **y se le acredita al Cliente
  el valor de la unidad en puntos**, con la regla de los demás reembolsos. El aviso previo y el del
  vencimiento lo dicen. El despacho diferido sigue volviendo sin reembolso.
- Lo retirado se puede reclamar (`CU-DEV-SOL`): una línea de un pedido para retirar admite el
  reclamo desde que se retiró, o se envió desde el stock en local, alguna de sus unidades, y el
  plazo corre desde ese momento. Antes de retirar nada, el reclamo informa que todavía no se
  retiró.

**Qué habría que cambiar.**
RF-25: los dos orígenes, y en (4) «sin reembolso» sólo para el despacho diferido; para el pedido
para retirar, «con el reembolso del valor en puntos». `CO-154`: la postcondición del reembolso.
`ArticuloRetenido`: el atributo «procedencia». `CU-DEV-SOL` y `CO-099`, precondiciones: el pedido
para retirar, con el plazo desde el retiro.

---

### B-18-009 · Todo lo guardado vence con reembolso, y el reemplazo de un cambio viaja sin costo

**Tipo:** Corrección · **Fecha:** 2026-10-19 · **Alcance:** RF-25 (4), `CO-154`, `CO-151`, `ArticuloRetenido`
**Estado:** Abierta

**Qué apareció.**
Un artículo pagado vencía con o sin reembolso según cómo había entrado al local (B-18-008), y el
reemplazo de un cambio por garantía necesitaba un camino para llegar al Cliente.

**Qué dice la especificación.**
> «reintegra automáticamente el artículo al stock general sin reembolso» (RF-25 (4))

> «No se acreditan puntos ni compensaciones por el vencimiento. Postcondición negativa explícita.»
> (`CO-154`)

**Qué se hizo** (plan 00, C1 y C2).
Las tres procedencias —despacho diferido, pedido para retirar y **cambio por garantía**, nueva—
vuelven al stock con el valor de la unidad en puntos, menos lo que había ganado. El reemplazo de un
cambio entra Disponible a nombre del Cliente; una solicitud de envío que sólo lleva reemplazos no
cobra envío. Se retira el estado «Reservado para cambio».

**Qué habría que cambiar.**
RF-25 (4) y `CO-154`: el reembolso en puntos para todas las procedencias, y quitar la
postcondición negativa. `CO-151`: el envío sin costo de los reemplazos. DME-12: la procedencia
Cambio, sin el estado «Reservado para cambio».
