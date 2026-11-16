> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `00` Sincronización con el documento de análisis

> Registro de las pasadas que comparan el sistema construido con el documento de análisis.
> **Se anexa, no se reescribe.** Una entrada resuelta se marca; no se borra.
>
> El inventario de cada pasada es una fotografía y vive en
> [`docs/sincronizacion/INVENTARIO.md`](../docs/sincronizacion/INVENTARIO.md); esta bitácora registra
> que la pasada ocurrió, contra qué se comparó y qué encontró que no tiene otro lugar.

---

## Entradas

### Nota · 2026-10-30 · Primer inventario de cambios para el documento

**Documento comparado.** `docs/Longbox - Comic Store Manager.docx`, modificado el 2026-09-30 09:03
(revisión interna 56). La última versión de su Lista de Cambios es la **13, del 05/09/2026**; el
responsable confirmó que el archivo es el vigente y que su contenido es del 30/09. El historial de git
se leyó desde esa fecha: 14 commits (`62b72d8` a `b6dd342`) y el árbol de trabajo sin commitear.

**Base.** `scripts/generar_contexto.py` corrido hoy: 18 módulos, 103 casos de uso, 219 contratos;
`.contexto-ia/` no cambió y los 11 archivos protegidos siguen iguales. Informe completo en
[`docs/sincronizacion/generador.txt`](../docs/sincronizacion/generador.txt).

**Cifras.**

| | |
| --- | ---: |
| Filas del inventario | 209 |
| Por tipo | 145 agregados, 49 correcciones, 8 desvíos, 2 mixtas, **5 sin registro** |
| Por estado en el documento | 81 no reflejadas, 119 parciales, 5 no determinables, 4 reflejadas |
| Requieren asignar un código | 23 |
| Requieren una decisión | 23 |
| Entradas `B-` de la bitácora | 267: 219 citadas en alguna fila y 48 excluidas con su motivo |
| Rótulos provisorios | 1 módulo, 19 casos de uso, 25 contratos, 16 DSS, 4 requisitos, 3 invariantes, 6 estados |
| Flujos que conviene reescribir | `CU-DEV-SOL`, `CU-DEV-RES`, `CU-ALT-TRA`, `CU-RST-APR`, `CU-CLI-HIS` |

**Lo que el responsable tiene que ver primero.** Dos cambios **sin registro** alteran lo que el
usuario puede hacer: la consulta de los **cierres de caja anteriores** (Cajero y Administrador,
`caja/cierres/`) y la **página pública de la política de privacidad**. Están en el inventario como
filas «Sin registro», con la decisión que piden.

**Citas de la bitácora que no cierran.** No se corrigen acá, porque las entradas no se reescriben:

- B-17-011 cita la consulta C-08; la del logo, en `docs/DEUDA.md`, es **C-21**.
- B-17-007 nombra `CU-PRV-MOD`, que no existe; el caso de uso es `CU-PRV-EDI`.
- B-05-016 dice «Nada» para el documento y `docs/DEUDA.md` pide enmendar `CU-RST-APR` paso 2; el
  inventario lo registra por `DEUDA.md`.
- B-00-001 dice «Nada» para el documento, pero el «Estudio de Factibilidad» nombra Tailwind en cuatro
  lugares.

**Una interpretación de la consigna.** El índice del documento numera dos capítulos «3». Las
«Secciones 4 y 5» se tomaron por orden real: «Alcance y Limitaciones» y «Estudio de Factibilidad».

**Contradicciones.** No hay contradicciones entre entradas sin resolver: en todos los casos la
posterior dice qué reemplaza. La más grande: B-09-008 retira `DevolucionFisica`, que R-09-001 había
decidido conservar.

### Nota · 2026-11-08 · Segunda pasada: decisiones del responsable y códigos nuevos

**Documento comparado.** El mismo de la nota anterior: versión 13 de la Lista de Cambios, archivo del
2026-09-30. La pasada completa el inventario del 2026-10-30 con las 13 entradas del 2026-11-07 y
verifica las decisiones abiertas de ciclos anteriores contra lo construido.

**Regla nueva del ciclo.** Lo construido es final: el documento de análisis se corrige para describirlo.

**Decisiones del responsable.**

- **Códigos de caso de uso**, asignados por Claude por delegación del responsable, con la forma
  `CU-###-!!!`: `CU-RST-RSP` (respuesta del proveedor), `CU-CFG-FIL` (filas de la portada),
  `CU-CAJ-HIS` (cierres de caja anteriores), `CU-TDA-POR` (portada pública), `CU-TDA-PFR` (preguntas
  frecuentes públicas), `CU-CLI-POL` (política de privacidad) y `CU-REP-PAN` (panel del Administrador,
  con `CO-219`). Se conservan `CU-RST-PRC`, `CU-RST-PDA`, `CU-RST-LLE` (C-23) y los once `CU-AVI-*`
  (B-19-001). «Volver a anunciar» queda como flujo alternativo del alta, sin código.
- **Se retiran**, y sus códigos no se reutilizan: `CU-RST-ING` (lo cubre `CU-RST-LLE`), `CU-DEV-PRU`,
  `CO-222`, `CO-223`, `CO-224`, `CO-225` y `CO-226`; el estado «Pendiente de verificación» de
  `TransaccionPago` y `CU-CAJ-CIE` A1, que ningún flujo usa; DME-16.
- **Reservados sin construir:** `CO-230` y `CO-231` (ingreso con Google).
- **RNF-09** declara la excepción: suscribirse a un aviso de reposición, cancelarlo, canjear puntos y
  anular el canje no se auditan (`CO-075`, `CO-076`, `CO-103`, `CO-104`), como ya hace el sistema.
- **Lo construido sin registro entra al documento**: los cierres de caja anteriores y la política de
  privacidad, con caso de uso, DSS y contratos; los datos que el modelo no declaraba, al modelo; el
  despliegue en la VM, al alcance.
- **Casos de prueba:** `CP-MOD-AAA-NN`.
- Las decisiones de ciclos anteriores (M6, N3, N7, `CO-155` en PA-04, la sección 5) se resuelven como
  lo construido.

**Pendiente de confirmar:** la numeración de los contratos nuevos desde `CO-233`, y la de requisitos,
invariantes y máquinas de estado a continuación de las vigentes.

**Para quien programe.** Ningún código cambia por esta pasada. Los códigos nuevos todavía no están en
`.contexto-ia/`: llegan cuando el responsable aplique las correcciones y se regenere el contexto.

### Nota · 2026-11-08 · Confirmación de la numeración

El responsable confirmó lo que la nota anterior dejaba pendiente: los contratos nuevos se numeran desde
`CO-233`, sin reutilizar huecos; siguen `RF-28` a `RF-30`, `RNF-13`, `I-24` a `I-26`, `DME-19` y
`DME-20`. Confirmó también que la relación entre cada caso de prueba y sus pruebas vive en la ficha del
caso, que `CO-228` es un paso de `CU-ALT-NOV` E2, que los contracargos de MercadoPago son un límite
declarado y que `CU-TDA-POR`, `CU-TDA-PFR` y `CU-REP-PAN` son casos de uso.

### Nota · 2026-11-12 · El documento de análisis pasa del .docx a HTML con salida en PDF

**Decisión del responsable.** El documento de análisis deja de mantenerse en Word. La fuente pasa a
ser HTML, en `privado/documentación/documento/` (sin versionar por ahora), y se publica en PDF
paginado con paged.js; la cátedra acepta el PDF. Las correcciones del ciclo se aplican directamente
sobre la fuente, y el responsable las revisa por sección.

**Migración.** Se convirtió `docs/Longbox - Comic Store Manager.docx` tal como estaba el 2026-11-12
a las 15:30, con la sección 1 ya aplicada por el responsable: 12 capítulos, 103 tarjetas, 103
fichas, 219 contratos, 39 requisitos y 93 tablas. Los 111 DSS se generan en SVG desde
`.contexto-ia/dss/DSS.md` con los apartados corregidos de C-17, y cada evento enlaza a su contrato
por el nombre. La numeración de capítulos, figuras e índice es automática.

**Para quien programe.** `docs/Longbox - Comic Store Manager.docx` queda congelado y deja de ser la
fuente. `scripts/generar_contexto.py` todavía lo lee: se adapta a la fuente nueva en el paso 5 del
ciclo. Hasta entonces, no regenerar `.contexto-ia/` desde el .docx.

### Nota · 2026-11-13 · Secciones 3 y 4: módulos, identificación y fichas

**Sección 3.** El documento declara diecinueve módulos y ciento veinticinco casos de uso. Entran el
módulo 19, Perfil y Avisos, y el actor `ACT-09` Servicio de Mensajería (aprobado por el responsable).
El panel del Administrador (`CU-REP-PAN`) se documenta entero, con la sección de inteligencia que
`apps/core/inteligencia.py` declaraba «fuera del documento formal» (decisión D2-7 del responsable:
«digamos la verdad»).

**Sección 4.** Cada caso de uso tiene su ficha: 22 nuevas y seis reescritas enteras (`CU-ALT-TRA`,
`CU-RST-APR`, `CU-DEV-SOL`, `CU-DEV-RES`, `CU-CLI-HIS` y, nueva, `CU-RST-LLE`); el resto, corregido por
fila del inventario. El escalado de `CU-ALT-TRA` pasa de E2 a E1, y la frase de `CU-CAT-INV` sobre
indicadores «no disponibles» se quita porque ya se calculan (las dos, aprobadas por el responsable).
Lo que las fichas dejan a los contratos está en `privado/documentación/correcciones/pendientes-seccion-6.md`.

**Pendiente del responsable.** Re-evaluar los riesgos y la factibilidad contra lo construido, junto
con el punto de Alcance y Factibilidad del ciclo; rehacer los diagramas que no son DSS con el estilo
del documento.

**Para quien programe.** Ningún código cambia. `privado/documentación/herramientas/aplicar_seccion_4.py`
reaplica la sección desde la copia previa del capítulo.

### Nota · 2026-11-13 · Secciones 5 y 6: DSS y contratos

**Sección 5.** 21 DSS nuevos y 13 corregidos (`privado/documentación/correcciones/05-dss/`). Al
redactar los contratos aparecieron dos diferencias con lo construido, corregidas en el DSS: los
canales de aviso no rechazan Telegram sin chat vinculado, sino que ese tipo queda por correo
(`CU-AVI-CAM` E1); y el cambio al modelo de respaldo (`CO-228`, `CO-229`), decidido el 2026-11-08
como parte de `CU-ALT-NOV`, no estaba en la ficha ni en el DSS: ahora está en su E4.

**Sección 6.** El capítulo pasa de 219 a 258 contratos y ningún evento de DSS queda sin el suyo.
Los nuevos van de `CO-233` a `CO-267` (tabla en `privado/documentación/CODIGOS.md`), más los ya
numerados `CO-219`, `CO-228`, `CO-229` y `CO-232`. Se corrigieron 30 contratos existentes contra las
fichas reescritas, los DSS y las bitácoras abiertas: entre ellos, B-03-014 (ofertas con cinco
destinos y su precedencia), B-01-027 (el valor de compra del lote importado, también en la ficha de
`CU-ALT-IMP`), la propuesta que espera respuesta, la llegada de mercadería por «Por llegar» y las
devoluciones (el cambio deja el reemplazo en el stock en local, como `ArticuloRetenido`; ya no hay
`DevolucionFisica`). También se limpiaron restos de la conversión: dos contratos internos cuyo
nombre no enlazaba desde el DSS, dos oraciones de auditoría partidas y 18 comillas invertidas
literales.

**Para quien programe.** Ningún código cambia. Los contratos citan `DME-19` y `DME-20`, que se
dibujan en la sección 7. `privado/documentación/herramientas/aplicar_seccion_6.py` reaplica la
sección 6 encadenada a la 5, desde la copia previa del capítulo 9.

### Nota · 2026-11-13 · Paginación del documento: fuentes, filas enteras e índice

El responsable encontró, en el visor, filas recortadas al pie de la hoja, una fila del historial
encimada con el pie de página y un título solo en su página. Dos causas:

- **paged.js paginaba antes de que cargaran las fuentes del documento.** Medía con la de reemplazo y,
  al llegar la del documento, el texto crecía y desbordaba la hoja. Eso explica también que el índice
  diera números de página equivocados (6.4 en la 55, estando en la 48), y que el resultado cambiara de
  una corrida a otra. La plantilla ahora espera las tres fuentes antes de paginar.
- **paged.js lee «break-inside: avoid» en las celdas y no en las filas**, así que ninguna fila estaba
  protegida. `CortesCuidados` (visor.js) lleva entera a la página siguiente la fila que no entra, salvo
  que sea casi tan alta como una hoja. Por decisión del responsable rige también en requisitos y
  contratos, donde antes se dejaba cortar.

Además, los códigos en celdas (R-13, RF-07) ya no se parten en el guion. `revisar_cortes.js` cuenta
ahora filas partidas, desbordes y entradas del índice desfasadas. Resultado: 609 páginas, todo en
cero; quedan 23 páginas llenas a menos de la mitad, casi todas antes de un diagrama que no se parte.

### Nota · 2026-11-14 · Sección 7: máquinas de estado, PA-01, invariantes y reglas

**Máquinas de estado.** Las 18 imágenes de la versión 13, sin fuente, se reemplazan por diagramas
generados desde `privado/documentación/herramientas/seccion_7/dme.py`, transcriptos de las imágenes y
corregidos contra lo construido y contra las postcondiciones de los contratos de la sección 6. El
generador se niega a dibujar si un código de contrato no existe o no corresponde a la operación nombrada.
Sobre cada transición va el código del contrato y la guarda; el nombre y la página van en un recuadro de
operaciones debajo de la figura, como los eventos de los DSS (con el nombre completo sobre cada línea, las
máquinas densas se imprimían por debajo de 5 pt). Cambios de contenido:

- `DME-02`: sin los contratos retirados `CO-222` y `CO-223`; Activo o Agotado vuelve a Pre-venta cuando
  hay un pedido a proveedor en camino; la edición del stock (`CO-030`); la baja sale una sola vez de un
  estado compuesto «En catálogo».
- `DME-03`: Procesado admite el descarte y el reprocesamiento (INV-069).
- `DME-04`: el alta desde Telegram y el reprocesamiento que elimina los borradores no decididos.
- `DME-07`: Vendido en el local, En el local y las dos formas de recibir lo disponible (INV-015,
  INV-020, INV-163).
- `DME-08`: sin «Transferido a stock almacenado», que el sistema no tiene; Entregado en el local.
- `DME-10`: la edición recalcula Programada o Activa.
- `DME-12`: sin «Reservado para cambio»; tres procedencias (INV-028, INV-045).
- `DME-13`: Esperando respuesta (INV-012).
- `DME-16` se retira con CambioProducto; `DME-19` y `DME-20` son nuevos.

**Contratos.** Dos postcondiciones que el sistema cumple y los contratos no declaraban: `CO-056` recalcula
el estado de la oferta por la fecha de inicio, y `CO-006` registra el pedido a proveedor de los ítems en
pre-venta. Van en `seccion_6/correcciones.py`.

**Lo demás.** PA-01 redibujado con la cola de aprobación, la clasificación del correo y el modelo de
respaldo, y su paso 5 lo dice. `I-20` reescrita para los cinco destinos de oferta (lo construido permite
destinos distintos superpuestos); `I-24` a `I-26` nuevas; la segunda ficha `PD-13` pasa a `PD-14`; el
Estado de Avance dice diecinueve máquinas de estado; `BR-14` declara los dos plazos y que corren desde el
despacho o el retiro (los valores legales siguen a confirmar con el tutor, `docs/DEUDA.md`).

**Un defecto de la hoja de estilo.** Las reglas que agrandaban los diagramas de subsistemas y de contexto
usaban selectores por id, que paged.js reescribe: nunca se aplicaron. Pasan a selectores de atributo.

**Lo que falta.** Los diagramas de actividad de PA-02, PA-03 y PA-04 no existen; el título del apartado lo
dice. El modelo de dominio lo grafica el responsable.

### Nota · 2026-11-15 · Arreglos de la sección 7 y sección 8: planificación y estado de construcción

**Arreglos pedidos por el responsable.** DME-01 ordenado en columna; los diagramas de estado chicos ya
no se imprimen con letra más grande que los demás. Las fichas PA tenían el encabezado desalineado con
sus columnas y la condición de verificación marcada como rótulo: corregidas. El apartado de diagramas de
actividad era un ítem de lista con «(Faltan el 2, 3 y 4)»: ahora es un subtítulo con los cuatro
diagramas (`herramientas/seccion_7/actividades.py`), y el texto de PA-02 y PA-03 dice lo que el sistema
hace (la propuesta por proveedor que espera la respuesta; cuatro opciones ante la demora; la cancelación
no devuelve stock, B-08-005). Los ocho diagramas del modelo de dominio que exportó el responsable
entran forzados a modo claro. Se retira una plantilla vacía de ficha («CU - ##») que el .docx traía
suelta. El responsable confirmó los plazos de `BR-14` (10 y 90 días); `docs/DEUDA.md` lo dice.

**Sección 8.** La Iteración C1 se cierra el 2026-11-15 con la versión 14 (Lista de Cambios, metas,
estado de avance con las cifras del cierre y P-01 a P-06 resueltos). El calendario desde el bloque 5 se
fechó con el historial de git (creación de cada aplicación y commits), y el Gantt, que eran dos
enlaces a un servicio externo, se genera desde la tabla. El capítulo de Estado de Construcción se
regenera desde las fichas y `docs/ESTADO.md`: 125 casos de uso, 104 verificados y 21 construidos con su
contrato redactado en esta versión.

**Para `docs/ESTADO.md`.** Siete casos de uso con código asignado en este ciclo figuran en prosa y sin
fila (`CU-PVP-VEN`, `CU-RST-RSP`, `CU-TDA-POR`, `CU-TDA-PFR`, `CU-CLI-POL`, `CU-CAJ-HIS`,
`CU-REP-PAN`); el generador del capítulo los declara aparte hasta que la tengan.

**Orden de los scripts.** `aplicar_seccion_8.py` parte de la salida de la sección 7 para el capítulo 1:
correr la 7 sola deja el capítulo 1 sin la 8.

**Pendiente de confirmar:** la recodificación de los 28 casos de prueba a `CP-MOD-AAA-NN`.

### Nota · 2026-11-15 · DME-02 con trazado propio, PA-05 a PA-07 y casos de prueba recodificados

**DME-02** se dibuja con trazado propio (`herramientas/seccion_7/dme02.py`): con trece transiciones
Graphviz cruzaba las líneas alrededor de Pre-venta, Activo y Agotado. Las leyendas siguen saliendo de
`dme.py`.

**PA-05 a PA-07** (aprobados por el responsable): la caducidad de puntos con aviso previo, el
vencimiento del stock en local y la vigilancia de pre-ventas con su escalado, procesos periódicos que el
sistema ya ejecutaba y el documento no declaraba como PA. Fichas y diagramas de actividad en el
capítulo 7; el capítulo de estado los lista.

**Corrección de `CO-154`**, encontrada al escribir PA-06: decía que lo que vence en el stock en local
vuelve «sin reembolso», y el sistema devuelve su valor en puntos (plan 07, octava parte, D3; plan 00,
C2; INV-045). Gana lo construido. `DME-11` suma `CO-154` a la entrada por reembolso.

**Casos de prueba** recodificados a `CP-MOD-AAA-NN`, con `CP-SIS-RNN-NN` para los transversales
(decisión del responsable): `docs/pruebas/CASOS_DE_PRUEBA.md` y `CATALOGO.md`, con la tabla de
equivalencias.

**Modelo de dominio.** Las áreas 4 y 5 van giradas 90°, en copias generadas. El área 5 del responsable
todavía dibuja CambioProducto, que se retiró con `DME-16`.

### Nota · 2026-11-15 · Sección 9: alcance, factibilidad y riesgos

**Alcance y Limitaciones.** Se suman tres dominios construidos (el circuito con los proveedores, los
avisos y la operación desde el teléfono, el despliegue y la operación) y el retiro en el local. El
despliegue entra al alcance (decisión del 2026-11-08, INV-187); queda fuera la contratación de la
infraestructura y de los servicios. Límites nuevos: las tareas de consola (INV-186), los contracargos
(INV-225), el ingreso con cuentas de terceros (reservado) y las variantes de producto. La tabla del
alcance construido pasa a «Construido» en todos los dominios, y se suman lo descartado para el cierre y
la próxima iteración, de `docs/DEUDA.md`.

**Factibilidad.** El stack sin Tailwind, sin Celery ni Redis (INV-188, INV-224); la VM; la lectura IMAP,
la pasarela probada y Telegram como integraciones (INV-189); el panel de Django retirado (INV-190); los
procesos periódicos resueltos; siete puertas. Las Suposiciones del capítulo 11, igual.

**Riesgos.** Una reevaluación al cierre de cada riesgo, con los casos de prueba que lo cubren, y tres
riesgos nuevos, numerados `R-16` a `R-18` a continuación de los vigentes: Telegram, el servidor único y
la configuración de despliegue. **Pendiente de confirmar** esa numeración.

**Orden de los scripts.** El capítulo 11 lo escriben las secciones 7 y 9: correr 7, 8 y 9 en ese orden.

### Nota · 2026-11-15 · Sección 10: plan de pruebas

El capítulo de Plan de Pruebas suma la séptima puerta (contratos); la trazabilidad, que era un
marcador «[Insertar tabla aquí]», pasa a una tabla por módulo con los casos de uso verificados y
construidos, y a la cuenta de contratos con prueba (222 de 258, con 1170 pruebas de contrato, leídas del
código); los casos de prueba elegidos por riesgo (INV-191), con los códigos nuevos; y el estado al cierre
de los huecos: H-1 abierto, H-2 cubierto por un script fuera de la suite, H-3 cerrado, H-4 manual.

El resto de la sección 10 del inventario (INV-192 a INV-209) son enmiendas a `TOKENS_VISUALES.md` e
`identidad_visual.md`, que el responsable mantiene dentro de `.contexto-ia/`: no se tocan.

### Nota · 2026-11-15 · Paneo final de cortes de página

Con el documento completo se revisaron los cortes y se ajustó `CortesCuidados` (`documento/visor.js`):

- Una tabla que empieza al pie con una sola fila no se movía: la medida «del comienzo de lo que se mueve
  al punto de corte» da valores falsos dentro de una tabla mientras paged.js maqueta (0,95 de la hoja
  para una fila). La tabla con una fila o ninguna al pie ahora se mueve siempre.
- Un título con un solo párrafo corto de introducción antes de su tabla, figura o ficha pasa con ella a
  la página siguiente (eran seis títulos al pie presentando un bloque que estaba en la otra hoja).
- Las filas de grupo (títulos dentro de una tabla) no quedan últimas al pie.
- Una figura de DSS o de DME no se separa de su recuadro de eventos u operaciones (eran seis).
- Los diagramas de actividad bajan a 185 mm para entrar con el título del apartado.

`revisar_cortes.js` mide ahora también los títulos al pie con sólo su introducción y las filas de grupo
al pie. Resultado: 634 páginas; títulos al pie, tablas al pie, filas partidas, desbordes, índice
desfasado y recuadros sueltos, todos en cero. Queda un título, «7.4 Patrones de Análisis», al pie con
dos párrafos de introducción y la tabla en la página siguiente, que no es un huérfano. Las 37 páginas
con más de media hoja libre están antes de un diagrama o de una figura que no se parte, o antes de un
módulo que empieza en hoja nueva; la menos llena, al 23 %.

### Nota · 2026-11-15 · Manual de Usuario

El Manual de Usuario se arma como el documento de análisis (HTML, paged.js, PDF), en
`privado/documentación/manual/`, con su `LEEME.md`. Once capítulos por quién usa cada parte (primeros
pasos, la tienda, el mostrador y la administración en seis temas), problemas frecuentes y un apéndice
que relaciona cada tarea con sus casos de uso. 120 páginas, 117 capturas; la revisión de cortes, toda
en cero.

Las capturas salen del sistema funcionando sobre `longbox_manual`, una copia de la base de la
demostración que `preparar_base.py` anonimiza: la base tiene datos de dos personas reales (nombres,
correos, direcciones, teléfonos, también dentro del log de auditoría), que pasan a dos clientes
ficticios; la clave de la API del modelo y el correo de la tienda se neutralizan, y la pasarela pasa
a la de prueba. Un guion recorre el escenario completo en orden (compras, una pre-venta demorada con la
decisión de la clienta, su llegada, una venta en el mostrador, el cierre de caja, un reclamo y su
resolución), así que las capturas cuentan una misma historia y se pueden regenerar.

Los textos se verificaron contra el código, no contra lo que se suponía de las pantallas. Hallazgo
para el responsable, sin tocar: en la pasarela de prueba (`tienda/pasarela_prueba.html`) el importe
usa el estilo del total del carrito, texto oscuro, sobre un panel oscuro, y casi no se lee. Sólo
afecta al entorno de prueba.

### Nota · 2026-11-15 · Manual de Usuario: huecos y tablas

La revisión a ojo encontró lo que la revisión de cortes no medía: 48 páginas que terminaban antes del
72 % porque una captura, que no se parte, saltaba a la hoja siguiente; finales de capítulo que se
desbordaban unas líneas a una hoja casi vacía; tablas cortas partidas con una o dos filas sueltas.

`manual/ajustar.js` pagina el manual y calcula, para cada captura que saltó, la altura con la que
entra en el hueco (mide el paso entero de un tutorial y el margen que recupera un título); si no
alcanza, la cede una captura de la hoja anterior; nunca baja del 60 % de su altura. Las capturas de
pantallas casi vacías se recortan a lo útil en el armado, sin volver a capturarlas, y en dos secciones
un párrafo pasó antes de su captura. Las tablas se parten sólo con tres filas o más de cada lado.
`manual/armar.py` repite armado y ajuste hasta que no cambia nada. Resultado: 91 páginas (eran 120),
ninguna con hueco fuera de los finales de capítulo, y la revisión de cortes en cero.

### Nota · 2026-11-15 · Manual de Pruebas

El Manual de Pruebas (`privado/documentación/pruebas/`, 38 páginas) pasa a documento formal los casos de
`docs/pruebas/CASOS_DE_PRUEBA.md`, con la estrategia, el entorno, los resultados, la trazabilidad y los
huecos. Los casos se leen del repositorio y cada resultado sale de una ejecución hecha hoy sobre la
versión 1.0: la suite completa (3989 pruebas, todas pasan, 97 % de cobertura), las puertas y el
ensayo de resistencia completo sobre la base de la demostración (migrada antes: 74 migraciones
pendientes, aplicaron sin errores). Resultado: 27 de 28 casos pasan.

`CP-SIS-R07-01` **falla**: con 50 sesiones no hubo errores ni operaciones de más de 1 s, pero cuatro
operaciones de administración degradaron su p95 más de un 20 % contra la línea base (+28 % a +53 %).
Además la condición de `RNF-07` es ambigua (habla de los tiempos «de RNF-02», un techo de 2 s, y de
operaciones de catálogo y compra, que no son las de la línea base). Queda para el responsable.

Correcciones hechas en el camino: el resultado esperado de `CP-ALT-REV-01` (el borrador queda Pendiente
y no Incompleto, por B-01-018); el criterio de `CASOS_DE_PRUEBA.md`, que daba a R-03 y R-06 por no
construidos; seis líneas «Se ejecuta con» que habían quedado bajo el título de la sección siguiente;
`scripts/demo/escalones.py`, que fallaba al leer el CSV de locust (cp1252); y `generar_catalogo.py`,
que no reconocía los códigos de caso nuevos y había dejado sin casos la tabla de scripts.

Paginación: el encabezado repetido de las tablas partidas se insertaba después de medir la página y
empujaba filas fuera de la hoja. El PDF del documento de análisis perdía así 57 filas (riesgos R-03 y
R-09 a R-12, filas de contratos y de requisitos). Ahora se inserta al maquetar (`documento/visor.js`) y
`revisar_cortes.js` controla también el contenido perdido. El documento quedó en 641 páginas, con
todas sus filas.

### Nota · 2026-11-15 · Carátulas, costos con COCOMO II y README

Las carátulas de los tres documentos dejan la fotografía y pasan al lenguaje visual del sistema
(Viñeta Nocturna: noche, acento naranja, trama, cinta de precaución, viñeta de papel con esquina cortada
y sombra dura). Los tres quedan como una serie numerada (Nº 1 a 3), con su código de barras. Los estilos
viven en `documento/estilo.css`, que comparten los tres.

El capítulo 11 tenía la sección «Coste y Fijación de Precio» con marcadores. Se completó con
`herramientas/aplicar_seccion_11_costos.py` (se corre después de la sección 10):

- Una subsección nueva con la estimación COCOMO II post-arquitectura (coeficientes de 2000). El tamaño
  se mide del repositorio: 45 849 líneas lógicas (Python, plantillas y JS), sin pruebas, migraciones
  ni CSS. Resultado: 165,4 meses-persona y 17,7 meses de plazo.
- El costo de operación, el mantenimiento anual, el precio por suscripción en cuatro escenarios y los
  costos no incluidos.

**A confirmar por el responsable:** los niveles de los factores de escala y de los multiplicadores
(cada uno con su justificación en la tabla) y la tarifa de referencia de USD 2.500 por mes-persona.
El costo es proporcional a la tarifa y la tabla muestra también 2.000 y 3.500.

El README se reescribió para la versión 1.0: la estructura de apps, las tecnologías (no se usan
Tailwind, Celery ni Redis, que figuraban) y la instalación. Se quitó `docs/INVENTARIO.md`, copia idéntica
de `docs/sincronizacion/INVENTARIO.md`, que es la que citan la bitácora y el plan de cierre.

### Nota · 2026-11-16 · Revisión final de las pruebas: los 258 contratos con su prueba

Los 36 contratos de la versión 14 sin prueba propia (`CO-219` y `CO-233` a `CO-267`) quedaron
cubiertos. Casi todos se cubrieron renombrando pruebas que ya verificaban el efecto. Para las
consultas se agregaron pruebas que afirman lo presentado y que nada cambió
(`apps/core/tests/test_contratos_consultas_del_nucleo.py`,
`apps/suppliers/tests/test_contratos_consultas_de_compras.py`, CO-250 y CO-251 en caja). También se
agregaron pruebas de las postcondiciones negativas que nadie miraba (CO-243, CO-247, CO-248).

Al revisarlas aparecieron pruebas con el código de otro contrato, que se corrigieron:

- tres de `CO-232` que verifican `CO-240` y `CO-244`;
- las del reembolso por el medio original, marcadas `CO-101` cuando su contrato es `CO-248`;
- quince con un código provisorio (`NUEVOCO23`) que correspondía a `CO-253`.

Corrida del 2026-11-16: 4031 pruebas, todas pasan, 97 % de cobertura. Hay 1300 pruebas de contrato
y cubren los 258 contratos.

`COBERTURA.md` sigue midiendo contra `.contexto-ia/` (219 contratos) y avisa de 39 códigos de prueba
sin contrato que los respalde. Esos códigos existen en la versión 14, pero `generar_contexto.py` lee
el `.docx` y no el documento en HTML. Queda para el responsable decidir si el generador pasa a leer
el HTML; hasta entonces, el conteo contra la versión 14 está en el Manual de Pruebas.

El Manual de Pruebas tenía rota la tabla del apéndice B: un carácter de control en la columna de
casos. Se corrigió en `pruebas/capitulos_2.py` y el manual se rearmó con la evidencia nueva: 37
páginas, sin cortes ni huecos.

### Nota · 2026-11-16 · Limpieza para la entrega

Por pedido del responsable:

- **Salen del repositorio** el `.docx` del documento de análisis, `docs/sincronizacion/`, la
  presentación de octubre y `scripts/datos/modelo_planificado.toml`. Copias en `privado/archivo/docs/`.
  El documento vigente es el HTML de `privado/documentación/`.
- **Se ocultan los generadores.** `scripts/generar_*.py` y `scripts/exportar_dss.py` siguen en la
  máquina y siguen funcionando, pero no viajan con el repositorio: se ignoran en `.gitignore`.
  `generar_contexto.py` ya no tiene el `.docx` en su ruta por defecto.
- **Sale de `.contexto-ia/` lo que no se usa**: el backlog de detalles funcionales, las
  referencias de pantallas y un archivo con una clave de API. Están en `privado/archivo/contexto-ia/`.
  Se dejan las referencias visuales que citan la hoja de estilos y las pruebas.
- **Los tres PDF de la entrega pasan a `docs/documentacion/`**: copias de la última exportación.
  Al reexportar hay que volver a copiarlos.
