> **Tipo: Fotografía.** Tomada el **2026-10-19**.
> Se reemplaza entera. No contiene reglas ni justificaciones de diseño.

# Deuda

La diferencia entre lo que el documento de análisis especifica y lo que el sistema hace, y las
decisiones que todavía no se tomaron.

Es el complemento de [`ESTADO.md`](ESTADO.md): aquél dice cuánto se avanzó; éste, qué separa al
código de la especificación.

---

## Consultas pendientes para el responsable

Las preguntas de la sesión del 2026-09-30, **ordenadas por lo que desbloquean**. Cada una remite
al plan o a la sección donde está desarrollada.

### Resueltas hoy

| # | Consulta | Resolución | Registrada en |
| --- | --- | --- | --- |
| C-01 | ¿Se retira Tailwind? | Sí | B-00-001 |
| C-02 | Encabezado público sin identidad; aviso de sesión | Recomendación del plan, sin objeción | B-00-002, B-00-003 |
| C-03 | ¿«Aplica a todos los tipos» es atributo de `Formato`? | Sí, es atributo | B-17-004 |
| C-04 | Acciones de auditoría de catálogos y contenido | Delegada: se eligieron once acciones nuevas | B-17-005 |
| C-05 | Valor inicial del intervalo del carrusel | 10 segundos | B-17-003 |
| C-06 | Dueño de la portada y de la página de FAQ públicas | El Administrador, a través de sus casos de uso: se construyen como parte de `CU-CFG-FAQ` y de los banners | Pendiente de construir |
| C-07 | Alcance de `IdentidadVisual` y fondo con imagen | El fondo de la tienda puede ser imagen | Pendiente de construir |
| C-08 | `CO-017` E4 frente al código | Mandan los contratos | B-04-004 |
| C-09, C-10 | Reprocesamiento que falla; extracción dentro de la petición | Recomendación del plan, sin objeción | B-04-005 |
| C-11 | Margen global con cancelados y sin importados | Mandan los contratos: `CO-053` recalcula todo importado con precio vinculado, y sin importados la precondición de `CO-052` no se cumple | Pendiente de construir |
| C-17 | `cancelarOperacion` en siete DSS | El responsable entregó los apartados corregidos en `.contexto-ia/dss/DSS.md-apartados-que-cambian.md`. **Falta incorporarlos a `DSS.md`**, que mantiene el responsable | — |
| C-18 | PostgreSQL detenido | Levantado | — |
| C-12 | Ofertas vigentes en el informe de baja de tipo | Recomendación del plan, sin objeción: «No disponible» | B-17-008 |
| C-13 | Filtros del catálogo público en grupos y etiquetas | Recomendación del plan, sin objeción: quedan parciales hasta `CU-TDA-CAT` | B-02-004 |
| C-14 | Formato de la exportación de inventario | Recomendación del plan, sin objeción: CSV | — |
| C-15 | Filtros por acción y por rol en el log | Recomendación del plan, sin objeción: acciones agrupadas y rol actual | B-16-001, B-16-002 |
| C-16 | Markdown de la FAQ | Recomendación del plan, sin objeción: sin HTML crudo | — |
| C-22 | El cambio de producto: `CO-100` y `DevolucionFisica` frente a DME-12 y DME-16 | Mandan la ficha, el contrato y el diagrama de clases; los DME están desactualizados (2026-10-16) | R-09-001 |
| C-20 | ¿La portada de la tienda se ve sin iniciar sesión? | Sí, el 2026-10-05: la ve un invitado y cualquier rol, y la raíz del sitio lleva a ella | B-07-019 |

### Siguen abiertas

| # | Consulta | Dónde está | Qué desbloquea |
| --- | --- | --- | --- |
| C-19 | `CO-052` y `CU-PVP-MAR` exigen que exista al menos un importado. Con la palabra del contrato, en una instalación sin importados el margen no se puede cambiar desde ninguna pantalla, porque `CU-CFG-PAR` tampoco lo edita. Construido así (B-03-003) | Plan 03, ambigüedad 2 | Una enmienda de `CO-052`, si no es lo que se quiere |
| C-21 | El logo no admite SVG porque RNF-05 convierte toda imagen a WebP. ¿Se enmienda la guía de `CU-CFG-VIS` o se exceptúa el logo de RNF-05? | B-17-011 | La guía de formato del logo |

---

## Decisiones transversales abiertas

| Ítem | Decisión pendiente | Qué bloquea | Desde |
| --- | --- | --- | --- |
| **P-05** · procesos periódicos | **Resuelta la forma** el 2026-10-03: `manage.py ejecutar_temporizador` es la puerta única; corre al arrancar `demostracion.bat` y se programa una vez por día (B-03-007). Hoy corre `CO-059`, `CO-011`, `CO-012`, `CO-096`, `CO-097`, `CO-154`, `CO-067`, `CO-105` con su aviso previo, `CO-016`, `CO-155` y el descarte de cobros abandonados. Falta sumar cada proceso cuando exista su caso de uso | Ninguno del alcance. La limpieza de carritos de invitado queda descartada (ver «Recorte para el cierre») | — |
| ~~Parámetros de seguridad~~ | **Construido el 2026-10-19** (B-12-004) | — | — |
| ~~Pedido como dependencia raíz~~ | **Resuelta el 2026-10-09**: la compra online crea `Pedido`, `LineaPedido`, `TransaccionPago`, `LotePuntos` y `MovimientoPuntos` (plan 07, sexta parte). El orden propuesto para lo que sigue está al final de ese plan | — | — |
| MercadoPago sin probar contra su API | El adaptador está construido y probado contra respuestas declaradas (B-07-031). Falta cargar `MERCADOPAGO_ACCESS_TOKEN` de una cuenta de prueba y recorrer un pago real con el aviso llegando por el túnel | Mostrar un pago real en la demostración | 2026-10-09 |
| Costo de envío por operador logístico | Hoy es un importe fijo de Parámetros (B-07-032). Cotizar con Correo Argentino (API MiCorreo o tabla por zona) exige una cuenta comercial y **el peso de cada producto**, que el modelo no tiene | Un costo de envío según peso y destino | 2026-10-09 |
| ~~Cobros en curso abandonados~~ | **Resuelto el 2026-10-19**: el Temporizador los descarta y un pago tardío se reembolsa (B-07-039) | — | — |
| Carreras de unicidad no ensayadas | El doble envío de un alta con datos únicos terminaba en 500 en catálogos y proveedores (B-17-016, B-04-006, corregidos). No se ensayaron el alta de productos (ISBN, código de barras, código interno), el registro de clientes (correo) ni el alta de personal | Que esas altas respondan con el aviso de duplicado y no con un 500 ante un doble clic | 2026-10-04 |
| `04_RESUMEN.md` | `MODELO_DE_DOMINIO.md` lo cita y el archivo no está en el repositorio | Saber cuáles son las «cuatro operaciones con contrato pausado» | 2026-09-14 |

---

## Recorte para el cierre

Decidido por el responsable el 2026-10-19 ([planes/00-revision-funcional.md](planes/00-revision-funcional.md)):
el código se termina antes de noviembre, así que se corrige lo que hace aguas, se completa lo que
el alcance promete y **se descarta lo demás como próxima implementación**, con su justificación. Su
lugar en el documento es la tabla «Alcance construido y alcance especificado».

| Se descarta | Justificación |
| --- | --- |
| Reclamo como ticket con conversación | No está en el alcance; Devoluciones es prioridad Media y de frecuencia baja. El correo o el teléfono cumplen la función |
| Prueba de destrucción dentro del sistema | Se pide y se ve por el canal externo; el sistema registra la resolución |
| Reembolso en pesos por la API de la pasarela | Exigiría transacciones negativas en la caja (I-09) y probar la API real. Se devuelve desde el panel de la pasarela y el sistema lo registra |
| Anexar lo guardado en el local al próximo pedido | Comodidad; ya existen el envío pago, el gratis desde el mínimo y el retiro |
| Vincular pedidos de invitado a una cuenta | El registro no verifica el correo. El botón de arrepentimiento por número de pedido y correo cubre lo que el invitado necesitaba |
| Estado «Entregado» y plazo desde la recepción | Límite declarado: «No rastreará el paquete más allá del estado Despachado» |
| Limpieza de carritos de invitado y aviso de carrito abandonado | Sin caso de uso; sólo un parámetro en el modelo |
| Costo de envío por peso y destino | Requiere el peso de cada producto y una cuenta comercial con el operador |

**Lo que el tutor tiene que confirmar**: los valores legales de los plazos (arrepentimiento, piso
10 días; garantía, 90 por defecto) y si el envío se reintegra en un arrepentimiento parcial. Los
dos son parámetros o una regla chica: cambiarlos no toca el diseño.

---

## Consistencia de la especificación consigo misma

Resultado de `scripts/generar_contexto.py` del 2026-09-30. Compara el documento contra sí mismo y
contra `dss/DSS.md`, **por nombre de operación**. Informa y no corrige. El inventario de
operaciones ya no existe, y con él desaparecieron las observaciones que esta sección hacía sobre
su numeración.

El generador terminó con «Ninguno desapareció ni cambió» sobre los 9 archivos protegidos, entre
ellos `TOKENS_VISUALES.md` e `identidad_visual.md`. En la consola de Windows hay que correrlo con
`PYTHONIOENCODING=utf-8`: sin eso aborta a mitad de la verificación con `UnicodeEncodeError`.

| Observación | Detalle | ¿Toca esta sesión? |
| --- | --- | --- |
| **`cancelarOperacion` ausente de siete DSS** | Los apartados de `CU-CAT-REA`, `CU-PRV-REA`, `CU-USR-BAJ`, `CU-USR-REA`, `CU-USR-ELI`, `CU-CLI-BAJ` y `CU-STK-DES` no la muestran. `CO-156` sí los referencia. El apartado de `CU-PED-OPC` sí muestra al Temporizador (`ejecutarCicloDeVencimientoDeVentanaDeDecision`) | Sí: `CU-CAT-REA` y `CU-PRV-REA` reciben su prueba de `CO-156` desde el contrato. Consulta C-17 |
| 6 huecos en la numeración | `CO-219`, `CO-222` a `CO-226` | No: un contrato que no está en `.contexto-ia/` no se implementa. `CO-219` es el del tablero del Administrador, en camino |
| `CO-155 sincronizarCotizaciones` sin caso de uso ni DSS | Archivado por posición en el módulo 18. Defecto conocido | No |
| `CO-059` sin caso de uso con ficha | Es la mención de `CU-PVP-VEN`, decidido y sin ficha hasta la sección 5. Esperado | No |
| Cinco códigos retirados todavía mencionados | `CU-CAT-ETQ`, `CU-CFG-BAN`, `CU-CFG-EDT`, `CU-CFG-TIP` y `CU-PVP-TAB`, en las tablas «Estado de Construcción» y «Plan de Iteración» del documento | No toca el código. Es una enmienda del documento |
| 57 operaciones que un contrato asocia a un caso de uso cuyo DSS no las muestra | Informativo. Salvo las siete de `cancelarOperacion`, todas son contexto: consultas previas (`consultarEditoriales` desde `EDA`), invocaciones desde otro caso de uso (`registrarEditorial` desde las altas de lote) o la fusión del carrito, que pasó de `CU-TDA-CRC` a `CU-AUT-INI` | No son deuda |
| Trazabilidad con requisitos | Sin observaciones | — |

**Dos atributos que los contratos o las fichas usan y el modelo de dominio no declara:**

| Atributo | Quién lo usa | Estado |
| --- | --- | --- |
| `ConfiguracionSistema` · intervalo del carrusel | Ficha de `CU-CFG-PAR` (sección Tienda), `CU-CFG-BNC` | Construido con 10 s (B-17-003). Falta la enmienda del modelo |
| `Formato` · aplica a todos los tipos | `CO-144`, `CO-145`, `CO-146`, `CO-049` y las fichas de formatos y tipos | Construido como atributo (B-17-004). Falta la enmienda del modelo |

**`CO-131` y la ficha de `CU-CFG-VIS` siguen diciendo que P-07 está abierta.** Se construyó con
la respuesta a C-07: las cuatro variables `--tienda-*` y el fondo con imagen. Falta quitar la nota
del documento.

---

## Conceptos especificados sin implementar

Fuente: `MODELO_DE_DOMINIO.md` contrastado contra las clases del código. Desde la fotografía
anterior se construyeron `Oferta` (plan 03), `Carrito` y `LineaCarrito` (plan 07, segunda parte),
y `Pedido`, `LineaPedido`, `TransaccionPago`, `LotePuntos` y `MovimientoPuntos` (plan 07, sexta
parte), `CierreDeCaja` (plan 14), y `ArticuloRetenido`, `PropuestaRestock`,
`LineaPropuestaRestock` y `SuscripcionReposicion` (planes 18 y 05), y `CasoDevolucion` y
`DevolucionFisica` (plan 09). **No queda ninguno.** La evidencia del caso es una tabla propia
(una o más fotos por caso), no un concepto nuevo: el modelo la declara como atributo.

**El estado «Reservado para cambio» de `ArticuloRetenido` queda sin uso**: venía de DME-12, que
está desactualizado (R-09-001). La confirmación del retiro físico (`DevolucionFisica` → Retirado)
no tiene caso de uso; el concepto guarda la fecha para cuando exista.

**Un registro técnico fuera del modelo**: `CobroEnCurso`, lo que se cobra congelado entre la
confirmación y el aviso de la pasarela (B-07-034). No es un concepto del dominio, como no lo es la
sesión.

**Tres conceptos construidos que el modelo todavía no declara**: `TransicionDePedido`, la línea de
tiempo del pedido (B-08-001), `TokenCambioCorreo`, que `CO-109` pide como concepto propio
(B-11-002), y `SolicitudDespacho`, el envío de stock almacenado (B-18-004). Los tres esperan su
enmienda.

**RNF-05 está construido a medias.** `core/imagenes.py` convierte a WebP, acota el lado mayor y
no conserva el original para los banners, el logo y el fondo de la tienda. **Las portadas de
producto siguen sin procesarse**: `CU-ALT-NAC`, `IMP`, `REV`, `CU-CAT-ALT` y `EDI` guardan el
archivo tal como llega. Es deuda del módulo 01. La calidad es un valor fijo y no un parámetro
(B-17-012).

---

## Contratos sin prueba

El detalle contrato por contrato vive en [pruebas/COBERTURA.md](pruebas/COBERTURA.md).

**Faltan 44 de 219.** 175 tienen al menos una prueba que lleva su código; de esos, sólo
`CO-060` no cierra del todo (sólo el doble envío). `CO-114`, `CO-130` y los de grupos y etiquetas
(`CO-039`, `CO-041`, `CO-043`, `CO-045`) se cerraron el 2026-10-19 (plan 00, A3 y A6).

`CO-089 registrarResultadoDePago` y `CO-087 declararDireccionDeEnvio` están verificados en la
compra online; los referencia también `CU-STK-DES`, que no existe.

Los contratos sin prueba que más pesan siguen siendo los de las altas de lote (`CO-001` a
`CO-010`): la funcionalidad está construida y probada por pantalla, pero ninguna prueba lleva su
código.

---

## Invariantes declaradas sin garantía en la base

Relevadas el 2026-09-22. Las migraciones de esta sesión no agregan restricciones: un campo
booleano en `Formato`, un entero en `ConfiguracionSistema` y tres tablas nuevas sin unicidades.

| Invariante | Dónde vive hoy | La respeta cualquier escritura |
| --- | --- | --- |
| I-01, I-03, I-04, I-07, I-08, I-10, I-15, I-16, I-17, I-19 (unicidades) | Restricciones en la base (I-19 desde el plan 09: `devoluciones_casodevolucion_linea_id_key`) | Sí |
| I-13 | Disparador de PostgreSQL, además de `save()` y `delete()` (B-16-004). `TRUNCATE` queda fuera | Sí, salvo `TRUNCATE` |
| I-02, I-14, I-11 | `save()`, `delete()` o el backend de autenticación | Sí |
| **I-05** tipo del mismo rubro que el producto | `clean()` | **No** |
| **I-06** no editorial sin Pre-venta ni Cancelado | `clean()` | **No** |
| **I-09** ningún importe negativo, ningún precio cero | `MinValueValidator` | **No** |
| **I-12** siempre un Administrador activo | Servicio de `accounts`, con bloqueo ordenado y prueba de concurrencia (B-13-006) | **No**: sólo las operaciones que pasan por el servicio |

**I-09 vive en la base para los conceptos de la compra** (2026-10-09): `LineaPedido.precio_unitario`
mayor que cero, y montos, costos de envío y compensaciones no negativos, como `CheckConstraint`.
**`Producto.precio` sigue sin restricción en la base**: la propagación del plan 03 escribe precios con
`update()` de queryset, que no pasa por los validadores.

Nueve de las doce restricciones de unicidad existen sólo como índice `UNIQUE` y no figuran en
`pg_constraint`. Buscarlas ahí da el falso negativo contra el que advierte `CLAUDE.md`.

---

## Una prueba frágil

`apps/catalog/tests/test_pantalla_revision.py::test_solo_se_puede_seleccionar_lo_que_el_lote_va_a_confirmar`
falló una vez en la corrida completa del 2026-10-17 y pasó en las cuatro siguientes. Busca el texto
`value="<pk>"` en toda la página, y otro elemento puede llevar por casualidad el mismo número
según el orden de las pruebas. No es un defecto del código: hay que acotar la búsqueda a las
casillas de selección.

---

## Código sin contrato

| Dónde | Qué hace | Qué falta |
| --- | --- | --- |
| `apps/core/views.py::PanelAdministracionView` | Tablero de entrada del Administrador con cifras agregadas | Ningún contrato lo declara. `CO-219` está en camino y todavía no aparece en `.contexto-ia/` |
| `apps/core/views.py::PoliticaPrivacidadView` | Publica la política que el registro obliga a aceptar | Ningún contrato declara su publicación ni qué pasa cuando cambia |
| `apps/core/integraciones.py` | Única puerta HTTP, con caché, servicio en vivo y respaldo local | La degradación está declarada sólo para cotizaciones (`CO-155`) |

**Las dos pantallas públicas del contenido de la tienda** (la portada con el carrusel y la página
de preguntas frecuentes) se construyeron dentro de `CU-CFG-BNC` y `CU-CFG-FAQ` por decisión del
responsable (C-06). Ningún caso de uso las declara todavía (B-17-013).

### Las tareas de consola quedan fuera del modelo de casos de uso

Por R-01-002: `respaldar_base`, `sincronizar_georef`, `sincronizar_paises`, `ingerir_correos`,
`extraer_novedades` y `crear_administrador_inicial`. La enmienda que declara ese límite en el
alcance sigue pendiente.

---

## Entradas de bitácora

| Bitácora | Total | Abiertas | Tipos |
| --- | ---: | ---: | --- |
| `bitacora/00-documentacion-de-pruebas.md` | 5 | 3 | 3 agregados, 2 correcciones |
| `bitacora/00-estilo-preliminar.md` | 12 | 8 | 10 agregados, 2 desvíos |
| `bitacora/00-pulido-de-interfaz.md` | 8 | 2 | 5 agregados, 3 correcciones |
| `bitacora/01-alta-editorial.md` | 14 | 11 | 9 agregados, 3 correcciones, 1 desvío |
| `bitacora/02-catalogo.md` | 6 | 4 | 4 agregados, 2 correcciones |
| `bitacora/03-pricing.md` | 13 | 11 | 10 agregados, 2 correcciones |
| `bitacora/04-proveedores.md` | 9 | 3 | 7 agregados, 1 corrección, 1 desvío |
| `bitacora/05-restock.md` | 8 | 8 | 7 agregados, 1 corrección |
| `bitacora/06-ventas-presenciales.md` | 6 | 6 | 4 agregados, 2 correcciones |
| `bitacora/07-tienda-online.md` | 40 | 32 | 34 agregados, 4 correcciones, 1 desvío |
| `bitacora/08-gestion-de-pedidos.md` | 10 | 10 | 7 agregados, 2 correcciones, 1 desvío |
| `bitacora/09-devoluciones.md` | 9 | 8 | 4 agregados, 4 correcciones |
| `bitacora/10-puntos.md` | 12 | 11 | 7 agregados, 4 correcciones |
| `bitacora/11-cuenta-de-cliente.md` | 6 | 4 | 6 agregados |
| `bitacora/12-autenticacion.md` | 4 | 1 | 1 agregado, 1 corrección, 1 desvío |
| `bitacora/13-gestion-de-usuarios.md` | 6 | 0 | 2 agregados, 2 correcciones, 2 desvíos |
| `bitacora/14-caja.md` | 3 | 3 | 2 agregados, 1 corrección |
| `bitacora/16-auditoria.md` | 4 | 3 | 3 agregados, 1 corrección |
| `bitacora/17-configuracion-del-sistema.md` | 18 | 12 | 13 agregados, 4 correcciones, 1 desvío |
| `bitacora/18-stock-almacenado-en-local.md` | 9 | 8 | 4 agregados, 4 correcciones |
| **Total** | **202** | **147** | |

«Abierta» quiere decir que el código ya resolvió el punto y la enmienda del documento está
pendiente, o que espera la respuesta a una consulta (C-19, C-21). Ninguna entrada abierta es
código sin terminar.

**Enmiendas pendientes al documento**, además de las de cada entrada abierta:

| Enmienda pendiente | De dónde sale |
| --- | --- |
| Las tareas de consola quedan fuera del modelo de casos de uso | R-01-002 |
| Los cinco catálogos no distinguen mayúsculas (Área 2 dice «único» a secas en `Formato` y `GrupoEtiqueta`) | R-02-002 |
| `CO-120`: el correo no pertenece a ninguna cuenta en cualquier estado | R-13-004 |
| `CO-124`: pierde la precondición de colisión y E2 | R-13-004 |
| `CO-125`: pierde la cita a I-14 | R-13-004 |
| `CO-149`: de dónde sale el contenido de diagnóstico | R-17-001 |
| `EnlaceActivacion` y `TokenRecuperacion` pasan a `<<construido>>` | B-12-003 |
| `Banner`, `ContenidoFAQ` e `IdentidadVisual` pasan a `<<construido>>`; `Formato` gana «aplica a todos los tipos»; `ConfiguracionSistema` gana el intervalo del carrusel | B-17-003, B-17-004 |
| Las once acciones de auditoría nuevas en la nota de INC-06 | B-17-005 |
| `TOKENS_VISUALES.md` e `identidad_visual.md`: la densidad del modo operativo y los componentes nuevos | B-00-004 |
| El DSS de los siete casos de uso con `cancelarOperacion` | C-17, archivo entregado por el responsable |
| `ImagenProducto` en el Área 3 del modelo | B-01-003 |
| `TOKENS_VISUALES.md`: el fondo de imagen de la tienda | B-00-006 |
| `Pedido`, `LineaPedido`, `TransaccionPago`, `LotePuntos` y `MovimientoPuntos` pasan a `<<construido>>`; `ConfiguracionSistema` gana el costo de envío y la pasarela | Plan 07, sexta parte; B-07-031, B-07-032 |
| La compra: A2 sólo con envío gratis, redondeo de puntos, el carrito pierde sólo lo comprado, el stock perdido mientras se pagaba se reembolsa, la sugerencia al invitado | B-07-033 a B-07-036 |
| DME-12 pierde «Reservado para cambio»; DME-16 se retira o se rehace sobre `DevolucionFisica`; el Área 5 pierde «sustituto en cambio» | R-09-001 |
| `CasoDevolucion` y `DevolucionFisica` pasan a `<<construido>>`; `ConfiguracionSistema` gana el plazo de devolución como construido; `MovimientoPuntos` → `CasoDevolucion` construida | Plan 09 |
| `ConfiguracionSistema` gana el aviso previo a la caducidad; `LotePuntos` gana la marca del aviso y pierde (o redefine) «comprometido en canje» | B-10-005, B-10-006 |
| `CO-195` y `CU-CLI-CON` paso 6: la ficha del Cliente ofrece sus puntos | B-10-011 |
| **Retiro en el local** (cambio de alcance del 2026-10-19): el alternativo de `CU-TDA-CMP`, la modalidad en `CO-180`, `CO-087`, `CO-088`, `CO-089`; En el local en DME-07 y `CO-092`; `Pedido` gana la modalidad | B-07-038 |
| RF-25 con dos orígenes y el reembolso al vencer lo que era para retirar; `ArticuloRetenido` gana la procedencia; `CU-DEV-SOL` admite lo retirado | B-18-008 |
| `TransicionDePedido` en el Área 5; correo en cada avance; filtro de cliente y total cobrado del listado | B-08-001 a B-08-003 |
| `TokenCambioCorreo` en el Área 1; historial = despachados; aviso al correo anterior | B-11-002, B-11-004, B-11-005 |
| El origen de cada movimiento de puntos y el saldo en el encabezado | B-10-001, B-10-002 |
| RF-19 y `CU-CFG-PAR`: valor del punto y reintegro en puntos como dos parámetros | B-10-004 |
| `identidad_visual.md`: la regla de redacción de los textos de interfaz | B-00-017 |
| RF-13, `CU-VTA-REG`, `CO-081` y `Usuario`: el código de cliente en lugar del DNI | B-06-001 |
| `CU-VTA-REG`: alta por código exacto, comprobante y la «corrección de transacciones» sin caso de uso | B-06-003, B-06-004 |
| `CU-CAJ-CIE` E1 y paso 2: lo posterior al cierre va al siguiente; qué entra en un cierre | B-14-001, B-14-002 |
| `CO-178`: el envío y lo que falta para el envío gratis | B-07-037 |
| `CO-013`: qué es el lote, lo recibido cubre primero las reservas, faltantes sólo vencidos, revisión previa | B-01-006, B-01-007, B-01-008, B-01-011 |
| `CO-012`: sin período de gracia configurable | B-01-009 |
| `CO-026`, `CO-027`, `CO-098`: conversión y redondeo del reembolso a puntos | B-01-010 |
| `LineaPedido` gana la ventana de decisión; `CU-CFG-PAR` fija 72 h por defecto | B-08-004 |
| `CO-098`, `CU-PED-CAN` y RF-17: cancelar una pre-venta demorada no suma stock | B-08-005 |
| RF-16 y `CU-PED-CMP` E1: la compensación corre hasta que el artículo llega | B-08-006 |
| `CO-095` opción 2: el pedido pasa a Empaquetado | B-08-007 |
| DME-07: el estado Cancelado y el reembolso del envío | B-08-008 |
| `CU-PED-OPC` paso 2: qué opciones se ofrecen | B-08-009 |
| `CO-097`: cálculo por semanas cumplidas contra lo acreditado | B-08-010 |
| Área 5: un `ArticuloRetenido` por unidad; `SolicitudDespacho`; la transacción de pedido o de solicitud | B-18-002, B-18-004 |
| RF-25 (5): lo pendiente de despacho no vuelve solo al stock; `CU-STK-VEN`: aviso «N días o menos» | B-18-005, B-18-006 |
| `CU-STK-DES`: envío gratis desde el mínimo; `CU-STK-FIS`: despacho de la solicitud entera | B-18-007 |
| `CU-RST-NOT` y `CO-077`: el aviso sale con toda suba de stock; tres intentos seguidos | B-05-001, B-05-005 |
| `CO-075`: el aviso se pide sobre un Agotado | B-05-002 |
| `CU-RST-PRO`: proveedor de cada producto, ciclo diario con ventana semanal, valores por defecto | B-05-003, B-05-004 |
| `CO-030`: reponer stock a mano vuelve el Agotado a Activo | B-05-006 |

---

## Lo que esta fotografía no cubre

- **Las enmiendas pendientes se verificaron por su marca más visible**, no leyendo cada artefacto
  entero. Por ejemplo, `CO-120` sigue diciendo «Activa o Pendiente», `CO-125` sigue citando I-14
  y los dos conceptos de enlace siguen `<<planificado>>`.
- **El chequeo de consistencia compara nombres, no significados.**
- **Las invariantes no se volvieron a relevar.** La única escritura nueva que pasa por fuera de
  los validadores es la propagación de precios (`update()` y `bulk_update()`), y sus valores
  salen de formularios que exigen precio mayor que cero y de la fórmula del margen.
- **Las pantallas nuevas se probaron por la suite**, no a mano en un navegador.
