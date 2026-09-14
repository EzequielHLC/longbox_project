> **Tipo: Fotografía.** Tomada el **2026-09-14**, del repositorio y no de memoria.
> Se reemplaza entera. No contiene reglas: si acá aparece una, está mal ubicada.

# Estado de construcción

Autoridad única del avance por caso de uso. Ningún otro archivo del proyecto informa estado; todos
enlazan a éste.

---

## Resumen

Primera fotografía del proyecto. Se tomó leyendo el código —modelos, rutas, vistas, servicios y
pruebas— y contrastándolo contra `.contexto-ia/INDICE.md` y los contratos de cada módulo, no
contra documentación previa.

La suite corre en verde: **1306 pruebas, 0 fallos, 97 % de cobertura**. Cinco de las siete puertas
pasan limpias sobre el repositorio entero, una queda en amarillo y una no pasa; el detalle está más
abajo.

**La puerta de contratos empezó a abrirse.** Los módulos `12` Autenticación y `13` Gestión de
Usuarios —los dos únicos con todos sus casos de uso construidos— tienen ahora pruebas de contrato:
94 pruebas nuevas, nombradas con el código del contrato que verifican. **10 contratos de 218 están
verificados por completo.**

**Aun así, ningún caso de uso figura como `Verificado`, y no es un descuido.** `Verificado` exige
las siete puertas, y la de configuración de despliegue tiene una advertencia abierta
(`ALLOWED_HOSTS`). Dos casos de uso —`CU-AUT-FIN` y `CU-USR-ELI`— tienen **todos** sus contratos
verificados y quedan a esa sola advertencia de alcanzar el estado. El resto del módulo 12 y 13
tiene contratos parciales o incumplidos, y la columna de cada fila dice cuántos.

| | |
| --- | --- |
| Casos de uso especificados | 75 |
| Verificados | 0 |
| Construidos, sin verificar | 26 |
| Parciales | 11 |
| En curso | 0 |
| Pendientes | 38 |
| Bloqueados | 0 |

Contratos de operación especificados: **218**. Verificados por completo: **10**. Parciales: **6**.
Incumplidos: **3**. El detalle está en [DEUDA.md](DEUDA.md).

La columna **Contratos** de cada tabla dice *cuántos contratos de los que el caso de uso referencia
tienen prueba que verifique **todas** sus postcondiciones*, sobre el total que referencia. Un
contrato cuya postcondición nombra un concepto `<<planificado>>` no cuenta como verificado aunque
su efecto observable sí se pruebe: la observación de cada fila dice cuál es el caso.

La columna suma 12 y los contratos verificados son 10: `CO-156` lo referencian tres casos de uso y
`CO-122` dos, así que un mismo contrato aparece en varias filas. El total cuenta contratos
distintos.

---

## Por módulo

### `01` Alta Editorial

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-ALT-NAC` | Construido, sin verificar | 0 / 8 | `AltaLoteNacionalView`, `catalog/services.py`, `catalog/precios.py`. Con pruebas propias (`test_alta_lote_nacional.py`). |
| `CU-ALT-IMP` | Construido, sin verificar | 0 / 11 | `AltaLoteImportadoView`, calculadora de envío y CRE en `LoteAlta`, cotización desde `core/cotizaciones.py`. |
| `CU-ALT-NOV` | Parcial | 0 / 6 | Extracción, cola de correos y generación de borradores construidas (`suppliers/correos.py`, `extraccion.py`, `catalog/borradores.py`). Falta el ciclo de monitoreo de casilla de CO-016: hoy la ingesta se dispara a mano con `manage.py ingerir_correos`. |
| `CU-ALT-REV` | Construido, sin verificar | 0 / 10 | `BorradorListaView`, `BorradorDetalleView`, `ConfirmarEnLoteView`, `CerrarSesionRevisionView`, `catalog/revisiones.py`, `ConfianzaCampo`. |
| `CU-ALT-DEM` | Parcial | 0 / 3 | Los campos existen (`ProductoEditorial.demorado`, `fecha_estimada`, `nota_demora`, `llegada_vigente`) y el inventario muestra el indicador. No hay pantalla de registro de demora (CO-014/CO-015) ni notificación a clientes: depende de Pedidos. |
| `CU-ALT-TRA` | Pendiente | 0 / 5 | El estado Pre-venta existe en `Producto`. No existe el ciclo de vigilancia (CO-011), ni el escalado por inacción (CO-012), ni la confirmación de ingreso de lote (CO-013). |
| `CU-ALT-CAN` | Pendiente | 0 / 3 | El estado terminal `Cancelado` existe en `Producto`. El flujo de cancelación en lote y el reembolso en puntos no: dependen de Pedidos y Puntos. |

### `02` Catálogo

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CAT-ALT` | Construido, sin verificar | 0 / 2 | `ProductoNoEditorialAltaView` y `DuplicadosNoEditorialesView` (el aviso de homónimo de E2). |
| `CU-CAT-EDI` | Construido, sin verificar | 0 / 5 | `ProductoEdicionView`, con la ruptura del vínculo automático al fijar precio a mano. |
| `CU-CAT-BAJ` | Construido, sin verificar | 0 / 3 | `ProductoBajaView` con el informe de impacto previo (`catalog/services.py`). |
| `CU-CAT-REA` | Construido, sin verificar | 0 / 3 | `ProductoReactivarView`. El docstring de la vista afirma que ningún CU la describe; `CU-CAT-REA` la describe — ver [DEUDA.md](DEUDA.md). |
| `CU-CAT-INV` | Parcial | 0 / 3 | `ProductoListaView` y `ProductoDetalleView`, con ficha diferenciada por rol. Falta la exportación de CO-037: no hay ninguna salida a archivo en todo el repositorio. |
| `CU-CAT-ETQ` | Parcial | 0 / 11 | Alta, edición y cambio de grupo construidos (`EtiquetasView` y las vistas de parámetros). La baja de etiqueta y de grupo es una casilla `activa` dentro del formulario de edición, no el par solicitar/confirmar con informe de impacto que piden CO-040/041/044/045. |

### `03` Pricing

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-PVP-TAB` | Construido, sin verificar | 0 / 7 | `TablaPrecioReferencia` con alta, edición y baja (`PrecioCrearView`, `PrecioEditarView`, `PrecioEliminarView`). |
| `CU-PVP-MAR` | Parcial | 0 / 4 | El margen se edita en `ParametrosView` y queda auditado. **No hay recálculo**: la propia pantalla avisa que «los productos ya cargados conservan el margen con el que se dieron de alta», y CO-053 exige recalcular todos los importados y propagar a los carritos. Ver [DEUDA.md](DEUDA.md). |
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
| `CU-PRV-REA` | Construido, sin verificar | 0 / 3 | `ProveedorReactivarView`. Su docstring afirma que ningún CU la describe; `CU-PRV-REA` la describe — ver [DEUDA.md](DEUDA.md). |
| `CU-PRV-COL` | Construido, sin verificar | 0 / 5 | `CorreoListaView` y `CorreoDetalleView`, con la aprobación explícita de cada correo. El docstring afirma que la pantalla «no sale de ningún caso de uso»; `CU-PRV-COL` la describe — ver [DEUDA.md](DEUDA.md). |
| `CU-PRV-BAJ` | Parcial | 0 / 3 | `ProveedorBajaView` con informe de impacto. El informe declara una de las dos cifras que pide el CU: las propuestas de restock afectadas quedan en `None` porque el módulo 05 no existe (`ImpactoDeBaja.propuestas_de_restock`). |

### `05` Restock

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-RST-PED` | Construido, sin verificar | 0 / 2 | `suppliers/pedidos.py`, con reintento hasta tres veces. Lo invoca hoy el cierre de sesión de revisión de `CU-ALT-REV`. |
| `CU-RST-PRO` | Pendiente | 0 / 2 | No existe PropuestaRestock. |
| `CU-RST-APR` | Pendiente | 0 / 8 | Ídem. |
| `CU-RST-SUS` | Pendiente | 0 / 2 | No existe SuscripcionReposicion. |
| `CU-RST-NOT` | Pendiente | 0 / 1 | Ídem. |

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
| `CU-PTS-CAD` | Pendiente | 0 / 1 | Ídem. |
| `CU-PTS-ADM` | Pendiente | 0 / 3 | Ídem. |

### `11` Cuenta de Cliente

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CLI-ALT` | Construido, sin verificar | 0 / 1 | `RegistroClienteView`, pantalla pública, con autocompletado de localidad desde `core/georef.py`. |
| `CU-CLI-CON` | Parcial | 0 / 2 | `ClienteListaView` cubre el listado (CO-194). No hay ficha de cliente (CO-195). El docstring de la vista afirma que no es un CU; `CU-CLI-CON` la describe — ver [DEUDA.md](DEUDA.md). |
| `CU-CLI-DAT` | Pendiente | 0 / 4 | El Cliente no tiene panel propio: no hay pantalla de datos personales, ni cambio de correo, ni cambio de contraseña con sesión iniciada. |
| `CU-CLI-BAJ` | Pendiente | 0 / 3 | Depende de Pedidos, Puntos y Stock Almacenado para el mapeo de impacto. |
| `CU-CLI-HIS` | Pendiente | 0 / 2 | No existe Pedido. |

### `12` Autenticación

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-AUT-INI` | Construido, sin verificar | 1 / 2 | `LoginUsuarioView`, bloqueo por intentos fallidos (`IntentoFallido`), redirección por rol y expiración por inactividad con renovación (`renovar_sesion`). CO-115 verificado. CO-114 verificado salvo «según `ConfiguracionSistema`» (B-12-001). |
| `CU-AUT-FIN` | Construido, sin verificar | 1 / 1 | `LogoutUsuarioView`, con registro en auditoría por signal. **CO-116 verificado**, incluida su postcondición negativa: las sesiones de otros dispositivos no se tocan. |
| `CU-AUT-REC` | Construido, sin verificar | 0 / 2 | Los cuatro pasos del flujo de recuperación, con token de 30 minutos (`accounts/tokens.py`). Los dos contratos quedan parciales: sus postcondiciones nombran `TokenRecuperacion`, concepto `<<planificado>>` que no existe como tabla (B-12-002). Lo observable sí se verifica. |
| `CU-AUT-ACT` | Construido, sin verificar | 1 / 3 | `ActivarCuentaView` con token de 48 horas, y `ReenviarActivacionView`. CO-196 verificado. CO-119 y CO-122 parciales por `EnlaceActivacion` (B-12-002). |

### `13` Gestión de Usuarios

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-USR-ALT` | Construido, sin verificar | 0 / 1 | `UsuarioAltaView`, con correo de activación. CO-120 verificado salvo «(a) se creó ea : EnlaceActivacion» y «(b) ea → u» (B-12-002). |
| `CU-USR-MOD` | Construido, sin verificar | 2 / 3 | `UsuarioEdicionView`. **CO-121 y CO-197 verificados**, incluidas las tres excepciones y la invalidación de sesión al cambiar el rol. CO-122 parcial por `EnlaceActivacion`. |
| `CU-USR-BAJ` | Construido, sin verificar | 2 / 3 | `UsuarioBajaView`. **CO-123 y CO-156 verificados**, incluida la postcondición negativa del historial. CO-198 E1 **no se cumple**: la baja del último Administrador se ofrece y recién se rechaza al confirmar (B-13-003). |
| `CU-USR-REA` | Construido, sin verificar | 1 / 4 | `UsuarioReactivarView`. CO-156 verificado. **CO-124 no se cumple**: no recibe el rol que el contrato exige elegir, y la auditoría no lo registra. CO-199 tampoco: la pantalla no deja modificarlo (B-13-002). |
| `CU-USR-ELI` | Construido, sin verificar | 3 / 3 | `UsuarioEliminarPendienteView`. **Los tres contratos verificados**, incluido el orden de CO-125 —auditoría antes del borrado— y las tres condiciones que impiden la eliminación. |
| `CU-USR-CON` | Construido, sin verificar | 1 / 2 | `UsuarioListaView`. **CO-201 verificado**, con su prueba de acceso por la dirección real. CO-202 sin cubrir: no hay ficha de usuario separada; el listado y el formulario de edición cubren lo que el CU pide mostrar. |

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
| `CU-AUD-CON` | Parcial | 0 / 3 | `RegistroAuditoria` existe, es inmutable por diseño y declara 27 acciones. El panel del Administrador muestra las últimas entradas. No hay pantalla de consulta con filtros (CO-205), ni detalle de entrada (CO-206), ni exportación (CO-129). |

### `17` Configuración del Sistema

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-CFG-LLM` | Construido, sin verificar | 0 / 3 | `DiagnosticoLLMView` y `core/llm.py`. El comentario de `suppliers/urls.py` lo declara «herramienta de operación, no de ningún CU»; `CU-CFG-LLM` lo describe — ver [DEUDA.md](DEUDA.md). |
| `CU-CFG-PAR` | Parcial | 0 / 3 | `ParametrosView` expone margen, stock inicial por defecto y la configuración del modelo de lenguaje. El CU pide siete secciones (Catálogo y Preventa, Logística, Comercial, Inventario y Restock, Proveedores, Fidelización, Seguridad): las que dependen de módulos no construidos no existen, y el bloqueo por intentos fallidos sigue siendo constante en `config/settings/base.py`. |
| `CU-CFG-EDT` | Parcial | 0 / 5 | Alta y edición construidas. La baja es una casilla `activa` dentro del formulario, no el par solicitar/confirmar con informe de impacto de CO-139/140. |
| `CU-CFG-TIP` | Parcial | 0 / 10 | Alta y edición de `Tipo` y `Formato` construidas, con la tabulación de formatos por tipo. La baja es una casilla `activo`, no el par solicitar/confirmar de CO-147/148, y no hay confirmación del cambio de tabulación de CO-143. |
| `CU-CFG-BAN` | Pendiente | 0 / 4 | No existe Banner. |
| `CU-CFG-FAQ` | Pendiente | 0 / 3 | No existe ContenidoFAQ. |
| `CU-CFG-VIS` | Pendiente | 0 / 2 | Los tokens visuales están escritos a mano en `templates/base.html`; no hay entidad ni pantalla que los edite. |

### `18` Stock Almacenado en Local

| Caso de uso | Estado | Contratos | Observación |
| --- | --- | --- | --- |
| `CU-STK-CON` | Pendiente | 0 / 1 | No existe ArticuloRetenido. |
| `CU-STK-DES` | Pendiente | 0 / 5 | Ídem. |
| `CU-STK-ADM` | Pendiente | 0 / 4 | Ídem. |
| `CU-STK-VEN` | Pendiente | 0 / 1 | Ídem. |

---

## Escala

| Valor | Significa |
| --- | --- |
| `Pendiente` | No se empezó |
| `En curso` | Se está trabajando ahora |
| `Construido, sin verificar` | El código existe y la suite pasa, pero nadie comprobó que cumpla las postcondiciones de sus contratos |
| `Verificado` | Pasó las siete puertas, incluida la de contratos |
| `Parcial` | Terminado en parte. La observación dice qué falta |
| `Bloqueado` | No puede avanzar. La observación dice qué lo bloquea |

**Sobre `Construido, sin verificar`.** Es el estado de todo lo que se escribió antes de que
existieran los contratos. No es una etiqueta transitoria ni un defecto: es información. La cola de
reconciliación que genera es trabajo real y conviene que se vea en vez de quedar escondida bajo
`Verificado`.

---

## Las siete puertas

Se corrieron las siete sobre el repositorio entero, con PostgreSQL levantado. Es una medición
global: dice el estado de cada puerta para todo el código, no por caso de uso.

| Puerta | Umbral | Resultado |
| --- | --- | --- |
| Suite de pruebas | Sin fallos | **1306 pasan**, 0 fallos, 4 xfail declarados, 5 min 43 s |
| **Contratos** | Cada operación tiene prueba que verifica sus postcondiciones | **10 de 218 verificados**, 6 parciales, 3 incumplidos. Todos del módulo 12 y del 13 |
| Cobertura sobre código de aplicación | No inferior al 80 % | **97 %** (4308 sentencias, 136 sin cubrir) |
| Análisis estático | Sin hallazgos | `ruff check apps config` — sin hallazgos |
| Formato | Sin diferencias | `black --check` — 140 archivos sin cambios |
| Auditoría de seguridad | Sin hallazgos sin justificación | `bandit -r apps config` — sin hallazgos |
| Configuración de despliegue | Sin advertencias | **1 advertencia**: `security.W020`, `ALLOWED_HOSTS` vacío |

**Sobre la advertencia de despliegue.** `ALLOWED_HOSTS` sale del entorno en
`config/settings/production.py`, con `""` por defecto, y `.env.example` lo deja en blanco. No hay
valor configurado en ninguna parte del repositorio porque el host de producción todavía no está
decidido. La puerta queda en amarillo hasta que lo esté.

**Cuatro archivos quedan por debajo del 90 %**, y uno importa más que los otros tres:

| Archivo | Cobertura | Qué queda sin cubrir |
| --- | --- | --- |
| `apps/suppliers/management/commands/ingerir_correos.py` | **0 %** | El comando entero. Es la vía de ingesta que hoy ocupa el lugar de CO-016 (ver `CU-ALT-NOV`) |
| `apps/core/utils.py` | 75 % | La rama sin `REMOTE_ADDR` de `obtener_ip` |
| `apps/core/management/commands/respaldar_base.py` | 85 % | Las ramas de error del volcado |
| `apps/core/integraciones.py` | 89 % | Ramas de degradación de la puerta HTTP |

El 97 % global las tapa: ninguna de las cuatro hace caer la puerta, y `ingerir_correos.py` al 0 %
no se ve en el número agregado.

---

## Lo que esta fotografía no cubre

- **208 de los 218 contratos siguen sin verificar.** Lo cubierto son dos módulos de diez casos de
  uso; los otros 65 siguen apoyados sólo en las pruebas descriptivas. El 97 % de cobertura dice que
  las líneas se ejecutaron, no que el efecto que el contrato declara se cumpla.
- **Las cuatro pruebas en `xfail(strict=True)` no son deuda escondida.** Marcan tres contratos que
  el sistema no cumple —CO-124, CO-198 y CO-199— y están anotadas en las bitácoras de sus módulos.
  Si alguna empezara a pasar, la suite falla y avisa.
- **La concurrencia de I-12 no se probó.** Dos administradores quitándose el rol a la vez es un
  caso declarado del foco reforzado; el resguardo usa `select_for_update()` y este pase verifica el
  resultado, no la carrera.
- **La lectura es del código, no de la pantalla.** Ningún caso de uso se ejercitó a mano contra el
  servidor de desarrollo: un flujo puede estar escrito y caído por una migración sin aplicar, y
  esta fotografía no lo distinguiría.
- **El estado `Parcial` es un juicio sobre el alcance, no sobre la calidad.** Dice que falta una
  parte declarada del caso de uso, no que lo construido esté mal.
- **No se revisaron las pantallas contra `TOKENS_VISUALES.md`.** El avance visual no entra acá.
