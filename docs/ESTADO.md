> **Tipo: Fotografía.** Tomada el **2026-10-03**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada. La escala de
> estados y los umbrales de las siete puertas son reglas y viven en `CLAUDE.md`.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Quinta fotografía. **Se construyó la etapa B sin la compra**: el carrito (plan 07, segunda parte) y
las ofertas (plan 03, segunda parte). La compra, el invitado y los pedidos siguen esperando a
`Pedido` y `TransaccionPago`.

**Lo que más se movió.**
- **El precio visible sale de una sola función.** La tienda, el carrito y, cuando exista, el
  mostrador cobran el precio con la oferta vigente. La oferta no toca el precio guardado del
  producto: darla de baja o dejarla vencer lo restaura solo (B-03-007).
- **El carrito guarda dos importes por línea**, el vigente y el que vio el Cliente, para poder
  avisar que el precio cambió sin dejar de propagar (B-07-003).
- **La propagación de precios llega a los carritos**: la tabla de precios, el margen y cada
  operación de oferta. Por eso `CU-PVP-TBM` y `MAR` pasan a Verificado (R-03-001).
- **P-05 tiene forma**: `manage.py ejecutar_temporizador` es la puerta de los procesos periódicos.
  Hoy corre el ciclo de vigencia de ofertas (`CO-059`) y arranca con `demostracion.bat`.
- **Los correos salen por SMTP** con copia en la consola y el estilo del sistema (B-00-008). Mientras
  el `.env` no tenga una contraseña de aplicación válida, quedan sólo en la consola.

**Por qué varios quedan `Parcial` con todas sus pruebas de contrato.** Sus contratos declaran un
efecto sobre los filtros del catálogo público (`CU-CAT-GRM`, `GRB`, `ETM`, `ETB`; B-02-004), o
inician un caso de uso que no existe (`CU-TDA-CAT`: «Avisarme cuando haya stock»). La prueba cubre
todo lo demás.

| | |
| --- | --- |
| Casos de uso especificados | 103 |
| Verificados | 48 |
| Construidos, sin verificar | 9 |
| Parciales | 15 |
| En curso | 0 |
| Pendientes | 31 |
| Bloqueados | 0 |

Contratos de operación especificados: **219**. Con prueba: **94**, de los cuales **89 verificados**
y **5 parciales** (`CO-114`, `CO-039`, `CO-041`, `CO-043`, `CO-045`). Sin prueba: **125**. El
detalle por contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md), regenerado hoy: 320
pruebas de contrato.

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
| `CU-ALT-DEM` | Parcial | 0 / 3 | Los campos existen (`demorado`, `fecha_estimada`, `nota_demora`) y el inventario muestra el indicador. No hay pantalla de registro de demora (`CO-014`/`CO-015`) ni aviso a clientes: depende de Pedido. |
| `CU-ALT-TRA` | Pendiente | 0 / 5 | El estado Pre-venta existe. No existen los ciclos de `CO-011` y `CO-012` (P-05) ni la confirmación de ingreso de `CO-013`. |
| `CU-ALT-CAN` | Pendiente | 0 / 3 | El estado terminal existe. La cancelación en lote y el reembolso en puntos dependen de Pedido y Puntos. |

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
| `CU-VTA-REG` | Pendiente | 0 / 7 | `MostradorView` es una pantalla de relleno: sólo fija el control de acceso del rol Cajero. |

### `07` Tienda Online

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | Parcial | 2 / 2 | Contratos con prueba (`CO-176`, `CO-177`). Catálogo público con filtros, de a 24; ficha con galería, **precio tachado con la oferta vigente** y el filtro de precio sobre el precio que se cobra (B-03-011). «Agregar al carrito» y «Reservar» inician `CU-TDA-CRA` (R-07-001). `Parcial`: «Avisarme cuando haya stock» espera a `CU-RST-SUS`. Plan 07 |
| `CU-TDA-CRC` | Verificado | 3 / 3 | `tienda/carrito.html`, `apps/tienda/carrito.py`. Líneas con el precio visible de hoy, aviso de precio cambiado con el importe anterior (B-07-003), disponibilidad derivada en tres valores (B-07-004) y total. «Ir a pagar» deshabilitado hasta `CU-TDA-CMP` (B-07-006). Plan 07, segunda parte. |
| `CU-TDA-CRA` | Verificado | 1 / 1 | Desde la ficha, con cantidad. Tope en el stock con aviso (E1); la Pre-venta reserva sin tope (A1). El personal no tiene carrito (B-07-005). |
| `CU-TDA-CRM` | Verificado | 1 / 1 | Tope en el stock (E1), mínimo uno (E2), sin tope en Pre-venta. La línea de otro carrito responde 404. |
| `CU-TDA-CRB` | Verificado | 1 / 1 | Sin confirmación. La línea de otro carrito responde 404. |
| `CU-TDA-CMP` | Pendiente | 0 / 6 | No existen `Pedido` ni `TransaccionPago`. |
| `CU-TDA-INV` | Pendiente | 0 / 5 | Ídem. |

**Sin caso de uso todavía:** las **filas de la portada** (plan 07, tercera parte; B-07-009). El
Administrador las arma por etiqueta o por grupo de etiquetas en «Tienda → Filas de la portada»; el
Cliente las recorre de costado. Con prueba (`test_filas_portada.py`, 10 casos, incluido el rol
equivocado por la dirección real). El código del caso de uso lo asigna el responsable.

### `08` Gestión de Pedidos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PED-CON` | Pendiente | 0 / 2 | No existe `Pedido`. |
| `CU-PED-EST` | Pendiente | 0 / 3 | Ídem. |
| `CU-PED-OPC` | Pendiente | 0 / 6 | Ídem. Su DSS muestra ahora al Temporizador disparando el vencimiento de la ventana (`CO-096`, P-05). |
| `CU-PED-CAN` | Pendiente | 0 / 2 | Ídem. |
| `CU-PED-CMP` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |

### `09` Devoluciones

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-DEV-SOL` | Pendiente | 0 / 2 | No existe `CasoDevolucion`. |
| `CU-DEV-RES` | Pendiente | 0 / 5 | Ídem. |

### `10` Puntos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PTS-CON` | Pendiente | 0 / 2 | No existen `LotePuntos` ni `MovimientoPuntos`. |
| `CU-PTS-CJE` | Pendiente | 0 / 3 | Ídem. |
| `CU-PTS-CAD` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |
| `CU-PTS-ADM` | Pendiente | 0 / 2 | Ídem. |

### `11` Cuenta de Cliente

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CLI-ALT` | Construido, sin verificar | 0 / 1 | `RegistroClienteView`, pantalla pública, con autocompletado de localidad desde `core/georef.py`. |
| `CU-CLI-CON` | Verificado | 2 / 2 | **Todos sus contratos verificados.** El listado (`CO-194`) enlaza a la ficha de sólo lectura (`ClienteFichaView`, `CO-195`). |
| `CU-CLI-DAT` | Pendiente | 0 / 4 | El Cliente no tiene panel propio. |
| `CU-CLI-HIS` | Pendiente | 0 / 2 | No existe `Pedido`. |
| `CU-CLI-BAJ` | Pendiente | 0 / 3 | Depende de Pedidos, Puntos y Stock Almacenado para el informe de impacto. |

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
| `CU-CAJ-CIE` | Pendiente | 0 / 3 | No existe `CierreDeCaja`. Depende de Ventas Presenciales. |
| `CU-REP-GEN` | Pendiente | 0 / 2 | No hay generación de reportes. |
| `CU-AUD-CON` | Verificado | 3 / 3 | **Todos sus contratos verificados.** `LogListaView` de a 50 con filtros por actor, rol, acción, entidad y fechas (B-16-001, B-16-002); `LogDetalleView`; exportación CSV en flujo de todo el filtro, auditada. Toda escritura responde 403. |

### `17` Configuración del Sistema

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CFG-PAR` | Parcial | 1 / 3 | `ParametrosView`: stock inicial por defecto, **intervalo del carrusel** (10 s, B-17-003) y modelo de lenguaje. El margen salió a `CU-PVP-MAR` y el panel lo enlaza (A1). Faltan las secciones de los módulos no construidos y la de Seguridad (B-12-001). `CO-130` y `CO-207` sin prueba de contrato. |
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

Medición del **2026-10-03**, con PostgreSQL levantado, sobre el repositorio entero.

| Puerta | Resultado |
| --- | --- |
| Suite de pruebas | **1812 pasan**, 0 fallos, 7 min 44 s. Después se ajustó el informe de baja de tipo (R-17-003) y se volvió a correr `apps/catalog` entero: 749 pasan |
| **Contratos** | **89 de 219 verificados**, 5 parciales, 125 sin prueba. Detalle en [pruebas/COBERTURA.md](pruebas/COBERTURA.md) |
| Cobertura sobre código de aplicación | **96 %** (6893 sentencias, 271 sin cubrir) |
| Análisis estático | `ruff check .`: sin hallazgos |
| Formato | `black --check .`: 194 archivos sin cambios |
| Auditoría de seguridad | `bandit -r apps config scripts`, sin pruebas ni migraciones: sin hallazgos |
| Configuración de despliegue | `check --deploy --fail-level WARNING` con la configuración de producción y el `.env` de esta máquina: **sin advertencias** |

**Las dos verificaciones a mano.** Las migraciones de hoy (`tienda.0001`, `catalog.0022`,
`core.0022`) aplicaron sobre la base de desarrollo, y `ejecutar_temporizador` corrió sobre ella.
`makemigrations --check` no detecta cambios. Las restricciones están en la base:
`linea_unica_por_producto` (restricción e índice), `linea_cantidad_minima`,
`carrito_persistente_si_tiene_usuario`, `oferta_alcance_coherente`, `oferta_fechas_coherentes`,
`oferta_valor_positivo` y `oferta_porcentaje_menor_a_100`.

**La prueba del estilo es ahora `test_estilo_vineta.py`**: `tokens.css` idéntico al del
responsable, fuentes autoalojadas presentes, ningún color ni radio en los componentes, sombras sin
desenfoque, sólo animaciones del catálogo, movimiento reducido declarado, las variables de la
tienda sólo en el público y el sticker fuera del mostrador.

---

## Lo que esta fotografía no cubre

- **Las pantallas se revisaron con capturas de Chrome sin interfaz** (portada, catálogo y ficha
  de la tienda, panel, carga de lotes), no a mano en un navegador interactivo. El carrusel y la vista previa de la identidad visual tienen guion:
  sus pruebas verifican que los controles estén, no su comportamiento en el navegador.
- **Las pantallas se revisaron con capturas**, no a mano en un navegador interactivo: panel,
  inventario, ficha de producto, ficha de correo, parámetros e inicio de sesión. El resto se
  verificó por la suite y la prueba del estilo.
- **El estado `Parcial` es un juicio sobre el alcance, no sobre la calidad.** Dice que falta una
  parte declarada del caso de uso, no que lo construido esté mal.
