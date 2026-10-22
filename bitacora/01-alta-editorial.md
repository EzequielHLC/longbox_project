# Bitácora — `01` Alta Editorial

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-01-001 · A qué caso de uso pertenecen los campos de demora del formulario de edición

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CAT-EDI`
**Estado:** Resuelta — sin enmienda al documento; corregido el código el 2026-09-22

**Qué apareció.**
El formulario de edición de un tomo (`ProductoEditorialForm`) enumera los campos que
deliberadamente **no** ofrece, y de tres de ellos —`demorado`, `fecha_estimada`, `nota_demora`—
dice que pertenecen al caso de uso de cancelación. En el modelo, esos mismos tres campos están
comentados como pertenecientes al caso de uso de demora, y son los que alimentan el indicador
«Demorado» del inventario. Los dos comentarios señalan casos de uso distintos para los mismos tres
campos, y los dos casos de uso están igualmente bloqueados por Pedidos, así que la contradicción
no tuvo consecuencia práctica hasta ahora.

La contradicción venía del esquema anterior de numeración y sobrevivió a la migración de códigos
del 2026-09-14, que tradujo cada referencia por su número y no la corrigió: el formulario quedó
diciendo `CU-ALT-CAN` y el modelo `CU-ALT-DEM`.

**Qué dice la especificación.**
> `CU-ALT-DEM` — «El sistema asigna el indicador "Demorado" al producto, transiciona los pedidos
> activos asociados a "Esperando Artículo Demorado" […]»

> `CU-ALT-CAN` — «Ante la cancelación definitiva de un título por parte de la editorial, el
> Administrador ejecuta la cancelación en lote de todas las reservas activas del producto.»

La ficha atribuye el indicador a `CU-ALT-DEM` sin ambigüedad. Lo que la especificación **no** dice
es cuál de los dos casos de uso es el que debe impedir que esos campos se editen desde la pantalla
de edición de producto, que es la afirmación que el formulario hace.

**Qué se hizo.**
Nada todavía. La migración de códigos preservó lo que cada comentario decía en vez de arreglarlo,
para que la discrepancia quedara visible en lugar de desaparecer dentro de una decisión tomada al
pasar. El comportamiento del sistema no cambió: los tres campos no se ofrecen en la edición, y no
hay pantalla que los escriba.

**Qué habría que cambiar.**
Confirmar que los tres campos pertenecen a `CU-ALT-DEM` y que la restricción del formulario de
edición se deriva de ese caso de uso. Con eso resuelto, el comentario de
`apps/catalog/forms.py` se corrige en una línea. Si en cambio la intención era otra —por ejemplo
que la cancelación en lote también los toque— eso sí cambia el alcance de `CU-ALT-CAN` y hay que
decirlo en la ficha.

---

### B-01-002 · La ingesta de correos se dispara a mano; el ciclo automático no existe

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-ALT-NOV`, `CO-016`
**Estado:** Resuelta — con enmienda pendiente al documento, decidida el 2026-09-22

**Qué apareció.**
El pipeline de novedades está construido de la cola en adelante: un correo que entra a
`CorreoProveedor` se aprueba, se extrae con el modelo de lenguaje y genera borradores. Lo que no
existe es el paso previo: nada lee la casilla. Los correos entran por dos comandos de gestión
—`manage.py ingerir_correos` y `manage.py extraer_novedades`— que una persona ejecuta.

Los dos comandos declaran en su docstring que no son un andamio descartable: cuando exista el
ciclo automático, va a invocar el mismo código.

**Qué dice la especificación.**
> `CO-016 ejecutarCicloMonitoreoCasilla` — operación disparada por el Temporizador del Sistema.

La especificación declara el ciclo. No dice nada sobre una vía manual de ingesta, ni sobre si esa
vía debe seguir existiendo una vez que el ciclo funcione.

**Qué se hizo.**
La ingesta quedó disponible como operación manual del Administrador sobre archivos `.eml`. El
resto del flujo —aprobación, extracción, generación de borradores— es idéntico venga el correo de
donde venga, así que el ciclo automático puede enchufarse sin tocar nada de lo que ya existe.

**Qué habría que cambiar.**
Decidir si la ingesta manual es permanente o transitoria. Si es permanente, `CU-ALT-NOV` necesita
declararla como flujo alternativo con el Administrador como actor primario, y probablemente un
contrato propio: hoy es una operación que modifica el estado del sistema y que ningún contrato
declara. Si es transitoria, alcanza con dejarlo dicho.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-01-001 · Resolución de B-01-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Los tres campos —`demorado`, `fecha_estimada`, `nota_demora`— pertenecen a `CU-ALT-DEM`. La ficha
ya lo dice sin ambigüedad y no hay nada que enmendar: el que estaba mal era el comentario del
formulario, que quedó diciendo `CU-ALT-CAN` al migrar la numeración.

La restricción del formulario de edición se deriva de `CU-ALT-DEM`: es ese caso de uso el que
escribe esos campos, y por eso `CU-CAT-EDI` no los ofrece. `CU-ALT-CAN` no los toca.

**Qué se hizo.**
`apps/catalog/forms.py`, docstring de `ProductoEditorialForm`: la referencia pasa de `CU-ALT-CAN`
a `CU-ALT-DEM`. El comportamiento no cambia —los campos siguen sin ofrecerse en la edición— y
ahora el formulario y el modelo dicen lo mismo.

---

### R-01-002 · Resolución de B-01-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** pendiente

**Qué se decidió.**
La carga de correos desde archivos `.eml` es una **herramienta de operación**, no un caso de uso.
No necesita ficha, no necesita contrato propio y no es la vía manual permanente de un flujo
especificado: es una utilidad de consola para operar el sistema.

`CO-016 ejecutarCicloMonitoreoCasilla` **sigue pendiente**. La decisión no lo cubre ni lo
reemplaza: el ciclo automático es lo que la especificación declara y lo que hay que construir. Lo
que queda resuelto es que los comandos de consola que hoy ocupan su lugar no son deuda de
especificación.

**Enmienda pendiente.**
Un **límite nuevo del sistema** que declare fuera del modelo de casos de uso a las tareas de
consola:

- el respaldo de la base (`respaldar_base`);
- la sincronización de los catálogos geográficos y de países (`sincronizar_georef`,
  `sincronizar_paises`);
- la carga de correos desde `.eml` (`ingerir_correos`, `extraer_novedades`);
- el alta de la primera cuenta Administrador en una instalación nueva.

Mientras esa enmienda no llegue a `.contexto-ia/`, esta resolución manda sobre el texto volcado.
Con ella, las cuatro filas correspondientes salen de «Código sin contrato» en `docs/DEUDA.md`: no
son contratos que falten escribir sino comportamiento deliberadamente fuera del alcance funcional.

**Qué se hizo.**
Nada en el código de la ingesta. La cuarta tarea de la lista —el alta del primer Administrador— se
construye en el bloque 2 como consecuencia del retiro del admin de Django, y queda registrada en
`bitacora/13-gestion-de-usuarios.md`.

---

### B-01-003 · Un producto admite imágenes adicionales además de su portada

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `Producto`, `CU-CAT-ALT`, `CU-CAT-EDI`, `CU-CAT-INV`, RNF-05
**Estado:** Abierta — pedido explícito del responsable el 2026-10-02

**Qué apareció.**
El responsable pidió poder subir más de una imagen por producto.

**Qué dice la especificación.**
> «imagen : archivo «marcador "imagen pendiente" si falta»» (`MODELO_DE_DOMINIO.md`, `Producto`)

RNF-05 habla de «portadas, imágenes de producto» en plural, sin declarar cuántas.

**Qué se hizo.**
La portada sigue siendo **la** imagen del producto, con su marcador «imagen pendiente»: ningún
contrato cambia. Se suma una galería de hasta 8 imágenes adicionales, que se cargan en el alta no
editorial y en la edición, se pueden quitar de a una, se procesan con RNF-05 (WebP, 800 px) y se
ven en la ficha. Agregarlas o quitarlas queda en el historial del producto. La carga de lotes no
las ofrece.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 3: agregar `ImagenProducto` (imagen, posición) con `Producto` 1 —
0..8. `CO-030`, parámetros: «imágenes adicionales?».

---

### B-01-004 · El historial del producto incluye su alta por lote y todo lo que la edición cambia

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CAT-INV` paso 6, `CO-030`, `CO-163`
**Estado:** Abierta

**Qué apareció.**
El historial de un tomo cargado por lote empezaba en su primera modificación: el alta se audita
sobre el lote, una entrada por lote. Además, una edición que sólo cambiaba etiquetas, sinopsis,
portada o fecha de llegada se guardaba pero no dejaba entrada, y la pantalla decía «No había
cambios para guardar».

**Qué dice la especificación.**
> «Se creó una entrada en el registro de auditoría con acción «Modificación de producto», el actor y
> el momento de la operación» (`CO-030`, Postcondiciones)

Sobre qué campos se registran y qué muestra el historial de la ficha: `Nada`.

**Qué se hizo.**
La ficha suma al historial la entrada del alta del lote del que salió el producto. La edición
registra también etiquetas, sinopsis (por su largo, comparando el texto entero), portada, fecha de
llegada e imágenes adicionales. Los valores del detalle van entre comillas angulares, como el
resto del log.

**Qué habría que cambiar.**
`CU-CAT-INV` paso 6: el historial de la ficha incluye el alta del lote de origen.

---

### B-01-005 · Los desplegables de formato muestran las medidas

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-ALT-NAC`, `CU-ALT-IMP`, `CU-CAT-EDI`, `CU-ALT-REV`, `CU-PVP-TBA`, `CU-CFG-TPM`
**Estado:** Abierta — pedido del responsable el 2026-10-02

**Qué apareció.**
Elegir un formato por su nombre obliga a recordar qué tamaño era.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Todo desplegable o lista de formatos los ofrece como «B6 · 12,8 × 18,2 cm» cuando el formato tiene
medidas cargadas.

**Qué habría que cambiar.**
Nada.

---

### B-01-006 · El lote que se confirma es la fecha de llegada de una editorial

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CU-ALT-TRA` pasos 2 a 5, `CO-013`
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 01, amb. 1)

**Qué apareció.**
`CO-013` recibe «el lote», pero las pre-ventas entran por la carga de lotes o por los borradores de
los correos de proveedores, y muchas no quedan atadas a un `LoteAlta`.

**Qué dice la especificación.**
> «confirmarIngresoDeLote(lote, unidadesPorProducto, productosFaltantes)» (`CO-013`)

Qué es un lote para esta operación: `Nada`.

**Qué se hizo.**
La pantalla «Pre-ventas por llegar» agrupa todas las pre-ventas por fecha de llegada vigente (la
estimada si hay demora, si no la programada) y por editorial. Cada grupo es un lote: el
Administrador carga las unidades recibidas de cada producto y lo que queda sin unidades es
faltante (A1).

**Qué habría que cambiar.**
`CO-013`: «el lote es el conjunto de pre-ventas de una editorial con la misma fecha de llegada».

---

### B-01-007 · Lo que llega cubre primero las reservas

**Tipo:** Corrección · **Fecha:** 2026-10-12 · **Alcance:** `CO-013`, `CU-ALT-TRA` paso 6
**Estado:** Abierta — decidida por el responsable el 2026-10-12

**Qué apareció.**
La compra de una pre-venta no descuenta stock. Si al llegar se suman todas las unidades, las ya
reservadas quedan a la venta otra vez y la tienda o el mostrador las venden dos veces.

**Qué dice la especificación.**
> «p.estado pasó de Pre-venta a Activo. p.stock pasó de su valor anterior a ese valor más las
> unidades recibidas» (`CO-013`, Postcondiciones)

**Qué se hizo.**
Las unidades recibidas cubren las reservas en el orden en que se compraron, línea entera por
línea entera; el orden no se saltea. Lo que sobra es el stock a la venta. Si alcanza para todas,
el producto pasa a Activo (o a Agotado si no sobra nada). Si no alcanza, el producto sigue en
Pre-venta, las reservas sin cubrir quedan demoradas (con la cascada de `CO-015` si el producto no
lo estaba) y las unidades que sobraron quedan en el stock del producto para la próxima llegada.

**Qué habría que cambiar.**
`CO-013` Postcondiciones: «p.stock pasó a las unidades recibidas menos las reservadas que
cubren. p.estado pasó a Activo sólo si cubrieron todas las reservas».

---

### B-01-008 · Un faltante sólo se demora si su fecha ya llegó

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CU-ALT-TRA` A1, `CO-013`
**Estado:** Abierta

**Qué apareció.**
Un lote puede llegar antes de su fecha. Lo que no vino con él todavía no está atrasado.

**Qué dice la especificación.**
> «los productos no incluidos en el lote recibido son marcados automáticamente como demorados»
> (`CU-ALT-TRA`, A1)

Qué pasa si la fecha de llegada todavía no llegó: `Nada`.

**Qué se hizo.**
Los faltantes se demoran sólo si su fecha de llegada es hoy o ya pasó. Si es futura, siguen en
Pre-venta sin cambios. Un faltante que ya estaba demorado tampoco cambia: la cascada no se repite.

**Qué habría que cambiar.**
`CU-ALT-TRA` A1: «… cuya fecha de llegada ya se cumplió».

---

### B-01-009 · Avisos al Administrador y escalado sin período de gracia

**Tipo:** Desvío · **Fecha:** 2026-10-12 · **Alcance:** `CO-011`, `CO-012`, `CU-ALT-TRA` E2
**Estado:** Abierta — consultado y aprobado por el responsable el 2026-10-12 (plan 01, amb. 2 y 3)

**Qué apareció.**
El Temporizador corre una vez por día. Un escalado «a las 23:59» y un período de gracia
configurable exigen un reloj que no existe.

**Qué dice la especificación.**
> «El período de gracia es configurable, con valor por defecto las 23:59 del día de llegada
> programada» (`CO-012`, Notas)

**Qué se hizo.**
El escalado sale en la primera corrida posterior al día de llegada y se repite una vez por día
mientras el producto siga sin resolver. El período de gracia no es parámetro: `CU-CFG-PAR` no lo
declara. Los avisos van por correo a cada Administrador activo y se ven también en el bloque
«Pre-ventas por llegar» del panel. El sistema recuerda qué avisó: correr el ciclo dos veces el
mismo día no repite ningún correo.

**Qué habría que cambiar.**
`CO-012` Notas: quitar el período de gracia configurable.

---

### B-01-010 · Cómo se calcula el reembolso en puntos

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CO-026`, `CO-027`, `CO-098`
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 01, amb. 4 y 5)

**Qué apareció.**
Una reserva se puede haber pagado en dinero o con puntos, y convertir pesos a puntos deja resto.

**Qué dice la especificación.**
> «la suma de los valores abonados por cada reserva activa» (`CU-ALT-CAN`, paso 2)

Cómo se convierte ni cómo se redondea: `Nada`.

**Qué se hizo.**
Lo pagado en dinero vuelve convertido a puntos con el valor del punto vigente, redondeado hacia
arriba. Lo pagado con puntos vuelve con los mismos puntos. Cada cliente recibe un solo lote por
cancelación, con todas sus reservas del título. Las reservas que ya estaban demoradas también se
cancelan y se reembolsan: siguen siendo reservas del título. Los puntos que el cliente ganó al
comprar no se descuentan.

**Qué habría que cambiar.**
`CO-026` Notas y `CO-027` Postcondiciones: la regla de conversión y de redondeo.

---

### B-01-011 · El ingreso se revisa antes de confirmarse

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CU-ALT-TRA` pasos 4 a 6, `CO-013`
**Estado:** Abierta

**Qué apareció.**
Confirmar un lote dispara avisos a clientes y demoras que no se deshacen. Un número mal tipeado o
un casillero vacío por olvido demora un título que sí llegó.

**Qué dice la especificación.**
> «El Administrador recibe el lote físico, verifica su contenido y confirma el ingreso de stock en
> el sistema, indicando las unidades recibidas por producto.» (`CU-ALT-TRA`, paso 4)

Si hay un paso de revisión antes de ejecutar: `Nada`.

**Qué se hizo.**
Antes de ejecutar, la pantalla muestra qué va a pasar con cada producto: pasa a la venta (con
cuántas unidades libres), ingreso parcial, se demora o sin cambios, y cuántas reservas cubre. El
Administrador confirma o vuelve. No registra nada hasta confirmar.

**Qué habría que cambiar.**
`CU-ALT-TRA` paso 5: «el sistema presenta el resumen de lo que va a ejecutar y el Administrador lo
confirma».

---

### Nota de cierre de tanda · 2026-10-12

El ciclo de la pre-venta está completo: avisos y escalado, confirmación del ingreso, demora y
cancelación por la editorial. Queda en el módulo: las pruebas de contrato de las altas de lote
(`CO-001` a `CO-010`), el monitoreo automático de la casilla (`CO-016`) y el aviso a suscriptores
de reposición (`CO-077`, módulo 05).

---

### B-01-012 · El Temporizador lee la casilla de novedades

**Tipo:** Agregado · **Fecha:** 2026-10-19 · **Alcance:** `CU-ALT-NOV`, `CO-016`, `CU-CFG-PAR` (Proveedores)
**Estado:** Abierta

**Qué apareció.**
`CO-016` faltaba (B-01-002): el alcance promete la extracción asistida de novedades y los correos
sólo entraban a mano.

**Qué dice la especificación.**
> `CO-016 ejecutarCicloMonitoreoCasilla` — operación disparada por el Temporizador del Sistema.

Nada sobre cómo se conecta a la casilla ni con qué credenciales.

**Qué se hizo** (plan 00, A1).
El Temporizador lee la casilla por IMAP con SSL, con las credenciales del entorno del servidor (no
de la base). Toma los mensajes sin leer, los ingiere con el mismo servicio de la carga manual
(idempotente por identificador, I-16), los marca leídos y avisa al Administrador de lo que entró a
la cola. Respeta «frecuencia de monitoreo de la casilla (horas)», parámetro nuevo de la sección
Proveedores (24 por defecto). Sin conexión (E3), avisa y se reintenta en el próximo ciclo. La
conexión tiene una puerta propia que las pruebas cortan, como la red. La carga manual de `.eml`
sigue disponible.

**Qué habría que cambiar.**
`CO-016`: dónde se configuran las credenciales. `CU-CFG-PAR` y `ConfiguracionSistema`: la
frecuencia, que la ficha ya nombra.

---

### B-01-013 · El lote nacional sobrescribía el precio de la tabla sin advertir ni confirmar

**Tipo:** Corrección · **Fecha:** 2026-10-22 · **Alcance:** `CU-ALT-NAC` A3, `CO-004`, `CO-005`
**Estado:** Abierta — el código ya cumple la ficha; queda la consulta sobre la auditoría

**Qué apareció.**
Al escribir las pruebas de contrato del alta de lotes (V1 del plan 00): en un lote nacional, un
precio distinto del de la tabla se guardaba sin advertencia ni confirmación. El importado sí las
pedía.

**Qué dice la especificación.**
> «el sistema muestra la advertencia: Este producto está vinculado a la combinación seleccionada de
> la tabla de precios de referencia. Modificar el precio individualmente romperá ese vínculo: el
> producto dejará de actualizarse automáticamente ante cambios de precio en CU-PVP-TBM. El
> Administrador confirma la edición explícitamente. (…) La confirmación se valida en el servidor y
> no únicamente en el formulario.» (`CU-ALT-NAC`, A3)

**Qué se hizo.**
El lote nacional muestra esa advertencia y exige la confirmación, también en el servidor: sin ella
no se guarda nada. Del texto cambia sólo el final, «ante cambios de precio en la tabla de precios
de referencia», porque la voz del sistema no muestra códigos de caso de uso. El aviso de un ítem
repetido dentro del lote ahora dice con qué ítem choca y si es por ISBN o por la combinación, como
pide la excepción de `CO-003`.

**Para consultar.** `CO-005` pide una entrada de auditoría «Modificación de producto»; `CO-006`
pide **una única** entrada consolidada por lote. En un lote se hace lo segundo: la entrada del lote
dice cuántos ítems quedaron con precio a mano. Si el responsable prefiere otra cosa, es un cambio
chico.

**Qué habría que cambiar.**
`CU-ALT-NAC` A3: el texto de la advertencia, sin el código. `CO-005`, postcondición de auditoría:
«en un alta por lote, la entrada consolidada de `CO-006`».

---

### B-01-014 · Un precio fijado a mano lo pisaba un cambio de la tabla de referencia

**Tipo:** Corrección · **Fecha:** 2026-10-22 · **Alcance:** `CO-005`, `CO-006`, `CO-048`, `CU-CAT-EDI` A1
**Estado:** Resuelta el 2026-10-22

**Qué apareció.**
Un producto con precio confirmado a mano —en el alta por lote, en la edición o al confirmar un
borrador— conservaba la asociación con su combinación de la tabla. Al modificar el precio de esa
combinación (`CO-048`), la propagación lo alcanzaba y le pisaba el precio: un tomo a $9.900 pasaba a
$12.000. También contaba como «vinculado» en el informe de baja de la combinación.

**Qué dice la especificación.**
> «(b) Se rompió la asociación ProductoEditorial → TablaPrecioReferencia (precio_referencia), si
> existía.» (`CO-005`) · «p → TablaPrecioReferencia cuando el precio provino de la tabla y no fue
> sobrescrito» (`CO-006`)

**Qué se hizo.**
Los tres caminos que fijan un precio a mano rompen la asociación; la propagación excluye además los
precios a mano; y una restricción en la base impide que un producto tenga precio a mano y
asociación a la vez. Una migración limpió los que hubiera (en la base de desarrollo, ninguno).
Restaurar el precio calculado (`CO-031`) vuelve a asociarlo, como ya hacía.

**Qué habría que cambiar.**
`Nada`: la especificación ya lo decía.
