> **Tipo: Fotografía.** Tomada el **2026-10-22**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada. La escala de
> estados y los umbrales de las siete puertas son reglas y viven en `CLAUDE.md`.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Del 2026-10-22: **todos los casos de uso construidos tienen sus contratos verificados** (V1 y V2
del plan 00). Escribir las pruebas desde los contratos encontró lo que faltaba y se completó:

- **La baja de producto resuelve lo que tenía atado** (B-02-006), y la reactivación registra el
  estado anterior y el nuevo.
- **El lote nacional exige confirmar el precio a mano** en el servidor (B-01-013), y un precio a mano
  ya no lo pisa la tabla de referencia (B-01-014).
- **La reactivación de proveedor es una revisión** con los datos corregibles, y la propuesta de
  restock marca al proveedor inactivo (B-04-009). La ficha muestra el historial de pedidos
  (B-04-008).
- **El diagnóstico del modelo queda en el log** y la disponibilidad se comprueba con un botón
  propio (B-17-018).
- **La revisión de borradores**: completar un incompleto lo pasa a Pendiente, y los pedidos del
  cierre de sesión dejan su entrada como cualquier pedido a proveedor (`CO-074`).
- **El calendario de pre-ventas** en el panel (B-00-025).

Quedan pendientes `CU-CLI-BAJ` y `CU-REP-GEN`, que esperan su plan.

Del 2026-10-19, antes: decimoquinta fotografía. **Revisión funcional y recorte para el cierre** (plan 00): se corrigió lo
que hacía aguas, se completó lo que el alcance promete y se descartó el resto con su
justificación (`docs/DEUDA.md`, «Recorte para el cierre»).

- **Devoluciones** según la ley y sin comprometer al negocio (B-09-008): arrepentimiento por un
  botón público sin registración, con reembolso por el medio de pago al recibir el artículo;
  garantía con su propio plazo y cambio por un tomo de la misma editorial y formato.
- **Todo reembolso descuenta los puntos ganados** con la compra (B-10-012), y todo lo guardado en
  el local vence con su valor en puntos (B-18-009).
- **El Temporizador completa los procesos automáticos del alcance**: lee la casilla de novedades
  (`CO-016`, B-01-012), sincroniza la cotización (`CO-155`, B-03-013) y descarta los cobros
  abandonados (B-07-039).
- **Parámetros completo**, con la sección Seguridad (B-12-004).
- Se cierran los parciales que ya tenían el código: `CU-TDA-CAT` y grupos y etiquetas.

Del 2026-10-19, antes:

- **Retiro en el local** (B-07-038): en el checkout, el Cliente con cuenta elige «Retiro en el
  local», sin dirección ni costo de envío. El pedido se arma como cualquiera y pasa de Armado a
  **En el local**: cada unidad entra a su stock en local y se le avisa que está listo. El mostrador
  lo entrega entero verificando al titular una vez. Si no lo retira en el plazo, vuelve al stock
  con su valor en puntos (B-18-008). Lo retirado admite reclamo, con el plazo desde el retiro.

Del 2026-10-17:

- **Caducidad** (`CU-PTS-CAD`): el Temporizador vence cada día los lotes cuya fecha llegó, deja un
  débito «Caducidad» en el historial y le avisa al Cliente con un solo correo (B-10-006). Los
  puntos de un canje con el pago pendiente no vencen (B-10-005). **A pedido del responsable**, un
  aviso unos días antes («aviso previo a la caducidad», 3 por defecto, en Parámetros) anima a
  usarlos. «Mis puntos» dice hasta qué día se pueden usar.
- **Ajuste manual** (`CU-PTS-ADM`): desde la ficha del Cliente (B-10-011), el Administrador ve
  sus puntos y lo comprometido en un canje, y acredita o debita con motivo; el débito informa el
  máximo y nunca toca lo comprometido.

Del 2026-10-16:

- **Devoluciones** (`CU-DEV-*`): desde el detalle de un pedido despachado, dentro del plazo, el
  Cliente elige el artículo, el motivo y adjunta de 1 a 5 fotos, que se guardan fuera de la carpeta
  pública (B-09-006). Un caso por línea, en cualquier estado (I-19). El Administrador recibe el
  aviso, revisa el caso con sus fotos y lo resuelve con un cambio (descuenta una unidad del
  reemplazo y deja el artículo reclamado pendiente de retiro), con el reembolso en puntos de una
  unidad (B-09-003, B-09-004) o lo rechaza con motivo. El Cliente sigue su reclamo al lado de la
  línea, en «Mi cuenta».
- **Parámetros** gana el plazo máximo de devolución (sección Comercial), con el piso legal de 10
  días rechazado aparte de los demás campos (`CO-130` E1) y como restricción de la base.
- Los diagramas de estados DME-12 y DME-16 están desactualizados: mandan la ficha y `CO-100`
  (R-09-001).

**Por qué no quedan parciales.** `CO-077` ya existe: `CO-013` avisa con lo que sobra al llegar una
pre-venta. Las altas de lote (`CU-ALT-NAC`, `IMP`, `REV`) crean productos nuevos, que no pueden
tener suscriptores (B-05-001): su parcialidad viene de otras operaciones.

| | |
| --- | --- |
| Casos de uso especificados | 103 |
| Verificados | 101 |
| Construidos, sin verificar | 0 |
| Parciales | 0 |
| En curso | 0 |
| Pendientes | 2 |
| Bloqueados | 0 |

Contratos de operación especificados: **219**. Con prueba y verificados: **215**. Sin prueba:
**4**, los de `CU-CLI-BAJ` (`CO-112`, `CO-113`) y `CU-REP-GEN` (`CO-128`, `CO-204`). El detalle por
contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md), regenerado hoy.

### Cómo leer la columna «Contratos»

Dice *cuántos de los contratos que el caso de uso referencia tienen una prueba que verifica todas
sus postcondiciones*, sobre el total que referencia. El total sale de las Referencias Cruzadas de
cada contrato. Un contrato compartido se cuenta una vez por cada caso de uso que lo referencia.
En un caso de uso sólo cuenta como verificado si la prueba lo ejerce **en ese caso de uso**.
`CO-156 cancelarOperacion` lo referencian ahora 22 casos de uso y su prueba lo ejerce en tres
(`CU-USR-BAJ`, `CU-USR-REA`, `CU-USR-ELI`).

---

## Por módulo

### `01` Alta Editorial

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-ALT-NAC` | Verificado | 9 / 10 | `AltaLoteNacionalView`, `catalog/services.py`, `catalog/precios.py`. **Todos sus contratos aplicables verificados** (`CO-001` a `CO-006`, V2 del plan 00): el precio a mano exige confirmación en el servidor y rompe el vínculo con la tabla (B-01-013, B-01-014). Alta al vuelo de editorial, tipo y formato (`CO-137`, `CO-141`, `CO-144`; B-17-009). `CO-077` no aplica: un producto nuevo no tiene suscriptores (B-05-001). |
| `CU-ALT-IMP` | Verificado | 12 / 13 | `AltaLoteImportadoView`, calculadora de envío y CRE en `LoteAlta`. **Todos sus contratos aplicables verificados** (`CO-001`, `CO-002`, `CO-005` a `CO-010`, V2 del plan 00). Alta al vuelo de los tres catálogos, como `CU-ALT-NAC`; `CO-031` desde `CU-CAT-EDI` A2. `CO-077` no aplica (B-05-001). |
| `CU-ALT-NOV` | Verificado | 3 / 3 | **Todos sus contratos verificados.** `CO-017` y `CO-019` desde la ficha del correo; **`CO-016`, el monitoreo de la casilla, en el Temporizador** por IMAP, con la frecuencia de Parámetros, E1, E3 sin conexión e idempotencia (B-01-012). Plan 00, A1. |
| `CU-ALT-REV` | Verificado | 9 / 10 | `BorradorListaView`, `BorradorDetalleView`, `ConfirmarEnLoteView`, `CerrarSesionRevisionView`, `catalog/revisiones.py`. **Todos sus contratos aplicables verificados.** Completar un borrador incompleto lo pasa a Pendiente (`CO-020`); el cierre encadena `CO-074` con su entrada por proveedor (`CO-025`); la colisión dice su criterio (`CO-022` E7). `CO-077` no aplica (B-05-001). |
| `CU-ALT-DEM` | Verificado | 3 / 3 | `apps/pedidos/preventa.py`, `views_preventa.py`. **Todos sus contratos verificados**: informe de impacto (A3), E1 con lo ingresado conservado, la cascada a pedidos con la ventana de decisión (B-08-004) y el correo con acceso directo, E2 con un pedido que falla, y volver sin registrar (`CO-156`). Desde la ficha del producto. Plan 01. |
| `CU-ALT-TRA` | Verificado | 5 / 5 | **Todos sus contratos verificados.** «Pre-ventas por llegar» (B-01-006) con revisión previa (B-01-011); `CO-013` cubre reservas en orden (B-01-007), demora los faltantes vencidos (B-01-008), avisa a los suscriptores con lo que sobra (B-05-001) y deja retenido lo de despacho diferido (B-18-002); `CO-011` y `CO-012` en el Temporizador (B-01-009). Plan 01. |
| `CU-ALT-CAN` | Verificado | 3 / 3 | **Todos sus contratos verificados**: informe por cliente con los puntos (B-01-010), atomicidad total (E1), un lote por cliente, el envío de los pedidos que se quedan vacíos (B-08-008) y volver sin efecto (`CO-156`). Plan 01. |

### `02` Catálogo

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAT-ALT` | Verificado | 2 / 2 | `ProductoNoEditorialAltaView` y `DuplicadosNoEditorialesView`. **Todos sus contratos verificados.** |
| `CU-CAT-EDI` | Verificado | 5 / 5 | `ProductoEdicionView`. **Todos sus contratos verificados.** La pantalla declara los inmutables: código, rubro y costo en origen del importado (`CO-161`). `CO-031` desde la ficha y desde la edición (B-03-005); el valor actual de editorial, tipo, formato y etiquetas aunque esté dado de baja (B-17-007). |
| `CU-CAT-BAJ` | Verificado | 3 / 3 | `ProductoBajaView` y `services.confirmar_baja_de_producto`. **Todos sus contratos verificados.** El informe calcula las cuatro categorías y la baja las resuelve: suscripciones canceladas, oferta exclusiva eliminada, carritos avisados, pedidos intactos (B-02-006). |
| `CU-CAT-REA` | Verificado | 3 / 3 | `ProductoReactivarView`. **Todos sus contratos verificados.** Rechaza el cancelado por editorial (E1), avisa la fecha de llegada vencida (E2) y registra el estado anterior y el nuevo. |
| `CU-CAT-INV` | Verificado | 3 / 3 | **Todos sus contratos verificados.** Exportación CSV del listado filtrado, sólo Administrador y auditada (`CO-037`); filtro por editorial y etiquetas inactivas marcadas (`CO-162`); ficha por rol que no dibuja lo que el Cajero no ve e indicadores «No disponible» (`CO-163`). |
| `CU-CAT-GRC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `GrupoListaView`: activos y dados de baja, filtro por estado, cantidad de etiquetas. |
| `CU-CAT-GRA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Nace activo; la colisión enlaza el grupo existente con su estado. |
| `CU-CAT-GRM` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Corrige y reactiva; la reactivación no alcanza a las etiquetas. Los filtros del catálogo público dejan de ofrecer y vuelven a ofrecer lo que se da de baja o se reactiva (B-02-004; plan 00, A6). |
| `CU-CAT-GRB` | Verificado | 4 / 4 | **Todos sus contratos verificados.** Par informe y confirmación; la baja alcanza a cada etiqueta del grupo. Los filtros del catálogo público dejan de ofrecer y vuelven a ofrecer lo que se da de baja o se reactiva (B-02-004; plan 00, A6). |
| `CU-CAT-ETC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `EtiquetasDeGrupoView`: las etiquetas de un grupo, de a 50 (B-02-003), con búsqueda y filtro por estado, y el estado del grupo. |
| `CU-CAT-ETA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Unicidad dentro del grupo, colisión con enlace, sólo en grupos activos. |
| `CU-CAT-ETM` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Corrige, mueve de grupo y reactiva; rechaza reactivar en un grupo dado de baja (E3). Los filtros del catálogo público dejan de ofrecer y vuelven a ofrecer lo que se da de baja o se reactiva (B-02-004; plan 00, A6). |
| `CU-CAT-ETB` | Verificado | 4 / 4 | **Todos sus contratos verificados.** Par informe y confirmación; la edición del producto la sigue presentando marcada. Los filtros del catálogo público dejan de ofrecer y vuelven a ofrecer lo que se da de baja o se reactiva (B-02-004; plan 00, A6). |

### `03` Pricing

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PVP-TBC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `PrecioListaView`, pantalla propia con filtros combinables por editorial, tipo y formato. |
| `CU-PVP-TBA` | Verificado | 3 / 3 | **Todos sus contratos verificados.** Exige rubro editorial, clasificación por formato, formato aplicable y entradas activas; la colisión enlaza la fila existente. |
| `CU-PVP-TBM` | Verificado | 4 / 4 | Informe de alcance y confirmación que propaga a los vinculados, salvo cancelados y precio a mano, **y a las líneas de carrito de esos productos** (R-03-001, B-07-003). |
| `CU-PVP-TBB` | Verificado | 5 / 5 | **Todos sus contratos verificados.** Informe de vinculados y baja que desvincula conservando precio y marca; se vuelven a vincular con `CO-031`. |
| `CU-PVP-MAR` | Verificado | 4 / 4 | `MargenView`: valor vigente en porcentaje, simulación y recálculo desde el precio base con `Decimal` exacto, **también en las líneas de carrito** (R-03-001). Sin importados el cambio no se ofrece (B-03-003, C-19). |
| `CU-PVP-ALT` | Verificado | 2 / 2 | `apps/catalog/ofertas.py`. Activa o Programada según la fecha; solapamiento con bloqueo sobre el alcance (E2); tope de $1 con confirmación (E3, `CO-055`); aviso de tipo vacío (A1). La oferta cambia el precio visible, no el guardado (B-03-007, B-03-008). |
| `CU-PVP-EDI` | Verificado | 2 / 2 | Registra cada campo anterior y nuevo; reducir el alcance restaura a los excluidos (A1); también pide confirmar el tope (B-03-010). |
| `CU-PVP-BAJ` | Verificado | 3 / 3 | Informe con productos con descuento activo y carritos (`CO-057`), confirmación terminal (`CO-058`) y cancelar sin efecto (`CO-156`). Una vencida informa que ya expiró (E1). |
| `CU-PVP-CON` | Verificado | 2 / 2 | `OfertaListaView`, `OfertaFichaView`. Estado según las fechas aunque el Temporizador no haya corrido (B-03-007). La ficha marca los productos «tapados» por su oferta individual y ofrece la baja también en Programada (B-03-009). Plan 03, segunda parte. |

### `04` Proveedores

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PRV-ALT` | Verificado | 2 / 2 | `ProveedorAltaView`, con alta de editorial al vuelo. **Todos sus contratos verificados.** |
| `CU-PRV-EDI` | Verificado | 3 / 3 | `ProveedorEdicionView`, con confirmación al cambiar el correo comercial. **Todos sus contratos verificados.** |
| `CU-PRV-CON` | Verificado | 2 / 2 | `ProveedorListaView` y `ProveedorDetalleView`. **Todos sus contratos verificados.** La ficha muestra el historial de pedidos al proveedor (B-04-008). |
| `CU-PRV-REA` | Verificado | 3 / 3 | `ProveedorReactivarView`. **Todos sus contratos verificados.** La reactivación es la revisión: datos corregibles con el correo destacado y el procesamiento de novedades declarado (B-04-009). |
| `CU-PRV-BAJ` | Verificado | 3 / 3 | `ProveedorBajaView` con informe de impacto (B-04-007). **Todos sus contratos verificados.** La propuesta de restock marca «Proveedor inactivo» (B-04-009). |
| `CU-PRV-COL` | Verificado | 5 / 5 | **Todos sus contratos verificados.** Aprobar (`AprobarCorreoView`) y reprocesar (`ReprocesarCorreoView`) desde la ficha, con la transición condicionada de E1 y la corrección de E4 a favor del contrato (B-04-004). |

### `05` Restock

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-RST-PED` | Verificado | 3 / 3 | `suppliers/pedidos.py`: tres intentos y su registro (`CO-074`), E2 sin correo. Lo invocan `CU-ALT-REV` y `CU-RST-APR`. Plan 05. |
| `CU-RST-PRO` | Verificado | 2 / 2 | **Todos sus contratos verificados**: ciclo diario con la ventana de la semana (B-05-004), cantidad sugerida, grupos por proveedor (B-05-003), E1 a E4, disparo manual que omite el ciclo; I-21 en la base y la carrera entre el ciclo y el botón. Plan 05. |
| `CU-RST-APR` | Verificado | 8 / 8 | **Todos sus contratos verificados**: propuesta por proveedor, ajustar, quitar, agregar al grupo correcto, despachar con correo (E2 vuelve a Pendiente), descartar con motivo y cierre automático; dos administradores a la vez. Plan 05. |
| `CU-RST-SUS` | Verificado | 2 / 2 | `apps/restock`. **Todos sus contratos verificados**: aviso desde la ficha de un agotado (B-05-002), E1, E2, cancelar, sin auditoría; I-22 en la base y dos clics a la vez. Plan 05. |
| `CU-RST-NOT` | Verificado | 1 / 1 | **Verificado**: FIFO con `min(N, M)` en cada suba de stock (B-05-001), tres intentos y turno conservado (B-05-005), E2 sin ceder el cupo. Plan 05. |

### `06` Ventas Presenciales

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-VTA-REG` | Verificado | 7 / 7 | `apps/ventas`. **Todos sus contratos verificados**: ticket en sesión (B-06-002), alta por código exacto o título (B-06-003), vínculo por código de cliente o correo (B-06-001), canje por ítem, cobro con bloqueo de stock y concurrencia contra la tienda, comprobante imprimible (B-06-004). Cajero y Administrador. Plan 06. |

### `07` Tienda Online

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | Verificado | 2 / 2 | **Todos sus contratos verificados** (`CO-176`, `CO-177`). Catálogo público con filtros de varios valores, orden elegible, ficha con galería, precio con oferta y «Avisarme cuando haya stock» (`CU-RST-SUS`). Plan 07; cerrado en el plan 00, A6. |
| `CU-TDA-CRC` | Verificado | 3 / 3 | `tienda/carrito.html`, `apps/tienda/carrito.py`. Líneas con el precio visible de hoy, aviso de precio cambiado con el importe anterior (B-07-003), disponibilidad derivada en tres valores (B-07-004) y total. «Ir a pagar» lleva al checkout; al invitado le ofrece iniciar sesión o comprar como invitado (B-07-006 resuelta). |
| `CU-TDA-CRA` | Verificado | 1 / 1 | Desde la ficha, con cantidad. Tope en el stock con aviso (E1); la Pre-venta reserva sin tope (A1). El personal no tiene carrito (B-07-005). |
| `CU-TDA-CRM` | Verificado | 1 / 1 | Tope en el stock (E1), mínimo uno (E2), sin tope en Pre-venta. La línea de otro carrito responde 404. |
| `CU-TDA-CRB` | Verificado | 1 / 1 | Sin confirmación. La línea de otro carrito responde 404. |
| `CU-TDA-CMP` | Verificado | 6 / 6 | **Con el retiro en el local** (plan 07, octava parte; B-07-038): la modalidad en el checkout, el cobro y el pedido que nacen con ella, D4 en el servidor y en la base. `apps/tienda/compra.py`, `views_compra.py`, `pasarelas.py`, `mercadopago.py`. **Todos sus contratos verificados**, con idempotencia, E2, E3 y la carrera del último ejemplar (B-07-035). A2 sólo con envío gratuito (B-07-033). El correo de confirmación lleva el enlace al pedido en «Mi cuenta». Plan 07, sexta parte; barra del envío gratis en la séptima (B-07-037). |
| `CU-TDA-INV` | Verificado | 5 / 5 | **Todos sus contratos verificados.** Sin pre-ventas (precondición), sin puntos, pedido asociado al correo; la sugerencia de iniciar sesión aparece dos veces (B-07-036). Plan 07, sexta parte. |

**Sin caso de uso todavía:** las **filas de la portada** (plan 07, tercera y cuarta parte;
B-07-009, B-07-010). El Administrador las arma por etiqueta o por grupo de etiquetas en «Tienda →
Filas de la portada», en tarjetas que se reordenan arrastrando y con imagen opcional; el Cliente
las recorre de costado. La cáscara de la tienda suma el encabezado fijo con búsqueda y menú de
cuenta (B-07-011, desvío consultado), la cinta de accesos, el globo de preguntas frecuentes y el
pie (B-07-012). Con prueba (`test_filas_portada.py`, 19 casos, incluido el rol equivocado por la
dirección real). El código del caso de uso lo asigna el responsable.

**Quinta parte del plan 07 (2026-10-05):** la portada es pública (C-20 resuelta, B-07-019) y suma
«Lo que se viene» (B-07-015); las tarjetas agregan al carrito sin abrir la ficha (`CO-083`,
B-07-014) y llevan los carteles «¡TOMO 1!» y «¡NOVEDAD!» (B-07-024); las pantallas de acceso siguen la guía, con la imagen del ingreso configurable en la identidad
visual (B-07-018, B-07-020); se quitó la cinta de accesos (B-07-021); el logo y la imagen del ingreso se pueden quitar (B-07-025); y donde el navegador no
tiene `base-select` el desplegable usa una lista propia (B-00-011, desvío consultado). Con prueba:
`test_tienda_quinta_parte.py`, 18 casos, y `CO-131` suma la imagen del ingreso.

### `08` Gestión de Pedidos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PED-CON` | Verificado | 2 / 2 | `apps/pedidos/views.py`. **Todos sus contratos verificados.** Listado de a 50 con filtros (cliente por nombre o correo, B-08-003), total cobrado en la misma consulta, y detalle con medio de pago, puntos y línea de tiempo (B-08-001). Sólo el Administrador. Plan 08. |
| `CU-PED-EST` | Verificado | 3 / 3 | `apps/pedidos/servicios.py`. **Todos sus contratos verificados**: un paso por vez con confirmación, E1, E2 con `CO-093`, líneas que avanzan salvo las demoradas, correo al cliente o al invitado (B-08-002), auditoría, y la carrera entre dos administradores. Plan 08. |
| `CU-PED-OPC` | Verificado | 6 / 6 | **Todos sus contratos verificados.** Opciones según el pedido (B-08-009), confirmación con la consecuencia, una sola decisión con dos pestañas, ventana vencida rechazada y cerrada por el Temporizador (`CO-096`); la opción 2 termina en el stock almacenado (B-18-002, B-18-003). Planes 08 y 18. |
| `CU-PED-CAN` | Verificado | 2 / 2 | **Todos sus contratos verificados**: reembolso en puntos (los mismos si se pagó con puntos), el stock no cambia (B-08-005), el pedido sin otros artículos se cancela con el envío (B-08-008), E1 todo o nada con aviso al Administrador, y la carrera contra la llegada del artículo. Plan 08, segunda parte. |
| `CU-PED-CMP` | Verificado | 1 / 1 | **Verificado**: 5 % por semana cumplida contra lo acreditado, tope del 25 %, doble corrida sin exceso, E1, E2 y E3 (B-08-010). Corre hasta que el artículo llega (B-08-006). Plan 08, segunda parte. |

### `09` Devoluciones

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-DEV-SOL` | Verificado | 2 / 2 | **Reformulado en el plan 00, C1** (B-09-008): **arrepentimiento** por el botón público, sin registración (número de pedido y correo), línea entera y sin fotos; **garantía** desde «Mi cuenta» con fotos y su propio plazo. Un caso por línea (I-19), el código por correo al abrirlo. **Todos sus contratos verificados.** |
| `CU-DEV-RES` | Verificado | 5 / 5 | **Reformulado en el plan 00, C1** (B-09-008): contacto a la vista para coordinar por fuera; arrepentimiento con **reembolso por el medio de pago registrado** (o en puntos si se pagó con puntos) y el artículo de vuelta al stock; garantía con cambio por la misma editorial y formato al stock en local sin costo de envío, puntos o medio de pago. Sin `DevolucionFisica`. Puntos ganados descontados (B-10-012). **Todos sus contratos verificados.** |

### `10` Puntos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PTS-CON` | Verificado | 2 / 2 | `apps/puntos/views.py`. **Todos sus contratos verificados.** Saldo con su equivalencia, lotes con «Próximo a vencer» (30 días), historial de a 50 con el pedido de cada movimiento (B-10-001) y filtros por tipo y fechas. El saldo, además, en el encabezado de la tienda (B-10-002). Plan 10. |
| `CU-PTS-CJE` | Verificado | 3 / 3 | **Todos sus contratos verificados en los dos canales**: la tienda (plan 07) y el mostrador (plan 06), por línea entera, sin tocar ningún lote hasta confirmar. |
| `CU-PTS-CAD` | Verificado | 1 / 1 | `apps/puntos/caducidad.py`, en el Temporizador. **`CO-105` verificado**: lote a Vencido con disponible cero, el saldo, lo futuro intacto, E2 con un canje pendiente (y no con uno abandonado), la auditoría por lote, E1 con el incidente y el ciclo que sigue, A1 sin registro (B-10-007), doble corrida. Aviso previo a pedido del responsable (B-10-006). Plan 10, segunda parte. |
| `CU-PTS-ADM` | Verificado | 2 / 2 | `apps/puntos/ajuste.py`, `AjustePuntosView`. **Todos sus contratos verificados**: el panel con lo comprometido (`CO-191`); la acreditación con la caducidad estándar, el débito por caducidad sin tocar lo comprometido, el movimiento, la auditoría con los dos saldos, el aviso, E1 con el máximo y E2 conservando lo ingresado (`CO-106`). Concurrencia: dos débitos, y un débito contra la caducidad. Plan 10, segunda parte. |

### `11` Cuenta de Cliente

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CLI-ALT` | Verificado | 1 / 1 | `RegistroClienteView`, pantalla pública, con autocompletado de localidad desde `core/georef.py`. **Todos sus contratos verificados.** |
| `CU-CLI-CON` | Verificado | 2 / 2 | **Todos sus contratos verificados.** El listado (`CO-194`) enlaza a la ficha de sólo lectura (`ClienteFichaView`, `CO-195`). |
| `CU-CLI-DAT` | Verificado | 4 / 4 | `apps/accounts/views_cuenta.py`. **Todos sus contratos verificados.** Datos con las validaciones del registro; contraseña que cierra las otras sesiones; correo con `TokenCambioCorreo` de 24 h (B-11-002), confirmación por botón y aviso al correo anterior (B-11-005). Plan 11, segunda parte. |
| `CU-CLI-HIS` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Pedidos activos, historial (despachados y cancelados), detalle con su línea de tiempo y acceso a la decisión ante una demora, y la sección Stock en Local (B-11-003 resuelta). Planes 11 y 18. |
| `CU-CLI-BAJ` | Pendiente | 0 / 3 | El informe de impacto necesita Stock Almacenado; pedidos y puntos ya existen. |

### `12` Autenticación

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-AUT-INI` | Verificado | 3 / 3 | `LoginUsuarioView`, bloqueo por intentos, redirección por rol y expiración con renovación. **Todos sus contratos verificados**: `CO-114` con el bloqueo y la expiración de la sesión parametrizados (B-12-004), `CO-115` y `CO-086` (fusión del carrito). Plan 00, A3. |
| `CU-AUT-FIN` | Verificado | 1 / 1 | **Todos sus contratos verificados.** |
| `CU-AUT-REC` | Verificado | 2 / 2 | **Todos sus contratos verificados.** |
| `CU-AUT-ACT` | Verificado | 3 / 3 | **Todos sus contratos verificados.** |

### `13` Gestión de Usuarios

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-USR-ALT` | Verificado | 1 / 1 | **Todos sus contratos verificados.** |
| `CU-USR-MOD` | Verificado | 3 / 3 | **Todos sus contratos verificados.** |
| `CU-USR-BAJ` | Verificado | 3 / 3 | **Todos sus contratos verificados**, incluido `CO-156`: abandonar la confirmación no cambia la cuenta ni audita. |
| `CU-USR-REA` | Verificado | 4 / 4 | **Todos sus contratos verificados**, incluido `CO-156`. |
| `CU-USR-ELI` | Verificado | 3 / 3 | **Todos sus contratos verificados**, incluido `CO-156`. |
| `CU-USR-CON` | Verificado | 2 / 2 | **Todos sus contratos verificados.** La ficha (`UsuarioFichaView`, `CO-202`) ofrece sólo las acciones que el estado admite, y no ofrece la baja del último Administrador. |

### `14` Caja · `15` Reportes · `16` Auditoría

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAJ-CIE` | Verificado | 3 / 3 | `apps/caja`. **Todos sus contratos verificados**: resumen por canal y por medio, un cierre por día (lo posterior va al siguiente, B-14-001), lo de días anteriores sin cerrar entra y se avisa (B-14-002), A1, CSV auditado, y dos cierres a la vez. Plan 14. |
| `CU-REP-GEN` | Pendiente | 0 / 2 | No hay generación de reportes. |
| `CU-AUD-CON` | Verificado | 3 / 3 | **Todos sus contratos verificados.** `LogListaView` de a 50 con filtros por actor, rol, acción, entidad y fechas (B-16-001, B-16-002); `LogDetalleView`; exportación CSV en flujo de todo el filtro, auditada. Toda escritura responde 403. |

### `17` Configuración del Sistema

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CFG-PAR` | Verificado | 3 / 3 | `ParametrosView`: **todas las secciones** — operación, Seguridad (B-12-004), Compra online (Logística, Comercial con los plazos de arrepentimiento y de garantía, Fidelización y pasarela), Proveedores (frecuencia de la casilla) y el modelo de lenguaje. **Todos sus contratos verificados**: `CO-130` con E1 y E2, `CO-207` y `CO-053` desde el enlace al margen (A1). Plan 00, A3. |
| `CU-CFG-LLM` | Verificado | 3 / 3 | `DiagnosticoLLMView` y `core/llm.py`. **Todos sus contratos verificados.** El diagnóstico y la comprobación de disponibilidad quedan en el log sin la credencial (B-17-018). |
| `CU-CFG-EDC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `EditorialListaView`, pantalla propia: activas y dadas de baja, productos vinculados, filtro por estado. |
| `CU-CFG-EDA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Nace activa; la colisión enlaza la existente con su estado. Alta al vuelo con la misma auditoría. |
| `CU-CFG-EDM` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Corrige y reactiva; no da de baja. |
| `CU-CFG-EDB` | Verificado | 4 / 4 | **Todos sus contratos verificados.** Par informe y confirmación; un borrador que la tiene presenta un reparo y no se confirma (B-17-006). |
| `CU-CFG-TPC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** Rubro, clasificación, formatos declarados, productos y filtro por estado. |
| `CU-CFG-TPA` | Verificado | 3 / 3 | **Todos sus contratos verificados.** El rubro entra al formulario; declaración de formatos (`CO-146`) auditada aparte. |
| `CU-CFG-TPM` | Verificado | 3 / 3 | **Todos sus contratos verificados.** E2, E4 y E5 validados; dejar de clasificarse por formato rompe sus combinaciones. |
| `CU-CFG-TPB` | Verificado | 4 / 4 | Par informe y confirmación. El informe cuenta las ofertas Programadas o Activas del tipo y la baja las conserva (R-17-003). |
| `CU-CFG-FMC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** Medidas, «aplica a todos», tipos, productos y filtro por estado. |
| `CU-CFG-FMA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** «Aplica a todos los tipos» es atributo (B-17-004), con migración que conserva el alcance. |
| `CU-CFG-FMM` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Pasar a «aplica a todos» desvincula los tipos; E3 validado. |
| `CU-CFG-FMB` | Verificado | 4 / 4 | **Todos sus contratos verificados.** Par informe y confirmación; borrador con el formato dado de baja no se confirma. |
| `CU-CFG-BNC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** Galería en orden con miniatura y posición, y la vista previa del carrusel tal como la ve el cliente. |
| `CU-CFG-BNA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Imagen procesada por RNF-05 (WebP, 1920 px), al final de la galería, publicada en la portada (B-17-013). |
| `CU-CFG-BNM` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Reemplazo de imagen (la anterior se borra) y cambio de posición con reajuste; una imagen inválida no registra nada. |
| `CU-CFG-BNB` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Confirmación y eliminación con reajuste; sin confirmar no hay eliminación. |
| `CU-CFG-FAQ` | Verificado | 3 / 3 | **Todos sus contratos verificados.** Editor Markdown con vista previa que no publica (B-17-014), publicación sin HTML crudo (C-16) y FAQ vacía con confirmación. Página pública de preguntas frecuentes. |
| `CU-CFG-VIS` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Tres secciones, vista previa en vivo, HEX validados, logo y fondo de imagen procesados (C-07; SVG no admitido, B-17-011). Pinta sólo las cuatro `--tienda-*`. |

### `18` Stock Almacenado en Local

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-STK-CON` | Verificado | 1 / 1 | `apps/almacen`, «Mi cuenta» → Stock en local. Lo propio, con lo próximo a vencer destacado y lo pendiente en sólo lectura. Plan 18. |
| `CU-STK-DES` | Verificado | 5 / 5 | **Todos sus contratos verificados**: resumen, dirección del envío sin tocar el perfil, gratis desde el mínimo (B-18-007) o pago por la pasarela con reembolso si el artículo cambió (E3), solicitud de despacho (B-18-004), volver sin registrar, dos pestañas a la vez. Plan 18. |
| `CU-STK-ADC` | Verificado | 2 / 2 | **Todos sus contratos verificados**: listado con filtros por cliente, producto, estado y vencimiento; ficha con origen e historial de plazo. Administrador y Cajero. Plan 18. |
| `CU-STK-FIS` | Verificado | 3 / 3 | **Todos sus contratos verificados**: despacho por solicitud (B-18-007), retiro con verificación del titular, E1, y la carrera entre despacho y retiro. Plan 18. |
| `CU-STK-PLA` | Verificado | 2 / 2 | **Todos sus contratos verificados**: extender o acortar con motivo, E1, E2, aviso al Cliente. Sólo el Administrador. Plan 18. |
| `CU-STK-VEN` | Verificado | 1 / 1 | **Verificado** en el Temporizador: aviso una vez por fecha (B-18-006), reintegro al stock sin reembolso, extensión de tres días cada vez que vence pendiente (B-18-005), doble corrida sin efecto. Plan 18. |

### Códigos retirados y a qué se repartieron

| Retirado | Se repartió en | Qué se leyó en el código |
| --- | --- | --- |
| `CU-CFG-EDT` | `CU-CFG-EDC`, `EDA`, `EDM`, `EDB` | Alta y edición de editorial; baja por casilla |
| `CU-CFG-TIP` | `CU-CFG-TPC` a `TPB` y `CU-CFG-FMC` a `FMB` | Alta y edición de tipo y de formato; bajas por casilla |
| `CU-CAT-ETQ` | `CU-CAT-GRC` a `GRB` y `CU-CAT-ETC` a `ETB` | Alta y edición de grupo y de etiqueta; bajas por casilla |
| `CU-PVP-TAB` | `CU-PVP-TBC`, `TBA`, `TBM`, `TBB` | Alta, edición sin propagación y borrado de fila |
| `CU-CFG-BAN` | `CU-CFG-BNC`, `BNA`, `BNM`, `BNB` | Nada construido |
| `CU-TDA-CAR` | `CU-TDA-CRC`, `CRA`, `CRM`, `CRB` | Nada construido |
| `CU-STK-ADM` | `CU-STK-ADC`, `FIS`, `PLA` | Nada construido |

`CU-PVP-VEN` («Vencer Ofertas») está decidido y todavía no tiene ficha: no figura entre los 103 y
no tiene fila.

---

## Las siete puertas

Medición del **2026-10-22**, al cerrar la verificación de contratos (V1 y V2 del plan 00), con
PostgreSQL levantado.

| Puerta | Resultado |
| --- | --- |
| Suite de pruebas | **2972 pasan**, 0 fallos, en paralelo y en orden aleatorio (3 min 46 s) |
| **Contratos** | **215 de 219 verificados**, 4 sin prueba: los de `CU-CLI-BAJ` y `CU-REP-GEN`, pendientes |
| Cobertura sobre código de aplicación | **97 %** (12565 sentencias, 425 sin cubrir) |
| Análisis estático | `ruff check .`: sin hallazgos |
| Formato | `black --check .`: 361 archivos sin cambios |
| Auditoría de seguridad | `bandit -r apps config scripts`, sin pruebas ni migraciones: sin hallazgos. `pip-audit`: sin vulnerabilidades conocidas, después de pasar `virtualenv` a 21.14.9 (CVE-2026-113722) |
| Configuración de despliegue | `check --deploy --fail-level WARNING` con la configuración de producción: **sin advertencias** |

**Verificación de contratos, a mano (2026-10-22).** `catalog.0023` y `core.0040` aplicaron sobre la
base de desarrollo; `producto_editorial_manual_sin_referencia` está en `pg_constraint`, y
`makemigrations --check` no detecta cambios.

**Plan 00 de interfaz, verificaciones a mano (2026-10-21).** `pedidos.0007` aplicó sobre la base
de desarrollo y pasó las 2 ventas presenciales existentes a «Vendido en el local · Mostrador»
(B-06-005); `pedido_mostrador_solo_presencial` está en `pg_constraint`, y `makemigrations --check`
no detecta cambios. El mostrador, la venta registrada, la caja, Restock, la lista de pedidos, «Mi
cuenta», los avisos de stock, el carrito lateral y las sugerencias se revisaron con capturas de
Chrome sin interfaz, en escritorio y en 390px.

**Plan 00, verificaciones a mano (2026-10-19).** `almacen.0004`, `core.0037` a `0039`,
`devoluciones.0002` (con el correo de contacto de los casos existentes y la disconformidad pasada a
arrepentimiento) y `tienda.0006` aplicaron sobre la base de desarrollo; `makemigrations --check` no
detecta cambios. En `pg_constraint` están `caso_arrepentimiento_sin_cambio`,
`caso_reembolso_medio_con_monto` y `caso_al_menos_una_unidad`; la tabla de `DevolucionFisica` ya no
existe. El botón de arrepentimiento, su pedido, la confirmación con el código, la ficha del caso,
el reembolso por el medio de pago y Parámetros se revisaron con capturas de Chrome sin interfaz. Las
pruebas de concurrencia de pre-venta y devoluciones corrieron tres veces seguidas sin fallos.

**Retiro en el local, verificaciones a mano (2026-10-19).** `pedidos.0006`, `almacen.0003` y
`tienda.0005` aplicaron sobre la base de desarrollo: los 5 pedidos existentes quedaron como envío a
domicilio; `makemigrations --check` no detecta cambios. `pedido_retiro_de_cuenta_sin_envio` está en
`pg_constraint`. El checkout con retiro, el pedido en «Mi cuenta», el stock en local, la ficha del
pedido en el panel, «Entregar todo» y la ficha del artículo se revisaron con capturas de Chrome sin
interfaz. La prueba de concurrencia de la entrega corrió tres veces seguidas sin fallos.

**Puntos, verificaciones a mano (2026-10-17).** `core.0036` y `puntos.0003` aplicaron sobre la
base de desarrollo, con el aviso previo en 3 días y los lotes existentes sin avisar;
`makemigrations --check` no detecta cambios. La segunda parte no agrega restricciones. La ficha
del Cliente con el enlace, el panel de puntos, E1 con el máximo, el ajuste registrado y «Mis
puntos» con «Se pueden usar hasta» se revisaron con capturas de Chrome sin interfaz. Las pruebas
de concurrencia corrieron tres veces seguidas sin fallos.

**Devoluciones, verificaciones a mano (2026-10-16).** `core.0035`, `devoluciones.0001` y
`puntos.0002` aplicaron sobre la base de desarrollo, con el plazo de devolución en 10 días;
`makemigrations --check` no detecta cambios. En `pg_constraint` están
`plazo_devolucion_piso_legal`, `caso_estado_coherente_con_resolucion`,
`caso_cambio_tiene_reemplazo`, `devolucion_fisica_retiro_con_fecha` y las unicidades
`devoluciones_casodevolucion_linea_id_key` (I-19) y `devoluciones_devolucionfisica_caso_id_key`.
El detalle del pedido con el botón y con el reclamo, el formulario (vacío y con E3), el panel, el
detalle del caso, la búsqueda del reemplazo, la confirmación del cambio, el reembolso, el rechazo
y Parámetros se revisaron con capturas de Chrome sin interfaz. Las pruebas de concurrencia
corrieron tres veces seguidas sin fallos. Las fotos se guardan en `privado/`, que no se versiona.

**Stock en local y restock, verificaciones a mano (2026-10-14).** `almacen.0001` y `0002` (sin
artículos diferidos pendientes en la base), `restock.0001`, `core.0033` y `0034`, `pedidos.0005` y
`tienda.0004` aplicaron sobre la base de desarrollo; `makemigrations --check` no detecta cambios.
En `pg_constraint` están `articulo_valor_positivo`, `articulo_con_plazo_tiene_vencimiento`,
`articulo_pendiente_tiene_solicitud`, `solicitud_costo_envio_no_negativo`,
`transaccion_de_pedido_o_de_solicitud` y `linea_restock_producto_unico`; las únicas condicionales
`suscripcion_en_espera_unica` (I-22) y `propuesta_pendiente_unica` (I-21) están en `pg_indexes`.
Las pantallas de «Mi cuenta», el panel de stock en local, la ficha, la solicitud, el plazo, la
propuesta de restock y la ficha pública con el aviso se revisaron con capturas de Chrome sin
interfaz. Las pruebas de concurrencia corrieron tres veces seguidas sin fallos.

**Pre-venta y demora, verificaciones a mano (2026-10-12).** `core.0032` y `pedidos.0004` aplicaron
sobre la base de desarrollo, con los valores por defecto de los dos parámetros nuevos (2 días y 72
horas); `makemigrations --check` no detecta cambios. `aviso_preventa_unico` está en
`pg_constraint` y en `pg_indexes`. Las pantallas de pre-ventas, la revisión del ingreso, la
demora, la cancelación, la ficha, el panel y las opciones del Cliente se revisaron con capturas de
Chrome sin interfaz. Las pruebas de concurrencia corrieron cinco veces seguidas sin fallos.

**Mostrador y caja, verificaciones a mano (2026-10-10).** `accounts.0009` (con el código de los
clientes existentes), `caja.0001`, `core.0031` y `pedidos.0003` aplicaron sobre la base de
desarrollo; los tres clientes que había recibieron su código. En la base están
`accounts_usuario_codigo_cliente_key`, `caja_cierredecaja_fecha_jornada_key` (I-23) y
`cierre_totales_no_negativos`. Las pantallas del mostrador, el comprobante, la caja y el cierre
se revisaron con capturas de Chrome sin interfaz.

**Las dos verificaciones a mano.** Las migraciones nuevas (`core.0027` y `0028`, `pedidos.0001` y
`0002`, `puntos.0001`, `tienda.0002` y `0003`, `accounts.0008`) aplicaron sobre la base de
desarrollo; `pedidos.0002` le dio su primera transición a los pedidos que ya había, y `makemigrations --check`
no detecta cambios. Las restricciones están en la base, consultadas en `pg_constraint` y
`pg_indexes`: `pedido_costo_envio_no_negativo`, `pedido_online_de_cuenta_o_invitado`,
`linea_pedido_cantidad_minima`, `linea_pedido_precio_positivo`,
`linea_pedido_compensacion_no_negativa`, `linea_pedido_canje_coherente`,
`transaccion_monto_no_negativo`, `lote_disponible_no_supera_lo_acreditado`,
`lote_estado_coherente_con_disponible`, `movimiento_cantidad_positiva` y
`cobro_importes_no_negativos`; y las unicidades `pedidos_pedido_numero_key`,
`pedidos_transaccionpago_referencia_key` y `tienda_cobroencurso_referencia_key`. **Son las
primeras `CheckConstraint` sobre dinero del proyecto** (I-09).

**Las pantallas nuevas se revisaron con capturas de Chrome sin interfaz**: las siete de la compra;
el carrito con la barra del envío; el listado, el detalle y la confirmación de avance de pedidos y
el tablero; y «Mi cuenta» (pedidos, detalle, puntos y datos).

---

## Lo que esta fotografía no cubre

- **Las pantallas se revisaron con capturas de Chrome sin interfaz** (portada, catálogo y ficha
  de la tienda, panel, carga de lotes, y las siete de la compra), no a mano en un navegador interactivo. El carrusel y la vista previa de la identidad visual tienen guion:
  sus pruebas verifican que los controles estén, no su comportamiento en el navegador.
- **Las pantallas se revisaron con capturas**, no a mano en un navegador interactivo: panel,
  inventario, ficha de producto, ficha de correo, parámetros e inicio de sesión. El resto se
  verificó por la suite y la prueba del estilo.
- **El estado `Parcial` es un juicio sobre el alcance, no sobre la calidad.** Dice que falta una
  parte declarada del caso de uso, no que lo construido esté mal.
- **MercadoPago se probó contra respuestas declaradas**, no contra su API: la red está cortada en
  la suite y no hay credenciales de prueba cargadas. El recorrido con una cuenta de prueba real y
  el aviso llegando por el túnel queda para cuando el responsable cargue `MERCADOPAGO_ACCESS_TOKEN`.
