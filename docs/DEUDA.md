> **Tipo: Fotografía.** Tomada el **2026-10-02**.
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
| C-20 | ¿La portada de la tienda se ve sin iniciar sesión? | Sí, el 2026-10-05: la ve un invitado y cualquier rol, y la raíz del sitio lleva a ella | B-07-019 |

### Siguen abiertas

| # | Consulta | Dónde está | Qué desbloquea |
| --- | --- | --- | --- |
| C-19 | `CO-052` y `CU-PVP-MAR` exigen que exista al menos un importado. Con la palabra del contrato, en una instalación sin importados el margen no se puede cambiar desde ninguna pantalla, porque `CU-CFG-PAR` tampoco lo edita. Construido así (B-03-003) | Plan 03, ambigüedad 2 | Una enmienda de `CO-052`, si no es lo que se quiere |
| C-21 | **Nueva.** El logo no admite SVG porque RNF-05 convierte toda imagen a WebP. ¿Se enmienda la guía de `CU-CFG-VIS` o se exceptúa el logo de RNF-05? | B-17-011 | La guía de formato del logo |

---

## Decisiones transversales abiertas

| Ítem | Decisión pendiente | Qué bloquea | Desde |
| --- | --- | --- | --- |
| **P-05** · procesos periódicos | **Resuelta la forma** el 2026-10-03: `manage.py ejecutar_temporizador` es la puerta única; corre al arrancar `demostracion.bat` y se programa una vez por día (B-03-007). Hoy corre `CO-059`. Falta sumar cada proceso cuando exista su caso de uso | `CO-016`, `CO-155`, `CU-ALT-TRA`, `CU-RST-NOT`, `CU-PTS-CAD`, `CU-PED-CMP`, `CU-STK-VEN`, `CO-096` de `CU-PED-OPC`, y la limpieza de carritos de invitado abandonados | — |
| Parámetros de seguridad | Resuelto en B-12-001; falta construirlo | La sección Seguridad de `CU-CFG-PAR` y la mitad de `CO-114` | — |
| Pedido como dependencia raíz | Orden de construcción: `Pedido` no existe | Del módulo 07, la compra (`CU-TDA-CMP`, `INV`, `CO-179`); los módulos 08, 09, 10, 14 y 18, más `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-BAJ` y `CU-CLI-HIS`. `Carrito` ya existe (plan 07, segunda parte) | — |
| Carreras de unicidad no ensayadas | El doble envío de un alta con datos únicos terminaba en 500 en catálogos y proveedores (B-17-016, B-04-006, corregidos). No se ensayaron el alta de productos (ISBN, código de barras, código interno), el registro de clientes (correo) ni el alta de personal | Que esas altas respondan con el aviso de duplicado y no con un 500 ante un doble clic | 2026-10-04 |
| `04_RESUMEN.md` | `MODELO_DE_DOMINIO.md` lo cita y el archivo no está en el repositorio | Saber cuáles son las «cuatro operaciones con contrato pausado» | 2026-09-14 |

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

Fuente: `MODELO_DE_DOMINIO.md` contrastado contra las clases del código. `Banner`,
`ContenidoFAQ` e `IdentidadVisual` se construyeron el 2026-10-02. Quedan 15:

| Concepto | Área | Módulo que lo introduce | Conceptos que dependen de él |
| --- | --- | --- | --- |
| `Pedido` | A5 Comercio | 07 Tienda Online | `LineaPedido`, `TransaccionPago` |
| `LineaPedido` | A5 Comercio | 07 Tienda Online | `CasoDevolucion`, `ArticuloRetenido` |
| `TransaccionPago` | A5 Comercio | 07 Tienda Online | `CierreDeCaja` |
| `Carrito` | A5 Comercio | 07 Tienda Online | `LineaCarrito` |
| `LineaCarrito` | A5 Comercio | 07 Tienda Online | — |
| `CasoDevolucion` | A5 Comercio | 09 Devoluciones | `DevolucionFisica` |
| `DevolucionFisica` | A5 Comercio | 09 Devoluciones | — |
| `ArticuloRetenido` | A5 Comercio | 18 Stock Almacenado en Local | — |
| `CierreDeCaja` | A5 Comercio | 14 Caja | — |
| `LotePuntos` | A6 Fidelización | 10 Puntos | `MovimientoPuntos` |
| `MovimientoPuntos` | A6 Fidelización | 10 Puntos | — |
| `PropuestaRestock` | A4 Pipeline | 05 Restock | `LineaPropuestaRestock` |
| `LineaPropuestaRestock` | A4 Pipeline | 05 Restock | — |
| `SuscripcionReposicion` | A3 Producto | 05 Restock | — |
| `Oferta` | A2 Clasificación | 03 Pricing | — |

**RNF-05 está construido a medias.** `core/imagenes.py` convierte a WebP, acota el lado mayor y
no conserva el original para los banners, el logo y el fondo de la tienda. **Las portadas de
producto siguen sin procesarse**: `CU-ALT-NAC`, `IMP`, `REV`, `CU-CAT-ALT` y `EDI` guardan el
archivo tal como llega. Es deuda del módulo 01. La calidad es un valor fijo y no un parámetro
(B-17-012).

---

## Contratos sin prueba

El detalle contrato por contrato vive en [pruebas/COBERTURA.md](pruebas/COBERTURA.md).

**Faltan 139 de 219.** 80 tienen al menos una prueba que lleva su código. Los que tienen
prueba y no cierran del todo son ocho: `CO-114` (B-12-001), `CO-048` y `CO-053` (carritos,
B-03-001), `CO-221` (ofertas, B-17-008), y `CO-039`, `CO-041`, `CO-043` y `CO-045` en su parte
sobre los filtros del catálogo público (B-02-004).

`CO-156 cancelarOperacion` lo referencian veintidós casos de uso. Tiene prueba en catorce:
`CU-USR-BAJ`, `REA`, `ELI`, `CU-CAT-BAJ`, `REA`, `GRB`, `ETB`, `CU-CFG-EDB`, `TPB`, `FMB`,
`CU-PVP-TBM`, `TBB`, `MAR` y `CU-PRV-REA`/`BAJ`.

Los contratos sin prueba que más pesan son los de las altas de lote (`CO-001` a `CO-010`): la
funcionalidad está construida y probada por pantalla, pero ninguna prueba lleva su código.

---

## Invariantes declaradas sin garantía en la base

Relevadas el 2026-09-22. Las migraciones de esta sesión no agregan restricciones: un campo
booleano en `Formato`, un entero en `ConfiguracionSistema` y tres tablas nuevas sin unicidades.

| Invariante | Dónde vive hoy | La respeta cualquier escritura |
| --- | --- | --- |
| I-01, I-03, I-04, I-07, I-08, I-10, I-15, I-16, I-17 (unicidades) | Restricciones en la base | Sí |
| I-13 | Disparador de PostgreSQL, además de `save()` y `delete()` (B-16-004). `TRUNCATE` queda fuera | Sí, salvo `TRUNCATE` |
| I-02, I-14, I-11 | `save()`, `delete()` o el backend de autenticación | Sí |
| **I-05** tipo del mismo rubro que el producto | `clean()` | **No** |
| **I-06** no editorial sin Pre-venta ni Cancelado | `clean()` | **No** |
| **I-09** ningún importe negativo, ningún precio cero | `MinValueValidator` | **No** |
| **I-12** siempre un Administrador activo | Servicio de `accounts`, con bloqueo ordenado y prueba de concurrencia (B-13-006) | **No**: sólo las operaciones que pasan por el servicio |

**No hay ninguna `CheckConstraint` en el proyecto.** I-09 es la más expuesta porque toca dinero, y
el plan 03 la ejerce más que nadie: la propagación escribe precios con `update()` de queryset, que
no pasa por los validadores.

Nueve de las doce restricciones de unicidad existen sólo como índice `UNIQUE` y no figuran en
`pg_constraint`. Buscarlas ahí da el falso negativo contra el que advierte `CLAUDE.md`.

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
| `bitacora/00-estilo-preliminar.md` | 6 | 2 | 5 agregados, 1 desvío |
| `bitacora/01-alta-editorial.md` | 5 | 3 | 5 agregados |
| `bitacora/02-catalogo.md` | 5 | 3 | 4 agregados, 1 corrección |
| `bitacora/03-pricing.md` | 6 | 5 | 6 agregados |
| `bitacora/04-proveedores.md` | 5 | 0 | 4 agregados, 1 desvío |
| `bitacora/07-tienda-online.md` | 2 | 2 | 2 agregados |
| `bitacora/11-cuenta-de-cliente.md` | 1 | 0 | 1 agregado |
| `bitacora/12-autenticacion.md` | 3 | 0 | 1 agregado, 1 corrección, 1 desvío |
| `bitacora/13-gestion-de-usuarios.md` | 5 | 0 | 2 agregados, 1 corrección, 2 desvíos |
| `bitacora/16-auditoria.md` | 3 | 3 | 3 agregados |
| `bitacora/17-configuracion-del-sistema.md` | 14 | 10 | 11 agregados, 2 correcciones, 1 desvío |
| `bitacora/18-stock-almacenado-en-local.md` | 1 | 0 | 1 corrección |
| **Total** | **56** | **28** | |

«Abierta» quiere decir que el código ya resolvió el punto y la enmienda del documento está
pendiente, o que espera la respuesta a una consulta (C-19 a C-21). Ninguna entrada abierta es
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
