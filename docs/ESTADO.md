> **Tipo: Fotografía.** Tomada el **2026-09-22**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada. La escala de
> estados y los umbrales de las siete puertas son reglas y viven en `CLAUDE.md`.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Segunda fotografía. Se tomó leyendo el código y contrastándolo contra `.contexto-ia/`, con los
contratos ya archivados por sus Referencias Cruzadas: hasta esta corrida, 64 contratos de todos
los módulos figuraban bajo el 18 y los recuentos por archivo no servían para nada.

La suite corre en verde: **1334 pruebas, 0 fallos, 97 % de cobertura**. **Cero `xfail`**: las
cuatro que había marcaban contratos que el sistema no cumplía, y los dos desvíos que las
originaban se resolvieron a favor del contrato.

**18 contratos de 218 están verificados**, uno queda parcial y 199 siguen sin prueba. Todos los
verificados son de los módulos `12` Autenticación y `13` Gestión de Usuarios, que son los dos
únicos con todos sus casos de uso construidos.

**Ocho casos de uso tienen todos sus contratos verificados** y quedan a una sola advertencia del
estado `Verificado`: `CU-AUT-FIN`, `CU-AUT-REC`, `CU-AUT-ACT`, `CU-USR-ALT`, `CU-USR-MOD`,
`CU-USR-BAJ`, `CU-USR-REA` y `CU-USR-ELI`. La observación de cada uno lo dice. La advertencia es
`ALLOWED_HOSTS`, no se resuelve dentro de un caso de uso y está en [DEUDA.md](DEUDA.md).

| | |
| --- | --- |
| Casos de uso especificados | 75 |
| Verificados | 0 |
| Construidos, sin verificar | 23 |
| Parciales | 14 |
| En curso | 0 |
| Pendientes | 38 |
| Bloqueados | 0 |

Tres casos de uso pasaron de `Construido, sin verificar` a `Parcial` en esta fotografía, y los
tres por la misma razón: se había leído como completo lo que sólo estaba a medias. `CU-PVP-TAB`
no propaga el precio, `CU-PRV-COL` no deja aprobar un correo desde la pantalla y `CU-USR-CON` no
tiene la ficha que CO-202 declara. Los tres están explicados en su fila.

Contratos de operación especificados: **218**. Verificados: **18**. Parciales: **1**. Sin prueba:
**199**. El detalle por contrato está en [pruebas/COBERTURA.md](pruebas/COBERTURA.md), que es la
única fuente de qué prueba cubre qué contrato.

### Cómo leer la columna «Contratos»

Dice *cuántos de los contratos que el caso de uso referencia tienen una prueba que verifica todas
sus postcondiciones*, sobre el total que referencia. El total sale de las Referencias Cruzadas de
cada contrato y no de suponerlo.

**Un contrato compartido no se cuenta dos veces como verificado.** `CO-156 cancelarOperacion` lo
referencian quince casos de uso de ocho módulos, y su prueba lo ejerce en tres pantallas del
módulo 13. Para un caso de uso cuya pantalla de cancelación todavía no existe, `CO-156` **no**
cuenta como verificado: la operación no se puede ejercer ahí. Por eso la columna suma menos que
la cuenta ingenua de códigos con prueba.

**La columna suma 22 y los contratos verificados son 18.** No es un error de arriba ni de abajo:
`CO-156` aparece en tres filas del módulo 13 y `CO-122` en tres filas más —lo referencian
`CU-AUT-ACT`, `CU-USR-MOD` y `CU-USR-REA`—, así que un mismo contrato se cuenta una vez por cada
caso de uso que lo usa. El total de la cabecera cuenta contratos distintos.

---

## Por módulo

### `01` Alta Editorial

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-ALT-NAC` | Construido, sin verificar | 0 / 8 | `AltaLoteNacionalView`, `catalog/services.py`, `catalog/precios.py`. Con pruebas propias (`test_alta_lote_nacional.py`), ninguna nombrada por contrato. |
| `CU-ALT-IMP` | Construido, sin verificar | 0 / 11 | `AltaLoteImportadoView`, calculadora de envío y CRE en `LoteAlta`, cotización desde `core/cotizaciones.py`. |
| `CU-ALT-NOV` | Parcial | 0 / 6 | Extracción, cola de correos y generación de borradores construidas (`suppliers/correos.py`, `extraccion.py`, `catalog/borradores.py`). Falta el ciclo de monitoreo de casilla de CO-016 y la aprobación desde la pantalla de CO-017: las dos se disparan hoy con `manage.py`. El ciclo depende de P-05 — ver [DEUDA.md](DEUDA.md). |
| `CU-ALT-REV` | Construido, sin verificar | 0 / 10 | `BorradorListaView`, `BorradorDetalleView`, `ConfirmarEnLoteView`, `CerrarSesionRevisionView`, `catalog/revisiones.py`, `ConfianzaCampo`. |
| `CU-ALT-DEM` | Parcial | 0 / 3 | Los campos existen (`ProductoEditorial.demorado`, `fecha_estimada`, `nota_demora`, `llegada_vigente`) y el inventario muestra el indicador. No hay pantalla de registro de demora (CO-014/CO-015) ni notificación a clientes: depende de Pedidos. |
| `CU-ALT-TRA` | Pendiente | 0 / 5 | El estado Pre-venta existe en `Producto`. No existe el ciclo de vigilancia (CO-011), ni el escalado por inacción (CO-012), ni la confirmación de ingreso de lote (CO-013). Los dos ciclos dependen de P-05. |
| `CU-ALT-CAN` | Pendiente | 0 / 3 | El estado terminal `Cancelado` existe en `Producto`. El flujo de cancelación en lote y el reembolso en puntos no: dependen de Pedidos y Puntos. |

### `02` Catálogo

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAT-ALT` | Construido, sin verificar | 0 / 2 | `ProductoNoEditorialAltaView` y `DuplicadosNoEditorialesView` (el aviso de homónimo de E2). |
| `CU-CAT-EDI` | Construido, sin verificar | 0 / 5 | `ProductoEdicionView`, con la ruptura del vínculo automático al fijar precio a mano. |
| `CU-CAT-BAJ` | Construido, sin verificar | 0 / 3 | `ProductoBajaView` con el informe de impacto previo (`catalog/services.py`). |
| `CU-CAT-REA` | Construido, sin verificar | 0 / 3 | `ProductoReactivarView`. Nadie comparó todavía lo construido contra el par solicitar/confirmar de CO-035 y CO-036. |
| `CU-CAT-INV` | Parcial | 0 / 3 | `ProductoListaView` y `ProductoDetalleView`, con ficha diferenciada por rol. Falta la exportación de CO-037: no hay ninguna salida a archivo en todo el repositorio. |
| `CU-CAT-ETQ` | Parcial | 0 / 11 | Alta, edición y cambio de grupo construidos (`EtiquetasView` y las vistas de parámetros). La baja de etiqueta y de grupo es una casilla `activa` dentro del formulario de edición, no el par solicitar/confirmar con informe de impacto que piden CO-040/041/044/045 (B-17-002). |

### `03` Pricing

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PVP-TAB` | Parcial | 0 / 7 | `TablaPrecioReferencia` con alta, edición y baja (`PrecioCrearView`, `PrecioEditarView`, `PrecioEliminarView`). **No propaga.** El CU declara que el cambio alcanza a los productos activos y a los carritos, y los pasos 3 a 5 —informe de cuántos productos se afectan, confirmación explícita, resumen en auditoría— tampoco existen. La propia pantalla lo dice: «cambiarlo acá no toca los productos ya cargados». Ver [DEUDA.md](DEUDA.md). |
| `CU-PVP-MAR` | Parcial | 0 / 4 | El margen se edita en `ParametrosView` y queda auditado. **No hay recálculo**: CO-053 exige recalcular todos los importados y propagar a los carritos. La parte de los carritos no puede cerrar antes de la cadena comercial. |
| `CU-PVP-ALT` | Pendiente | 0 / 2 | No existe el concepto Oferta. |
| `CU-PVP-EDI` | Pendiente | 0 / 2 | Ídem. |
| `CU-PVP-BAJ` | Pendiente | 0 / 4 | Ídem. |
| `CU-PVP-CON` | Pendiente | 0 / 3 | Ídem. |

### `04` Proveedores

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PRV-ALT` | Construido, sin verificar | 0 / 2 | `ProveedorAltaView`, con alta rápida de editorial sin salir de la pantalla. |
| `CU-PRV-EDI` | Construido, sin verificar | 0 / 3 | `ProveedorEdicionView`, con confirmación al cambiar el correo comercial. |
| `CU-PRV-CON` | Construido, sin verificar | 0 / 2 | `ProveedorListaView` y `ProveedorDetalleView`. |
| `CU-PRV-REA` | Construido, sin verificar | 0 / 3 | `ProveedorReactivarView`. Falta comparar lo construido contra CO-065 y CO-066. |
| `CU-PRV-COL` | Parcial | 0 / 5 | `CorreoListaView` y `CorreoDetalleView` sirven la cola y la ficha (CO-157, CO-158) y el descarte (CO-018). **No se puede aprobar un correo desde la pantalla**: la única decisión que el `POST` acepta es el descarte, y la aprobación de CO-017 se dispara con `manage.py extraer_novedades`. CO-016 tampoco existe. Ver [DEUDA.md](DEUDA.md). |
| `CU-PRV-BAJ` | Parcial | 0 / 3 | `ProveedorBajaView` con informe de impacto. El informe declara una de las dos cifras que pide el CU: las propuestas de restock quedan en `None` porque el módulo 05 no existe. Es un estado de construcción y no una deuda del contrato (B-04-001). |

### `05` Restock

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-RST-PED` | Construido, sin verificar | 0 / 2 | `suppliers/pedidos.py`, con reintento hasta tres veces. Lo invoca hoy el cierre de sesión de revisión de `CU-ALT-REV`. |
| `CU-RST-PRO` | Pendiente | 0 / 2 | No existe PropuestaRestock. |
| `CU-RST-APR` | Pendiente | 0 / 8 | Ídem. |
| `CU-RST-SUS` | Pendiente | 0 / 2 | No existe SuscripcionReposicion. |
| `CU-RST-NOT` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |

### `06` Ventas Presenciales

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-VTA-REG` | Pendiente | 0 / 7 | `MostradorView` es una pantalla placeholder: sólo fija el control de acceso del rol Cajero. |

### `07` Tienda Online

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | Pendiente | 0 / 3 | `TiendaView` es una pantalla placeholder: sólo fija el control de acceso del rol Cliente. |
| `CU-TDA-CAR` | Pendiente | 0 / 6 | No existe Carrito. |
| `CU-TDA-CMP` | Pendiente | 0 / 5 | No existe Pedido ni TransaccionPago. |
| `CU-TDA-INV` | Pendiente | 0 / 4 | Ídem. |

### `08` Gestión de Pedidos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PED-CON` | Pendiente | 0 / 2 | No existe Pedido. |
| `CU-PED-EST` | Pendiente | 0 / 3 | Ídem. |
| `CU-PED-OPC` | Pendiente | 0 / 5 | Ídem. |
| `CU-PED-CAN` | Pendiente | 0 / 1 | Ídem. |
| `CU-PED-CMP` | Pendiente | 0 / 1 | Ídem. |

### `09` Devoluciones

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-DEV-SOL` | Pendiente | 0 / 2 | No existe CasoDevolucion. |
| `CU-DEV-RES` | Pendiente | 0 / 5 | Ídem. |

### `10` Puntos

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PTS-CON` | Pendiente | 0 / 2 | No existen LotePuntos ni MovimientoPuntos. |
| `CU-PTS-CJE` | Pendiente | 0 / 3 | Ídem. |
| `CU-PTS-CAD` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |
| `CU-PTS-ADM` | Pendiente | 0 / 3 | Ídem. |

### `11` Cuenta de Cliente

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CLI-ALT` | Construido, sin verificar | 0 / 1 | `RegistroClienteView`, pantalla pública, con autocompletado de localidad desde `core/georef.py`. Lo que se acepta es la política de privacidad, que es lo que CO-107 declara. |
| `CU-CLI-CON` | Parcial | 0 / 2 | `ClienteListaView` cubre el listado de CO-194. **La ficha de cliente de CO-195 no existe.** Mismo criterio que `CU-USR-CON`: el CU declara dos operaciones y sólo una tiene pantalla. Si el listado alcanza para lo que la ficha promete es una ambigüedad a resolver en el plan del módulo, no acá. |
| `CU-CLI-DAT` | Pendiente | 0 / 4 | El Cliente no tiene panel propio: no hay pantalla de datos personales, ni cambio de correo, ni cambio de contraseña con sesión iniciada. |
| `CU-CLI-BAJ` | Pendiente | 0 / 3 | Depende de Pedidos, Puntos y Stock Almacenado para el mapeo de impacto. |
| `CU-CLI-HIS` | Pendiente | 0 / 2 | No existe Pedido. |

### `12` Autenticación

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-AUT-INI` | Construido, sin verificar | 1 / 2 | `LoginUsuarioView`, bloqueo por intentos fallidos (`IntentoFallido`), redirección por rol y expiración por inactividad con renovación. **CO-115 verificado.** CO-114 queda parcial: su postcondición nombra `ConfiguracionSistema` y los valores viven en `config/settings/base.py` (B-12-001). |
| `CU-AUT-FIN` | Construido, sin verificar | 1 / 1 | **Todos sus contratos verificados.** `LogoutUsuarioView`, con registro en auditoría por signal. CO-116 incluye su postcondición negativa: las sesiones de otros dispositivos no se tocan. Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-AUT-REC` | Construido, sin verificar | 2 / 2 | **Todos sus contratos verificados.** CO-117 y CO-118 se afirman ahora literalmente: `TokenRecuperacion` existe como concepto con sus tres estados (B-12-003). Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-AUT-ACT` | Construido, sin verificar | 3 / 3 | **Todos sus contratos verificados.** CO-119, CO-122 y CO-196. El `EnlaceActivacion` permite además distinguir E1 («vencido») de E2 («ya utilizado»), que antes se respondían igual. Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |

### `13` Gestión de Usuarios

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-USR-ALT` | Construido, sin verificar | 1 / 1 | **Todos sus contratos verificados.** CO-120 se afirma literalmente desde que existe `EnlaceActivacion`, incluida la vigencia de 48 horas y el estado Vigente. Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-USR-MOD` | Construido, sin verificar | 3 / 3 | **Todos sus contratos verificados.** CO-121, CO-122 y CO-197, incluidas las tres excepciones y la invalidación de sesión al cambiar el rol. Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-USR-BAJ` | Construido, sin verificar | 3 / 3 | **Todos sus contratos verificados.** CO-198 E1 pasó a cumplirse: la solicitud de baja del último Administrador se bloquea en el `GET` y no sólo al confirmar (B-13-003). Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-USR-REA` | Construido, sin verificar | 4 / 4 | **Todos sus contratos verificados.** La reactivación recibe el rol y la auditoría lo registra, que es lo que CO-124 y CO-199 declaraban y el código no hacía (B-13-002). Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-USR-ELI` | Construido, sin verificar | 3 / 3 | **Todos sus contratos verificados**, incluido el orden de CO-125 —auditoría antes del borrado— y las tres condiciones que impiden la eliminación. Sólo lo separa de `Verificado` la advertencia de `ALLOWED_HOSTS`. |
| `CU-USR-CON` | Parcial | 1 / 2 | `UsuarioListaView` cubre CO-201, con su prueba de acceso por la dirección real. **La ficha de usuario de CO-202 no existe** como pantalla propia. Mismo criterio que `CU-CLI-CON`: el CU declara dos operaciones y sólo una tiene pantalla. Si el listado y el formulario de edición alcanzan para lo que la ficha promete es una ambigüedad del plan del módulo. |

### `14` Caja

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAJ-CIE` | Pendiente | 0 / 3 | No existe CierreDeCaja. Depende de Ventas Presenciales. |

### `15` Reportes

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-REP-GEN` | Pendiente | 0 / 2 | No hay generación de reportes ni exportación a archivo. |

### `16` Auditoría

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-AUD-CON` | Parcial | 0 / 3 | `RegistroAuditoria` existe, es inmutable por diseño y declara 28 acciones. El panel del Administrador muestra las últimas entradas. No hay pantalla de consulta con filtros (CO-205), ni detalle de entrada (CO-206), ni exportación (CO-129). |

### `17` Configuración del Sistema

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CFG-LLM` | Construido, sin verificar | 0 / 3 | `DiagnosticoLLMView` y `core/llm.py`. El banco de muestras propio es el contenido de prueba que el paso 2 del CU declara (B-17-001). |
| `CU-CFG-PAR` | Parcial | 0 / 3 | `ParametrosView` expone margen, stock inicial por defecto y la configuración del modelo de lenguaje. El CU pide siete secciones: las que dependen de módulos no construidos no existen, y la de **Seguridad** —expiración por inactividad y período de bloqueo— sigue como constantes en `config/settings/base.py` (B-12-001). |
| `CU-CFG-EDT` | Parcial | 0 / 5 | Alta y edición construidas. La baja es una casilla `activa` dentro del formulario, no el par solicitar/confirmar con informe de impacto de CO-139/140 (B-17-002). |
| `CU-CFG-TIP` | Parcial | 0 / 10 | Alta y edición de `Tipo` y `Formato` construidas, con la tabulación de formatos por tipo. La baja de formato es una casilla, no el par CO-147/148 (B-17-002), y no hay confirmación del cambio de tabulación de CO-143. La baja de **tipo** es un caso aparte: existe y ningún contrato la declara — ver [DEUDA.md](DEUDA.md). |
| `CU-CFG-BAN` | Pendiente | 0 / 4 | No existe Banner. |
| `CU-CFG-FAQ` | Pendiente | 0 / 3 | No existe ContenidoFAQ. |
| `CU-CFG-VIS` | Pendiente | 0 / 2 | Los tokens visuales están escritos a mano en `templates/base.html`; no hay entidad ni pantalla que los edite. |

### `18` Stock Almacenado en Local

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-STK-CON` | Pendiente | 0 / 1 | No existe ArticuloRetenido. |
| `CU-STK-DES` | Pendiente | 0 / 5 | Ídem. |
| `CU-STK-ADM` | Pendiente | 0 / 4 | Ídem. |
| `CU-STK-VEN` | Pendiente | 0 / 1 | Ídem, y depende además de P-05. |

---

## Las siete puertas

Se corrieron las siete sobre el repositorio entero, con PostgreSQL levantado. Es una medición
global: dice el estado de cada puerta para todo el código, no por caso de uso.

| Puerta | Resultado |
| --- | --- |
| Suite de pruebas | **1334 pasan**, 0 fallos, **0 xfail**, 5 min 53 s |
| **Contratos** | **18 de 218 verificados**, 1 parcial, 199 sin prueba. Todos del módulo 12 y del 13 |
| Cobertura sobre código de aplicación | **97 %** (4381 sentencias, 153 sin cubrir) |
| Análisis estático | `ruff check apps config scripts` — sin hallazgos |
| Formato | `black --check` — 145 archivos sin cambios |
| Auditoría de seguridad | `bandit -r apps config scripts` — sin hallazgos |
| Configuración de despliegue | **1 advertencia**: `security.W020`, `ALLOWED_HOSTS` vacío |

Las tres últimas cubren ahora también `scripts/`, que dejó de estar fuera del repositorio.

**Sobre la advertencia de despliegue.** `ALLOWED_HOSTS` sale del entorno en
`config/settings/production.py`, con `""` por defecto, y `.env.example` lo deja en blanco. No hay
valor configurado en ninguna parte del repositorio porque el host de producción todavía no está
decidido. La puerta queda en amarillo hasta que lo esté, y es lo único que separa a nueve casos de
uso del estado `Verificado`.

**Cinco archivos quedan por debajo del 90 %**, y uno importa más que los otros cuatro:

| Archivo | Cobertura | Qué queda sin cubrir |
| --- | --- | --- |
| `apps/suppliers/management/commands/ingerir_correos.py` | **0 %** | El comando entero. Es la vía de ingesta que hoy ocupa el lugar de CO-016 |
| `apps/core/utils.py` | 75 % | La rama sin `REMOTE_ADDR` de `obtener_ip` |
| `apps/accounts/management/commands/crear_administrador_inicial.py` | 81 % | Las ramas interactivas: `input()` y `getpass()` no se ejercen desde la suite |
| `apps/core/management/commands/respaldar_base.py` | 85 % | Las ramas de error del volcado |
| `apps/core/integraciones.py` | 89 % | Ramas de degradación de la puerta HTTP |

El 97 % global las tapa: ninguna hace caer la puerta, y `ingerir_correos.py` al 0 % no se ve en el
número agregado.

---

## Lo que esta fotografía no cubre

- **200 de los 218 contratos siguen sin verificar.** Lo cubierto son dos módulos de diez casos de
  uso; los otros 65 siguen apoyados sólo en las pruebas descriptivas. El 97 % de cobertura dice
  que las líneas se ejecutaron, no que el efecto que el contrato declara se cumpla.
- **La columna «Contratos» no mide calidad.** Un contrato verificado es uno cuyas postcondiciones
  tienen prueba; que el contrato sea el correcto es otra pregunta, y la responde la bitácora.
- **La concurrencia de I-12 no se probó.** Dos administradores quitándose el rol a la vez es un
  caso declarado del foco reforzado; el resguardo usa `select_for_update()` y este pase verifica
  el resultado, no la carrera.
- **La lectura es del código, no de la pantalla.** Ningún caso de uso se ejercitó a mano contra el
  servidor de desarrollo. Las dos verificaciones que `CLAUDE.md` pide a mano sí se hicieron: las
  migraciones aplican sobre la base de desarrollo y `migrate --check` sale en 0.
- **El estado `Parcial` es un juicio sobre el alcance, no sobre la calidad.** Dice que falta una
  parte declarada del caso de uso, no que lo construido esté mal.
- **No se revisaron las pantallas contra `TOKENS_VISUALES.md`.** El avance visual no entra acá.
