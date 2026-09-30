> **Tipo: Fotografía.** Tomada el **2026-09-30**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada. La escala de
> estados y los umbrales de las siete puertas son reglas y viven en `CLAUDE.md`.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Tercera fotografía. **El código no cambió desde la anterior**: el último commit que toca código
es `7891b0e`, del 2026-09-22. Lo que cambió es la especificación: el documento de análisis pasó
de 75 a **103 casos de uso** y de 218 a **219 contratos**. Varios casos de uso agrupados se
dividieron en alta, baja, modificación y consulta, y esta fotografía reparte lo construido entre
los códigos nuevos leyendo el código de cada pantalla. Los códigos que ya no existen se listan al
final, con los códigos que los reemplazan.

**Consecuencia de la división: sube la cantidad de `Parcial`.** Un caso de uso agrupado que se
contaba como un solo `Parcial` ahora son cuatro filas. En cada una la observación dice qué parte
falta. Casi siempre es la misma: **la baja es una casilla `activo` dentro del formulario de
edición**. Los contratos piden, en cambio, un par solicitar/confirmar con informe de impacto, y
que la modificación **no** pueda pasar un registro de activo a inactivo.

**Dos casos de uso que estaban construidos pasan a `Parcial` porque su ficha creció.**
`CU-AUT-INI` ahora referencia `CO-086 fusionarCarritoDeSesion`, que necesita `Carrito`.
`CU-CAT-EDI` referencia `CO-031 restaurarPrecioCalculado`, que no existe en el código: se puede
romper el vínculo del precio pero no restaurarlo. Por el mismo criterio pasan a `Parcial` las
altas de lote y la revisión de borradores (`CO-077`, que depende de restock) y `CU-RST-PED`
(`CO-072`, ídem).

| | |
| --- | --- |
| Casos de uso especificados | 103 |
| Verificados | 11 |
| Construidos, sin verificar | 9 |
| Parciales | 37 |
| En curso | 0 |
| Pendientes | 46 |
| Bloqueados | 0 |

Contratos de operación especificados: **219**. Verificados: **26**. Parciales: **1** (`CO-114`).
Sin prueba: **192**. El detalle por contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md),
regenerado hoy. Es la única fuente de qué prueba cubre qué contrato. Las 98 pruebas de contrato
de la suite apuntan a 19 contratos, y los 19 siguen vigentes con la misma operación que
nombraban.

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
| `CU-ALT-NAC` | Parcial | 0 / 10 | `AltaLoteNacionalView`, `catalog/services.py`, `catalog/precios.py`, con alta de editorial al vuelo (`EditorialRapidaView`). No hay alta al vuelo de tipo ni de formato (`CO-141`, `CO-144` desde el lote). `CO-077` no tiene código: depende de `SuscripcionReposicion`, módulo 05. |
| `CU-ALT-IMP` | Parcial | 0 / 13 | `AltaLoteImportadoView`, calculadora de envío y CRE en `LoteAlta`, cotización desde `core/cotizaciones.py`. Las mismas dos faltas que `CU-ALT-NAC`. `CO-031` como vía de A1 tampoco existe. |
| `CU-ALT-NOV` | Parcial | 2 / 3 | **`CO-017` y `CO-019` verificados**: la aprobación y el reprocesamiento se disparan desde la ficha del correo (CU-PRV-COL). `CO-016`, el ciclo de monitoreo de la casilla, no existe y depende de P-05. |
| `CU-ALT-REV` | Parcial | 0 / 10 | `BorradorListaView`, `BorradorDetalleView`, `ConfirmarEnLoteView`, `CerrarSesionRevisionView`, `catalog/revisiones.py`, `ConfianzaCampo`. `CO-077` no tiene código. |
| `CU-ALT-DEM` | Parcial | 0 / 3 | Los campos existen (`demorado`, `fecha_estimada`, `nota_demora`) y el inventario muestra el indicador. No hay pantalla de registro de demora (`CO-014`/`CO-015`) ni aviso a clientes: depende de Pedido. |
| `CU-ALT-TRA` | Pendiente | 0 / 5 | El estado Pre-venta existe. No existen los ciclos de `CO-011` y `CO-012` (P-05) ni la confirmación de ingreso de `CO-013`. |
| `CU-ALT-CAN` | Pendiente | 0 / 3 | El estado terminal existe. La cancelación en lote y el reembolso en puntos dependen de Pedido y Puntos. |

### `02` Catálogo

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAT-ALT` | Construido, sin verificar | 0 / 2 | `ProductoNoEditorialAltaView` y `DuplicadosNoEditorialesView`. |
| `CU-CAT-EDI` | Parcial | 0 / 5 | `ProductoEdicionView`, con la ruptura del vínculo al fijar el precio a mano (`CO-005`). **`CO-031 restaurarPrecioCalculado` no existe**: el vínculo se rompe y no se puede restaurar. |
| `CU-CAT-BAJ` | Construido, sin verificar | 1 / 3 | `ProductoBajaView`, con el informe de impacto previo. `CO-156` verificado. |
| `CU-CAT-REA` | Construido, sin verificar | 1 / 3 | `ProductoReactivarView`. `CO-156` verificado. Falta comparar lo construido contra `CO-035`/`CO-036`. |
| `CU-CAT-INV` | Parcial | 0 / 3 | `ProductoListaView` y `ProductoDetalleView`, con ficha diferenciada por rol. Falta la exportación de `CO-037`: no hay ninguna salida a archivo en el repositorio. |
| `CU-CAT-GRC` | Parcial | 0 / 1 | `EtiquetasView` lista los grupos con sus etiquetas, y la pantalla de parámetros los lista con la cantidad de etiquetas. No hay filtro por estado. |
| `CU-CAT-GRA` | Parcial | 0 / 2 | `GrupoEtiquetaCrearView`, con el nombre normalizado. La colisión no enlaza al grupo existente ni dice su estado (E1). El formulario deja crear el grupo inactivo, y `CO-038` declara `g.activo` en sí. |
| `CU-CAT-GRM` | Parcial | 0 / 2 | `GrupoEtiquetaEditarView`. Permite desactivar el grupo desde la casilla, cosa que `CO-039` excluye. |
| `CU-CAT-GRB` | Parcial | 0 / 4 | La baja es la casilla del formulario: no hay informe (`CO-040`) ni confirmación (`CO-041`). **No da de baja las etiquetas del grupo**: las saca de los desplegables por filtro, sin cambiar `e.activa`, como pide `CO-041`. |
| `CU-CAT-ETC` | Parcial | 0 / 1 | `EtiquetasView`, con búsqueda por texto sobre todas las etiquetas. No hay listado por grupo, ni paginación, ni filtro por estado. |
| `CU-CAT-ETA` | Parcial | 0 / 2 | `EtiquetaCrearView`, con unicidad dentro del grupo. La colisión no enlaza a la existente. Permite crearla inactiva. |
| `CU-CAT-ETM` | Parcial | 0 / 2 | `EtiquetaEditarView`: nombre, grupo (sólo activos) y estado. Permite desactivarla desde la casilla, cosa que `CO-043` excluye. |
| `CU-CAT-ETB` | Parcial | 0 / 4 | La baja es la casilla del formulario, sin informe (`CO-044`) ni confirmación (`CO-045`). |

### `03` Pricing

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PVP-TBC` | Parcial | 0 / 1 | Tabla dentro de `ParametrosView`, con filtro sólo por editorial. `CO-166` pide también por tipo y por formato. |
| `CU-PVP-TBA` | Parcial | 0 / 3 | `PrecioCrearView`. La validación de posibilidad es parcial: exige tipo por formato y formato aplicable, pero **no exige que el tipo sea del rubro editorial**. La colisión no enlaza a la fila existente. `CO-031` no existe. |
| `CU-PVP-TBM` | Parcial | 0 / 4 | `PrecioEditarView` cambia el precio de la fila y **no propaga**. No hay informe de alcance (`CO-047`), ni confirmación (`CO-048`), ni acción de auditoría propia. La pantalla lo dice: «cambiarlo acá no toca los productos ya cargados». |
| `CU-PVP-TBB` | Parcial | 0 / 5 | `PrecioEliminarView` borra la fila y los productos conservan su precio (`SET_NULL`). No informa cuántos productos están vinculados (`CO-050`) ni devuelve la cantidad desvinculada. |
| `CU-PVP-MAR` | Parcial | 0 / 4 | El margen se edita dentro de `ParametrosView`. **No hay simulación (`CO-052`) ni recálculo (`CO-053`)**. La propagación a carritos no puede cerrar antes de `Carrito`. |
| `CU-PVP-ALT` | Pendiente | 0 / 2 | No existe `Oferta`. |
| `CU-PVP-EDI` | Pendiente | 0 / 2 | Ídem. |
| `CU-PVP-BAJ` | Pendiente | 0 / 3 | Ídem. |
| `CU-PVP-CON` | Pendiente | 0 / 2 | Ídem. |

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
| `CU-TDA-CAT` | Pendiente | 0 / 3 | `TiendaView` es una pantalla de relleno: sólo fija el control de acceso del rol Cliente. |
| `CU-TDA-CRC` | Pendiente | 0 / 3 | No existe `Carrito`. |
| `CU-TDA-CRA` | Pendiente | 0 / 1 | Ídem. |
| `CU-TDA-CRM` | Pendiente | 0 / 1 | Ídem. |
| `CU-TDA-CRB` | Pendiente | 0 / 1 | Ídem. |
| `CU-TDA-CMP` | Pendiente | 0 / 6 | No existen `Pedido` ni `TransaccionPago`. |
| `CU-TDA-INV` | Pendiente | 0 / 5 | Ídem. |

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
| `CU-AUT-INI` | Parcial | 1 / 3 | `LoginUsuarioView`, bloqueo por intentos, redirección por rol y expiración con renovación. **`CO-115` verificado**, `CO-114` parcial (B-12-001). **Nuevo:** la ficha referencia `CO-086 fusionarCarritoDeSesion`, que no puede existir antes de `Carrito`. |
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
| `CU-AUD-CON` | Parcial | 0 / 3 | `RegistroAuditoria` existe, es inmutable y declara 28 acciones. El panel muestra las últimas entradas. No hay consulta con filtros (`CO-205`), ni detalle (`CO-206`), ni exportación (`CO-129`). |

### `17` Configuración del Sistema

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CFG-PAR` | Parcial | 0 / 3 | `ParametrosView` expone margen, stock inicial por defecto y el modelo de lenguaje. Faltan las secciones de los módulos no construidos, la de **Seguridad** (B-12-001) y el **intervalo del carrusel**, que la ficha ya declara y el modelo de dominio todavía no. El margen se edita acá, y la ficha dice que desde este panel sólo se enlaza a `CU-PVP-MAR`. |
| `CU-CFG-LLM` | Construido, sin verificar | 0 / 3 | `DiagnosticoLLMView` y `core/llm.py`. |
| `CU-CFG-EDC` | Parcial | 0 / 1 | Listado dentro de `ParametrosView`, con estado. Cuenta **filas de precio** y no productos vinculados, como pide `CO-211`. No hay filtro por estado. |
| `CU-CFG-EDA` | Parcial | 0 / 2 | `EditorialCrearView` y alta al vuelo (`EditorialRapidaView`). La colisión no enlaza a la existente ni dice su estado. Permite crearla inactiva. |
| `CU-CFG-EDM` | Parcial | 0 / 2 | `EditorialEditarView`. Permite desactivar, cosa que `CO-138` excluye. |
| `CU-CFG-EDB` | Parcial | 0 / 4 | La baja es la casilla del formulario, sin informe (`CO-139`) ni confirmación (`CO-140`). Un borrador que hereda una editorial inactiva **no registra reparo**. |
| `CU-CFG-TPC` | Parcial | 0 / 1 | Listado dentro de `ParametrosView`: nombre, si se clasifica por formato y estado. Falta el rubro, los formatos declarados, la cantidad de productos y el filtro por estado. |
| `CU-CFG-TPA` | Parcial | 0 / 3 | `TipoCrearView`. **El formulario no pide el rubro**: todo tipo nuevo nace editorial. No se pueden declarar formatos desde el tipo (`CO-146`). |
| `CU-CFG-TPM` | Parcial | 0 / 3 | `TipoEditarView`. No cambia el rubro, no valida E2, E4 ni E5, y permite desactivar. |
| `CU-CFG-TPB` | Parcial | 0 / 4 | La baja es la casilla del formulario. **Ahora tiene contrato** (`CO-220`/`CO-221`) y sale de «Código sin contrato». Falta el par con informe. |
| `CU-CFG-FMC` | Parcial | 0 / 1 | Listado dentro de `ParametrosView`: nombre, medidas, tipos y estado. Falta la cantidad de productos y el filtro por estado. |
| `CU-CFG-FMA` | Parcial | 0 / 2 | `FormatoCrearView`. «Aplica a todos» se infiere de la lista vacía; los contratos lo declaran como atributo. No hay alta al vuelo desde el lote. |
| `CU-CFG-FMM` | Parcial | 0 / 2 | `FormatoEditarView`. No valida E3 y permite desactivar. |
| `CU-CFG-FMB` | Parcial | 0 / 4 | La baja es la casilla del formulario, sin informe (`CO-147`) ni confirmación (`CO-148`). |
| `CU-CFG-BNC` | Pendiente | 0 / 1 | No existe `Banner`. |
| `CU-CFG-BNA` | Pendiente | 0 / 2 | Ídem. |
| `CU-CFG-BNM` | Pendiente | 0 / 2 | Ídem. |
| `CU-CFG-BNB` | Pendiente | 0 / 2 | Ídem. |
| `CU-CFG-FAQ` | Pendiente | 0 / 3 | No existe `ContenidoFAQ`. |
| `CU-CFG-VIS` | Pendiente | 0 / 2 | No existe `IdentidadVisual`. |

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

Medición del **2026-09-30**, con PostgreSQL levantado, sobre el repositorio entero.

| Puerta | Resultado |
| --- | --- |
| Suite de pruebas | **1458 pasan**, 0 fallos, 6 min 14 s |
| **Contratos** | **26 de 219 verificados**, 1 parcial (`CO-114`), 192 sin prueba. Detalle en [pruebas/COBERTURA.md](pruebas/COBERTURA.md) |
| Cobertura sobre código de aplicación | **97 %** (4476 sentencias, 155 sin cubrir) |
| Análisis estático | `ruff check apps config scripts`: sin hallazgos |
| Formato | `black --check apps config scripts`: 151 archivos sin cambios |
| Auditoría de seguridad | `bandit -r apps config scripts`, sin las carpetas de pruebas: sin hallazgos |
| Configuración de despliegue | `check --deploy` con la configuración de producción y el `.env` de esta máquina (`ALLOWED_HOSTS=.trycloudflare.com`): **sin advertencias** |

`manage.py migrate --check` sale en 0 sobre la base de desarrollo.

**Sobre la puerta de despliegue.** La conexión tiene CGNAT y la demostración se publica con un
túnel de Cloudflare ([despliegue/DEMOSTRACION.md](despliegue/DEMOSTRACION.md)). Con el host
declarado, la puerta quedó verde por primera vez, y **once casos de uso pasan a `Verificado`**:
son los que ya tenían todos sus contratos verificados. La puerta mide la configuración de esta
máquina: otra instalación tiene que declarar su propio `ALLOWED_HOSTS`.

**La prueba del estilo preliminar pasa**: ninguna plantilla ni la hoja de estilo tienen
animaciones, transiciones, sombras, esquinas redondeadas, gradientes, fuentes web, colores fuera
de los seis tokens ni clases de Tailwind (`apps/core/tests/test_estilo_preliminar.py`).

---

## Lo que esta fotografía no cubre

- **El reparto de los códigos retirados se hizo leyendo vistas, formularios y la pantalla de
  parámetros.** No se ejercitó ninguna pantalla contra el servidor.
- **Las pantallas se revisaron con capturas**, no a mano en un navegador interactivo: panel,
  inventario, ficha de producto, ficha de correo, parámetros e inicio de sesión. El resto se
  verificó por la suite y la prueba del estilo.
- **El estado `Parcial` es un juicio sobre el alcance, no sobre la calidad.** Dice que falta una
  parte declarada del caso de uso, no que lo construido esté mal.
