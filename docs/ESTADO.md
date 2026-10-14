> **Tipo: Fotografía.** Tomada el **2026-10-12**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada. La escala de
> estados y los umbrales de las siete puertas son reglas y viven en `CLAUDE.md`.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Décima fotografía. **La pre-venta llega, se demora o se cancela** (plan 01, ciclo de la
pre-venta, y plan 08, segunda parte). Antes, del 2026-10-10: el mostrador y la caja (planes 06 y
14).

- **«Pre-ventas por llegar»** (`CU-ALT-TRA`): las pre-ventas agrupadas por fecha de llegada y
  editorial (B-01-006). El Administrador carga lo que llegó, revisa qué va a pasar (B-01-011) y
  confirma. Lo recibido cubre primero las reservas, en orden de compra (B-01-007); lo que falta y ya
  venció se demora (B-01-008). Una transacción por producto (E3).
- **Demora** (`CU-ALT-DEM`) y **cancelación por la editorial** (`CU-ALT-CAN`) desde la ficha del
  producto, cada una con su informe de impacto. La cancelación reembolsa en puntos a cada cliente,
  todo o nada (B-01-010).
- **El Cliente ante la demora** (`CU-PED-OPC`, `CU-PED-CAN`): desde el correo o el detalle del
  pedido en «Mi cuenta» elige esperar, recibir lo disponible o cancelar con reembolso. Las opciones
  dependen de cómo está el pedido (B-08-009) y la ventana de decisión dura 72 horas por defecto
  (B-08-004). Un pedido que se queda sin artículos pasa a **Cancelado** y devuelve el envío en
  puntos (B-08-008).
- **Temporizador**: avisos de lo que llega y escalado de lo vencido (`CO-011`, `CO-012`), cierre de
  ventanas vencidas (`CO-096`) y compensación del 5 % semanal hasta el 25 % (`CU-PED-CMP`, B-08-010).
- Panel del Administrador con el bloque «Pre-ventas por llegar»; dos parámetros nuevos: aviso
  previo de pre-venta y ventana de decisión.

**Por qué quedan `Parciales`.** `CU-ALT-TRA`: `CO-013` encadena el aviso a los suscriptores de
reposición (`CO-077`, módulo 05). `CU-PED-OPC`: con la opción 2, el artículo que llega queda
Disponible con la marca «Despacho diferido» y no pasa a `ArticuloRetenido` hasta el módulo 18
(B-08-007). `CU-CLI-HIS`: la sección Stock en Local sigue oculta (B-11-003); el acceso a
`CU-PED-OPC` ya existe.

| | |
| --- | --- |
| Casos de uso especificados | 103 |
| Verificados | 61 |
| Construidos, sin verificar | 9 |
| Parciales | 17 |
| En curso | 0 |
| Pendientes | 16 |
| Bloqueados | 0 |

Contratos de operación especificados: **219**. Con prueba: **140**, de los cuales **130
verificados** y **10 parciales**: `CO-114`, `CO-039`, `CO-041`, `CO-043`, `CO-045`, `CO-060` (sólo
el doble envío), `CO-130` (sin el plazo de devolución ni la sección Seguridad), `CO-192` (sin la
sección Stock en Local), `CO-013` (sin `CO-077`) y `CO-095` (sin `ArticuloRetenido`). Sin
prueba: **79**. El detalle por
contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md), regenerado hoy: 624 pruebas de
contrato.

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
| `CU-ALT-NAC` | Parcial | 3 / 10 | `AltaLoteNacionalView`, `catalog/services.py`, `catalog/precios.py`. **Alta al vuelo de editorial, tipo y formato** desde la cabecera del lote (`CO-137`, `CO-141`, `CO-144` verificados por su caso de uso propio; B-17-009). `CO-077` no tiene código: depende de `SuscripcionReposicion`, módulo 05. Las operaciones propias del alta (`CO-001` a `CO-006`) no tienen prueba de contrato. |
| `CU-ALT-IMP` | Parcial | 4 / 13 | `AltaLoteImportadoView`, calculadora de envío y CRE en `LoteAlta`. Alta al vuelo de los tres catálogos, como `CU-ALT-NAC`. `CO-031` existe y está verificado (`CU-CAT-EDI` A2). Las operaciones propias del alta no tienen prueba de contrato. |
| `CU-ALT-NOV` | Parcial | 2 / 3 | **`CO-017` y `CO-019` verificados**: la aprobación y el reprocesamiento se disparan desde la ficha del correo (CU-PRV-COL). `CO-016`, el ciclo de monitoreo de la casilla, no existe y depende de P-05. |
| `CU-ALT-REV` | Parcial | 0 / 10 | `BorradorListaView`, `BorradorDetalleView`, `ConfirmarEnLoteView`, `CerrarSesionRevisionView`, `catalog/revisiones.py`, `ConfianzaCampo`. `CO-077` no tiene código. |
| `CU-ALT-DEM` | Verificado | 3 / 3 | `apps/pedidos/preventa.py`, `views_preventa.py`. **Todos sus contratos verificados**: informe de impacto (A3), E1 con lo ingresado conservado, la cascada a pedidos con la ventana de decisión (B-08-004) y el correo con acceso directo, E2 con un pedido que falla, y volver sin registrar (`CO-156`). Desde la ficha del producto. Plan 01. |
| `CU-ALT-TRA` | Parcial | 5 / 5 | «Pre-ventas por llegar» (B-01-006) con revisión previa (B-01-011); `CO-013` con cobertura de reservas en orden (B-01-007), faltantes (A1, B-01-008), E3 por producto y dos administradores a la vez; `CO-011` y `CO-012` en el Temporizador, por correo y en el panel, sin repetir avisos (B-01-009). `CO-013` queda parcial: el aviso a suscriptores (`CO-077`) es del módulo 05. Plan 01. |
| `CU-ALT-CAN` | Verificado | 3 / 3 | **Todos sus contratos verificados**: informe por cliente con los puntos (B-01-010), atomicidad total (E1), un lote por cliente, el envío de los pedidos que se quedan vacíos (B-08-008) y volver sin efecto (`CO-156`). Plan 01. |

### `02` Catálogo

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAT-ALT` | Construido, sin verificar | 0 / 2 | `ProductoNoEditorialAltaView` y `DuplicadosNoEditorialesView`. |
| `CU-CAT-EDI` | Parcial | 1 / 5 | `ProductoEdicionView`. **`CO-031 restaurarPrecioCalculado` construido y verificado**, ofrecido desde la ficha y desde la edición con el precio a la vista (B-03-005). La edición ofrece el valor actual de editorial, tipo, formato y etiquetas aunque esté dado de baja (B-17-007). `CO-030`, `CO-032`, `CO-005` y `CO-161` sin prueba de contrato. |
| `CU-CAT-BAJ` | Construido, sin verificar | 1 / 3 | `ProductoBajaView`, con el informe de impacto previo. `CO-156` verificado. |
| `CU-CAT-REA` | Construido, sin verificar | 1 / 3 | `ProductoReactivarView`. `CO-156` verificado. Falta comparar lo construido contra `CO-035`/`CO-036`. |
| `CU-CAT-INV` | Verificado | 3 / 3 | **Todos sus contratos verificados.** Exportación CSV del listado filtrado, sólo Administrador y auditada (`CO-037`); filtro por editorial y etiquetas inactivas marcadas (`CO-162`); ficha por rol que no dibuja lo que el Cajero no ve e indicadores «No disponible» (`CO-163`). |
| `CU-CAT-GRC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `GrupoListaView`: activos y dados de baja, filtro por estado, cantidad de etiquetas. |
| `CU-CAT-GRA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Nace activo; la colisión enlaza el grupo existente con su estado. |
| `CU-CAT-GRM` | Parcial | 2 / 2 | Contratos con prueba. Corrige y reactiva; no da de baja. La reactivación no alcanza a las etiquetas (`CO-039`). Queda `Parcial` por la postcondición sobre los filtros del catálogo público, que no existe hasta `CU-TDA-CAT` (B-02-004, C-13). |
| `CU-CAT-GRB` | Parcial | 4 / 4 | Contratos con prueba. Par informe y confirmación; **la baja alcanza a cada etiqueta del grupo** (`CO-041`) y conserva las asignaciones. `Parcial` por los filtros públicos (B-02-004). |
| `CU-CAT-ETC` | Verificado | 1 / 1 | **Todos sus contratos verificados.** `EtiquetasDeGrupoView`: las etiquetas de un grupo, de a 50 (B-02-003), con búsqueda y filtro por estado, y el estado del grupo. |
| `CU-CAT-ETA` | Verificado | 2 / 2 | **Todos sus contratos verificados.** Unicidad dentro del grupo, colisión con enlace, sólo en grupos activos. |
| `CU-CAT-ETM` | Parcial | 2 / 2 | Contratos con prueba. Corrige, mueve de grupo y reactiva; rechaza reactivar en un grupo dado de baja (E3). `Parcial` por los filtros públicos (B-02-004). |
| `CU-CAT-ETB` | Parcial | 4 / 4 | Contratos con prueba. Par informe y confirmación; la edición del producto la sigue presentando marcada (`CO-045`). `Parcial` por los filtros públicos (B-02-004). |

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
| `CU-PRV-ALT` | Construido, sin verificar | 0 / 2 | `ProveedorAltaView`, con alta de editorial al vuelo. |
| `CU-PRV-EDI` | Construido, sin verificar | 0 / 3 | `ProveedorEdicionView`, con confirmación al cambiar el correo comercial. |
| `CU-PRV-CON` | Construido, sin verificar | 0 / 2 | `ProveedorListaView` y `ProveedorDetalleView`. |
| `CU-PRV-REA` | Construido, sin verificar | 1 / 3 | `ProveedorReactivarView`. `CO-156` verificado. Falta compararla contra `CO-065`/`CO-066`. |
| `CU-PRV-BAJ` | Parcial | 1 / 3 | `ProveedorBajaView` con informe de impacto. `CO-156` verificado. La cifra de propuestas de restock queda «No disponible» porque el módulo 05 no existe (B-04-001). |
| `CU-PRV-COL` | Verificado | 5 / 5 | **Todos sus contratos verificados.** Aprobar (`AprobarCorreoView`) y reprocesar (`ReprocesarCorreoView`) desde la ficha, con la transición condicionada de E1 y la corrección de E4 a favor del contrato (B-04-004). |

### `05` Restock

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-RST-PED` | Parcial | 0 / 3 | `suppliers/pedidos.py`, con reintento hasta tres veces. Lo invoca el cierre de sesión de revisión (`CO-025`). `CO-072 despacharPedidoAProveedor` necesita `PropuestaRestock`. |
| `CU-RST-PRO` | Pendiente | 0 / 2 | No existe `PropuestaRestock`. |
| `CU-RST-APR` | Pendiente | 0 / 8 | Ídem. |
| `CU-RST-SUS` | Pendiente | 0 / 2 | No existe `SuscripcionReposicion`. |
| `CU-RST-NOT` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |

### `06` Ventas Presenciales

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-VTA-REG` | Verificado | 7 / 7 | `apps/ventas`. **Todos sus contratos verificados**: ticket en sesión (B-06-002), alta por código exacto o título (B-06-003), vínculo por código de cliente o correo (B-06-001), canje por ítem, cobro con bloqueo de stock y concurrencia contra la tienda, comprobante imprimible (B-06-004). Cajero y Administrador. Plan 06. |

### `07` Tienda Online

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | Parcial | 2 / 2 | Contratos con prueba (`CO-176`, `CO-177`). Catálogo público con panel de filtros de varios valores que se aplican mientras se cambian, y orden elegible (B-07-013), de a 24; ficha con galería, **precio tachado con la oferta vigente** y el filtro de precio sobre el precio que se cobra (B-03-011). «Agregar al carrito» y «Reservar» inician `CU-TDA-CRA` (R-07-001). `Parcial`: «Avisarme cuando haya stock» espera a `CU-RST-SUS`. Plan 07 |
| `CU-TDA-CRC` | Verificado | 3 / 3 | `tienda/carrito.html`, `apps/tienda/carrito.py`. Líneas con el precio visible de hoy, aviso de precio cambiado con el importe anterior (B-07-003), disponibilidad derivada en tres valores (B-07-004) y total. «Ir a pagar» lleva al checkout; al invitado le ofrece iniciar sesión o comprar como invitado (B-07-006 resuelta). |
| `CU-TDA-CRA` | Verificado | 1 / 1 | Desde la ficha, con cantidad. Tope en el stock con aviso (E1); la Pre-venta reserva sin tope (A1). El personal no tiene carrito (B-07-005). |
| `CU-TDA-CRM` | Verificado | 1 / 1 | Tope en el stock (E1), mínimo uno (E2), sin tope en Pre-venta. La línea de otro carrito responde 404. |
| `CU-TDA-CRB` | Verificado | 1 / 1 | Sin confirmación. La línea de otro carrito responde 404. |
| `CU-TDA-CMP` | Verificado | 6 / 6 | `apps/tienda/compra.py`, `views_compra.py`, `pasarelas.py`, `mercadopago.py`. **Todos sus contratos verificados**, con idempotencia, E2, E3 y la carrera del último ejemplar (B-07-035). A2 sólo con envío gratuito (B-07-033). El correo de confirmación lleva el enlace al pedido en «Mi cuenta». Plan 07, sexta parte; barra del envío gratis en la séptima (B-07-037). |
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
| `CU-PED-OPC` | Parcial | 6 / 6 | `apps/pedidos/demora.py`, `cuenta:demora`. Opciones según el pedido (B-08-009), confirmación con la consecuencia, una sola decisión con dos pestañas a la vez, ventana vencida rechazada en el servidor y cerrada por el Temporizador (`CO-096`). `CO-095` queda parcial: el artículo diferido que llega no pasa a `ArticuloRetenido` hasta el módulo 18 (B-08-007). Plan 08, segunda parte. |
| `CU-PED-CAN` | Verificado | 2 / 2 | **Todos sus contratos verificados**: reembolso en puntos (los mismos si se pagó con puntos), el stock no cambia (B-08-005), el pedido sin otros artículos se cancela con el envío (B-08-008), E1 todo o nada con aviso al Administrador, y la carrera contra la llegada del artículo. Plan 08, segunda parte. |
| `CU-PED-CMP` | Verificado | 1 / 1 | **Verificado**: 5 % por semana cumplida contra lo acreditado, tope del 25 %, doble corrida sin exceso, E1, E2 y E3 (B-08-010). Corre hasta que el artículo llega (B-08-006). Plan 08, segunda parte. |

### `09` Devoluciones

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-DEV-SOL` | Pendiente | 0 / 2 | No existe `CasoDevolucion`. |
| `CU-DEV-RES` | Pendiente | 0 / 5 | Ídem. |

### `10` Puntos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PTS-CON` | Verificado | 2 / 2 | `apps/puntos/views.py`. **Todos sus contratos verificados.** Saldo con su equivalencia, lotes con «Próximo a vencer» (30 días), historial de a 50 con el pedido de cada movimiento (B-10-001) y filtros por tipo y fechas. El saldo, además, en el encabezado de la tienda (B-10-002). Plan 10. |
| `CU-PTS-CJE` | Verificado | 3 / 3 | **Todos sus contratos verificados en los dos canales**: la tienda (plan 07) y el mostrador (plan 06), por línea entera, sin tocar ningún lote hasta confirmar. |
| `CU-PTS-CAD` | Pendiente | 0 / 1 | Los lotes nacen con su fecha de caducidad; falta el ciclo, que depende de P-05. |
| `CU-PTS-ADM` | Pendiente | 0 / 2 | Falta la pantalla del ajuste manual. |

### `11` Cuenta de Cliente

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CLI-ALT` | Construido, sin verificar | 0 / 1 | `RegistroClienteView`, pantalla pública, con autocompletado de localidad desde `core/georef.py`. |
| `CU-CLI-CON` | Verificado | 2 / 2 | **Todos sus contratos verificados.** El listado (`CO-194`) enlaza a la ficha de sólo lectura (`ClienteFichaView`, `CO-195`). |
| `CU-CLI-DAT` | Verificado | 4 / 4 | `apps/accounts/views_cuenta.py`. **Todos sus contratos verificados.** Datos con las validaciones del registro; contraseña que cierra las otras sesiones; correo con `TokenCambioCorreo` de 24 h (B-11-002), confirmación por botón y aviso al correo anterior (B-11-005). Plan 11, segunda parte. |
| `CU-CLI-HIS` | Parcial | 1 / 2 | «Mi cuenta»: pedidos activos, historial (despachados y cancelados, B-11-004, B-08-008) y detalle con su línea de tiempo, que se refresca cada 30 s. **`CO-193` verificado**: el detalle ofrece elegir qué hacer con un artículo demorado. `CO-192` sigue parcial: Stock en Local oculta (B-11-003). Plan 11, segunda parte. |
| `CU-CLI-BAJ` | Pendiente | 0 / 3 | El informe de impacto necesita Stock Almacenado; pedidos y puntos ya existen. |

### `12` Autenticación

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-AUT-INI` | Parcial | 2 / 3 | `LoginUsuarioView`, bloqueo por intentos, redirección por rol y expiración con renovación. **`CO-115` y `CO-086` verificados**: el inicio de sesión fusiona el carrito de invitado (B-07-005). `CO-114` parcial (B-12-001). |
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
| `CU-CFG-PAR` | Parcial | 1 / 3 | `ParametrosView`: stock inicial por defecto, intervalo del carrusel (B-17-003), modelo de lenguaje y **«Compra online»**: Logística, Fidelización y pasarela (B-07-031, B-07-032). Una entrada de auditoría por parámetro modificado. El margen salió a `CU-PVP-MAR` (A1). Faltan el plazo de devolución, las secciones de los módulos no construidos y la de Seguridad (B-12-001). **`CO-130` con prueba, parcial** por esos campos; `CO-207` sin prueba. |
| `CU-CFG-LLM` | Construido, sin verificar | 0 / 3 | `DiagnosticoLLMView` y `core/llm.py`. |
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
| `CU-STK-CON` | Pendiente | 0 / 1 | No existe `ArticuloRetenido`. |
| `CU-STK-DES` | Pendiente | 0 / 5 | Ídem. |
| `CU-STK-ADC` | Pendiente | 0 / 2 | Ídem. |
| `CU-STK-FIS` | Pendiente | 0 / 3 | Ídem. |
| `CU-STK-PLA` | Pendiente | 0 / 2 | Ídem. |
| `CU-STK-VEN` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |

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

Medición del **2026-10-12**, con PostgreSQL levantado, sobre el repositorio entero.

| Puerta | Resultado |
| --- | --- |
| Suite de pruebas | **2402 pasan**, 0 fallos, en paralelo y en orden aleatorio (2 min 51 s) |
| **Contratos** | **130 de 219 verificados**, 10 parciales, 79 sin prueba. Detalle en [pruebas/COBERTURA.md](pruebas/COBERTURA.md) |
| Cobertura sobre código de aplicación | **97 %** (9850 sentencias, 308 sin cubrir). Lo nuevo: `pedidos/preventa.py` 99 %, `pedidos/demora.py` 98 %, `pedidos/views_preventa.py` 92 %, `pedidos/forms.py` 100 % |
| Análisis estático | `ruff check .`: sin hallazgos |
| Formato | `black --check .`: 292 archivos sin cambios |
| Auditoría de seguridad | `bandit -r apps config scripts`, sin pruebas ni migraciones: sin hallazgos. `pip-audit`: sin vulnerabilidades conocidas |
| Configuración de despliegue | `check --deploy --fail-level WARNING` con la configuración de producción: **sin advertencias** |

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
