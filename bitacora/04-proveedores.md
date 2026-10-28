# Bitácora — `04` Proveedores

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-04-001 · El informe de impacto de la baja declara una cifra que no puede calcular

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-PRV-BAJ`, `CO-063`
**Estado:** Resuelta — sin enmienda; se mantiene el `None`, decidido el 2026-09-22

**Qué apareció.**
El caso de uso pide que antes de dar de baja un proveedor se le muestren al Administrador dos
cifras: los productos de catálogo vinculados y las propuestas de restock afectadas. La segunda no
se puede calcular: el módulo de Restock no existe, así que no hay nada que contar.

**Qué dice la especificación.**
> `CO-063 solicitarBajaDeProveedor` — el informe de impacto previo a la confirmación.

La especificación pide las dos cifras. No dice qué debe mostrar el sistema cuando una de ellas no
se puede obtener, porque desde el documento las dos existen siempre.

**Qué se hizo.**
`ImpactoDeBaja.propuestas_de_restock` se declara en `None` y no en cero, y la pantalla dice «no se
puede calcular todavía» en vez de «ninguna». La diferencia importa para la decisión que el
Administrador está tomando: cero afirma que dar de baja no rompe nada, y eso todavía no se sabe.

**Qué habría que cambiar.**
`CO-063`, campo Salida: contemplar que una cifra del informe de impacto pueda no estar disponible,
y que el sistema lo distinga de la cifra en cero. Es un caso que se va a repetir en los otros
informes de impacto —la baja de producto, la baja de cuenta de Cliente— a medida que se construyan
antes que los módulos de los que dependen.

---

### B-04-002 · Dos pantallas del módulo se construyeron declarándose fuera de todo caso de uso

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-PRV-REA`, `CU-PRV-COL`
**Estado:** Resuelta — comentarios vencidos; corregido el código el 2026-09-22

**Qué apareció.**
Dos pantallas del módulo llevan escrito en el código que no pertenecen a ningún caso de uso:

- `ProveedorReactivarView` — «la vuelta que ningún CU describe».
- `CorreoListaView` y `CorreoDetalleView` — «no es de ningún CU: es la antesala del pipeline».

El esquema vigente describe las dos: `CU-PRV-REA` · Reactivar Proveedor Editorial, con `CO-065` y
`CO-066`; y `CU-PRV-COL` · Gestionar Cola de Correos de Proveedor, con `CO-016`, `CO-017`,
`CO-018`, `CO-157` y `CO-158`.

Como en `B-02-001`, desde el repositorio no se puede determinar si los casos de uso se agregaron
después o si los comentarios nunca fueron ciertos.

**Qué dice la especificación.**
> `CU-PRV-REA` · Reactivar Proveedor Editorial — 04 Proveedores.
> `CU-PRV-COL` · Gestionar Cola de Correos de Proveedor — 04 Proveedores.

Las dos existen con ficha y contratos.

**Qué se hizo.**
Nada sobre el comportamiento. Se registró la discrepancia.

**Qué habría que cambiar.**
En el documento, probablemente nada. Hace falta verificar lo construido contra los siete contratos
y, hecho eso, sacar del código las afirmaciones de que ningún caso de uso las describe.

---

### B-04-003 · Una referencia al esquema viejo de numeración quedó sin migrar

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-PRV-BAJ`, módulo `05` Restock
**Estado:** Resuelta — corregido el código el 2026-09-22

**Qué apareció.**
La migración de códigos del 2026-09-14 tradujo 426 referencias `CU-NN` del esquema anterior a
`CU-MOD-AAA` en 101 archivos, buscando el equivalente por lo que hace cada archivo. Una quedó sin
traducir, en `apps/suppliers/services.py`:

> «el módulo de Restock (CU-22 en adelante) todavía no existe»

`CU-22` no designa ahí un caso de uso sino el comienzo de un rango: el módulo entero. No tiene un
equivalente único en el esquema vigente —el módulo 05 tiene cinco casos de uso— y traducirlo por
cualquiera de ellos habría dicho algo que la frase no dice.

**Qué dice la especificación.**
Nada. El esquema vigente no numera módulos por rangos de casos de uso, así que la construcción
«CU-NN en adelante» no tiene forma de expresarse.

**Qué se hizo.**
Se dejó la referencia como estaba, para que la falta de equivalente sea visible en vez de quedar
resuelta por una traducción inventada.

**Qué habría que cambiar.**
Nada en el documento. Es una línea de comentario que conviene reescribir como «el módulo 05,
Restock» cuando alguien toque ese archivo. Se anota acá y no se corrige sola porque la tarea del
día era migrar numeración, no redactar comentarios.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-04-001 · Resolución de B-04-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
**Sin enmienda.** «No disponible» es un **estado de construcción**, no un caso que el contrato
tenga que contemplar. `CO-063` describe el sistema completo, donde las dos cifras del informe de
impacto existen siempre; que hoy una no se pueda calcular es una propiedad del avance del
proyecto, no del sistema especificado.

Escribir el caso en el contrato sería llevarle al documento una consecuencia del orden en que se
construye, que es justo lo que el documento no debe registrar. La distinción vale también para los
otros informes de impacto que van a pasar por lo mismo —la baja de producto, la baja de cuenta de
Cliente—: ninguno enmienda su contrato por esto.

**Qué se hizo.**
Nada. `ImpactoDeBaja.propuestas_de_restock` **se mantiene en `None`** y la pantalla sigue diciendo
«no se puede calcular todavía». La diferencia con el cero es la que importa para la decisión que el
Administrador está tomando, y se conserva.

---

### R-04-002 · Resolución de B-04-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Igual que en `B-02-001`: **`CU-PRV-REA` y `CU-PRV-COL` se incorporaron al documento el 05/09**,
después de que las pantallas existieran. Los comentarios fueron ciertos y quedaron vencidos.

**Qué se hizo.**
Se reemplazaron las afirmaciones por la referencia al caso de uso que describe cada pantalla, en
`apps/suppliers/views.py` (cabecera del módulo, `ProveedorReactivarView`, `CorreoListaView`,
`DiagnosticoLLMView`), en `apps/suppliers/urls.py`, en las tres plantillas correspondientes y en
`test_baja_proveedor.py` y `test_diagnostico_llm.py`.

La verificación contra los contratos sigue pendiente y es trabajo del plan del módulo 04.

---

### R-04-003 · Resolución de B-04-003

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
La construcción «CU-NN en adelante» no tiene equivalente porque designa un módulo, no un caso de
uso. Se escribe como lo que es: el módulo por su número y su nombre.

**Qué se hizo.**
`apps/suppliers/services.py`: «el módulo de Restock (CU-22 en adelante)» pasa a «el módulo 05,
Restock». Es la última referencia al esquema anterior de numeración que quedaba en el código.

---

### B-04-004 · Un correo sin productos identificados quedaba Procesado, y el contrato dice que falla

**Tipo:** Desvío · **Fecha:** 2026-09-30 · **Alcance:** `CU-PRV-COL`, `CU-ALT-NOV`, `CO-017` E4
**Estado:** Resuelta — el responsable decidió el 2026-09-30 que manda el contrato (consulta C-08)

**Qué apareció.**
La extracción marcaba *Procesado* un correo cuando el modelo respondía pero no identificaba
ningún producto, o lo clasificaba como algo que no es un anuncio de novedades. El código lo
justificaba como «un resultado válido, no un fallo». Es anterior al contrato.

**Qué dice la especificación.**
> «Si el servicio devuelve error, no responde dentro del tiempo configurado o no identifica
> ningún producto (E4), no se generan borradores, el correo pasa a Falló el procesamiento y
> permanece en la cola para reprocesamiento.» (`CO-017`, Excepciones)

**Qué se hizo.**
Se corrigió el código a favor del contrato. Un correo sin productos identificados queda
*Falló el procesamiento*, con el motivo escrito, y se puede reprocesar desde su ficha. Las dos
pruebas que fijaban el comportamiento anterior se reescribieron para exigir el del contrato.

**Qué habría que cambiar.**
Nada.

---

### B-04-005 · La aprobación y el reprocesamiento corren dentro de la petición

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** `CU-PRV-COL`, `CO-017`, `CO-019`
**Estado:** Resuelta — recomendación del plan 04, sin objeción del responsable (consultas C-09 y C-10)

**Qué apareció.**
El paso 5 de CU-PRV-COL dice que el sistema «ejecuta la extracción», y la extracción puede
tardar hasta el tiempo de espera configurado. El documento no dice si eso ocurre mientras la
pantalla espera o en segundo plano. Tampoco dice qué pasa con los borradores abiertos si un
reprocesamiento falla.

**Qué dice la especificación.**
`Nada` sobre dónde corre. Sobre el reprocesamiento: «reemplaza únicamente los borradores que
sigan abiertos» (`CO-019`), con «las excepciones de CO-017».

**Qué se hizo.**
La extracción corre dentro de la petición. Antes de llamar al modelo, el correo pasa a *En
proceso* con el registro bloqueado, así que una segunda aprobación simultánea encuentra el
estado y no vuelve a procesarlo (`CO-017` E1). Los borradores abiertos sólo se reemplazan si
la nueva extracción tiene éxito; si falla, se conservan.

**Qué habría que cambiar.**
`CO-019`, Notas: agregar que, si la extracción falla, los borradores abiertos se conservan.

---

### B-04-006 · Un doble clic en el alta de un proveedor terminaba en error 500

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** `CO-060`
**Estado:** Resuelta — corregido el código el 2026-10-04, encontrado en el ensayo de la demostración (plan 00, D4-04)

**Qué apareció.**
El mismo defecto que B-17-016: dos envíos idénticos a la vez pasaban la validación y el segundo
chocaba contra la unicidad de la razón social o del correo comercial, con **error 500**.

**Qué dice la especificación.**
La razón social y el correo comercial son únicos; un duplicado se informa y no se registra.

**Qué se hizo.**
El alta atrapa el choque de unicidad, vuelve a validar el formulario —que ahora ve el proveedor
que el otro envío acaba de crear— y lo devuelve con su aviso. Prueba:
`test_concurrencia_proveedores.py`, escrita antes de la corrección.

**Qué habría que cambiar.**
Nada en el documento. Otras altas con datos únicos (productos por ISBN, código de barras o código
interno; cuentas por correo) pueden tener la misma carrera y no se ensayaron: quedan en `DEUDA.md`.

---

### B-04-007 · El informe de la baja ya cuenta las propuestas de restock

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-PRV-BAJ` paso 2
**Estado:** Abierta

**Qué apareció.**
Con el módulo 05 construido, la cifra que B-04-001 dejaba «No disponible» se puede calcular.

**Qué dice la especificación.**
> «propuestas de restock afectadas» (`CU-PRV-BAJ`, paso 2)

**Qué se hizo.**
Cuenta la propuesta pendiente si tiene un pedido sin despachar a este proveedor: 0 o 1, porque
a lo sumo hay una pendiente (I-21). B-04-001 decidía mantener el valor sin calcular; ya no hace
falta.

**Qué habría que cambiar.**
Nada.

---

### B-04-008 · El historial de la ficha muestra todos los pedidos al proveedor, no sólo los de restock

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-PRV-CON` paso 4, `CO-173`, `CO-074`
**Estado:** Abierta

**Qué apareció.**
Al escribir las pruebas de contrato del padrón (V2 del plan 00): la ficha del proveedor decía
«No disponible» en el historial de pedidos, de cuando Restock no existía. Al llenarlo apareció que
al proveedor se le hacen pedidos por dos caminos —el despacho de la propuesta de restock y el
cierre de una revisión de novedades— y los dos son la misma operación, `CO-074`.

**Qué dice la especificación.**
> «historial de pedidos de restock despachados» (`CU-PRV-CON`, paso 4; `CO-173`)

**Qué se hizo.**
La ficha lista los pedidos enviados a ese proveedor por los dos caminos, con fecha, títulos,
unidades y si el correo salió o no. Dejar afuera el pedido inicial de una novedad haría que un
proveedor al que se le pidió todo por ese camino pareciera no haber recibido pedidos nunca.

**Qué habría que cambiar.**
`CU-PRV-CON` paso 4 y `CO-173`, salida: «historial de pedidos despachados al proveedor
(`CO-074`)», sin acotarlo a restock.

---

### B-04-009 · La reactivación de proveedor no ofrecía corregir los datos, y la propuesta no marcaba al proveedor inactivo

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-PRV-REA` pasos 3-8, `CO-064`, `CO-065`, `CO-066`
**Estado:** Abierta

**Qué apareció.**
Al escribir las pruebas de contrato del padrón: la reactivación era sólo un botón de confirmar,
con un enlace para «editar antes». No dejaba corregir los datos ni decidir el procesamiento de
novedades, y no validaba nada. La propuesta de restock tampoco avisaba nada cuando el proveedor
de una línea estaba dado de baja.

**Qué dice la especificación.**
> «El sistema presenta los datos vigentes del proveedor para su revisión, con el Correo Comercial
> destacado, y ofrece corregirlos antes de confirmar.» (`CU-PRV-REA`, paso 3) ·
> «LineaPropuestaRestock: las propuestas activas que lo involucraban quedaron marcadas con la
> advertencia Proveedor inactivo.» (`CO-064`)

**Qué se hizo.**
La reactivación es la revisión: el correo destacado, la razón social, la editorial y el tipo
habituales, el contacto y el procesamiento de novedades, todo corregible, y la confirmación guarda
las correcciones y reactiva en el mismo acto. Dos decisiones que la especificación no toma:

- **No pide la confirmación del cambio de correo de `CU-PRV-EDI` A1.** La pantalla entera es la
  revisión del correo; confirmar la reactivación es confirmar el correo que se ve.
- **Las notas internas no están.** El contrato no las nombra; se siguen editando desde
  `CU-PRV-EDI`, también con el proveedor inactivo.

La marca «Proveedor inactivo» de la propuesta se deriva del estado del proveedor y no se guarda en
la línea: alcanza a la línea cuyo producto tiene ese proveedor, y a la que no tiene proveedor
propio cuando el habitual de su editorial es el dado de baja y ningún otro lo reemplaza.
Reactivarlo la quita sin tocar la propuesta.

**Qué habría que cambiar.**
`CU-PRV-REA`: anotar que el cambio de correo no lleva la confirmación de `CU-PRV-EDI` A1. `CO-064`,
postcondición (c): «la advertencia se deriva del estado del proveedor mientras siga inactivo».

---

### B-04-010 · Un aviso de demora procesado termina como «Falló el procesamiento»

**Tipo:** Corrección · **Fecha:** 2026-10-26 · **Alcance:** `CU-ALT-NOV` E4, `CU-PRV-COL` E2, `CU-ALT-TRA` E1, `CU-ALT-DEM`, `CO-017`
**Estado:** Resuelta — plan 00 del circuito de proveedores, aprobado el 2026-10-26; ver B-04-011

**Qué apareció.**
El modelo clasifica cada correo como «novedades», «demora» u «otro». Si se aprueba un aviso de
demora (o una factura), el modelo lo clasifica bien, pero como no trae productos el correo pasa a
**Falló el procesamiento**, con el mensaje «el modelo no identificó ningún producto… vuelva a
procesarlo». Queda en la cola para siempre, invita a reprocesar algo que salió bien, y la demora
que anunciaba no llega a ningún lado: hay que ir producto por producto a registrarla a mano.

**Qué dice la especificación.**
> «si la extracción falla (CU-ALT-NOV E4), el correo pasa a Falló el procesamiento y permanece en
> la cola para su reprocesamiento» (`CU-PRV-COL` E2) · «el Administrador recibe aviso del proveedor
> (directamente o a través de un borrador de PA-01) y marca el producto como demorado» (`CU-ALT-TRA`
> E1)

La primera trata como falla lo que no lo es. La segunda supone que un aviso de demora produce un
borrador, y la extracción sólo arma borradores de novedades.

**Qué se hizo.**
Nada todavía.

**Qué habría que cambiar.**
`CO-017` y `CU-ALT-NOV` E4: un correo bien clasificado que no es de novedades no falla; queda con
su clasificación y sale de la cola. Si es una demora, ofrece registrarla (`CU-ALT-DEM`) sobre las
pre-ventas de ese proveedor, con el producto que el modelo haya reconocido como propuesta, nunca
aplicada (regla 4). `CU-ALT-TRA` E1 pierde la mención al borrador.

---

### B-04-011 · Un aviso de demora o un correo «otro» bien clasificados quedan Procesados, y la demora se propone

**Tipo:** Corrección · **Fecha:** 2026-10-26 · **Alcance:** `CU-ALT-NOV` E4, `CU-PRV-COL` E2, `CU-ALT-DEM`, `CU-ALT-TRA` E1, `CO-017`, `CO-018`, `CO-019`
**Estado:** Abierta — decidida por el responsable el 2026-10-26 (plan 00 del circuito de proveedores); reemplaza a B-04-010

**Qué apareció.**
Lo de B-04-010: un aviso de demora o una factura, bien clasificados por el modelo, terminaban en
«Falló el procesamiento», quedaban en la cola para siempre y la demora no llegaba a ningún lado.

**Qué dice la especificación.**
> «Si el servicio devuelve error, no responde dentro del tiempo configurado o no identifica ningún
> producto (E4), no se generan borradores, el correo pasa a Falló el procesamiento y permanece en la
> cola para reprocesamiento.» (`CO-017`, Excepciones)

**Qué se hizo.**
- Un correo que el modelo clasificó como **demora** u **otro** queda **Procesado**, sin borradores,
  con el motivo a la vista («Es un aviso de demora…», «No anuncia novedades ni demoras…»). Sigue
  fallando lo que sí es una falla: el modelo que no responde o lo que no se puede interpretar, y un
  correo de **novedades** sin ningún producto.
- La extracción de una demora lee **lo que se atrasa**: título, volumen, ISBN si lo trae, la fecha
  nueva de cada producto si la da, y la fecha general del aviso. No son altas: van aparte de los
  productos de una novedad.
- La ficha del aviso **propone registrar la demora** sobre las pre-ventas del proveedor (las de su
  editorial y las que tienen un pedido suyo en camino, para cubrir a una distribuidora). Las que el
  aviso nombra van primero, reconocidas por ISBN o por título y volumen sin importar mayúsculas ni
  tildes, con la fecha propuesta; las demás quedan plegadas por si el modelo no las reconoció. Lo que
  `CU-ALT-DEM` no admite (ya demorada, llegada vencida) dice por qué en lugar del botón. Lo que el
  aviso nombra y no es una pre-venta del proveedor se informa.
- **Nada se aplica desde el correo** (regla 4): cada fila abre la pantalla de `CU-ALT-DEM` con la
  fecha y una nota que citan el aviso, y la demora se registra recién al confirmar su informe de
  impacto. Una fecha propuesta que ya pasó no se carga. Al confirmar, se vuelve al correo.
- Un correo procesado que no era de novedades **se puede descartar después**, con motivo, para dejar
  dicho que ya se atendió. Uno de novedades procesado no: sus borradores siguen en la revisión.

**Qué habría que cambiar.**
`CO-017`, Excepciones (E4): «no identifica ningún producto» vale para un correo clasificado como
novedades; uno clasificado como demora u otro pasa a Procesado sin borradores. Postcondiciones: para
una demora, la extracción del modelo guarda lo que se atrasa. `CU-ALT-NOV` E4 y `CU-PRV-COL` E2, lo
mismo. `CU-PRV-COL` y `CO-018`: el descarte también desde Procesado, si no era de novedades.
`CU-ALT-DEM`: un flujo alternativo que entra desde el aviso de demora con la fecha propuesta.
`CU-ALT-TRA` E1 pierde la mención al borrador de PA-01.

---

### B-04-012 · La casilla se puede revisar a mano desde la consola, para la demostración

**Tipo:** Agregado · **Fecha:** 2026-10-26 · **Alcance:** `CU-ALT-NOV`, `CO-016`
**Estado:** Resuelta — plan 00 del circuito de proveedores (H)

**Qué apareció.**
Para mostrar el circuito con el correo de prueba hay que esperar a que el Temporizador lea la
casilla según la frecuencia de Parámetros, y no había forma de escribir un correo de proveedor a
mano: sólo los generados al azar.

**Qué dice la especificación.**
`Nada.` `CO-016` lo dispara el Temporizador.

**Qué se hizo.**
`manage.py revisar_casilla` corre el mismo ciclo de `CO-016` en el momento, sin mirar la
frecuencia: deja en la cola lo nuevo y no procesa nada. Fuera del sistema, una página local de la
demostración (`scripts/demo/redactar_correo.py`) permite escribir el correo como lo escribiría una
editorial —remitente, asunto, texto, tabla de productos con portadas— desde tres plantillas
(novedades, demora, libre), mandarlo al correo de prueba o bajarlo como `.eml`.

**Qué habría que cambiar.**
`Nada`: son herramientas de operación y de demostración, no casos de uso.

---

### B-04-013 · El Administrador revisa la casilla desde la cola, sin esperar al Temporizador

**Tipo:** Agregado · **Fecha:** 2026-10-26 · **Alcance:** `CU-PRV-COL`, `CU-ALT-NOV`, `CO-016`
**Estado:** Abierta — pedida por el responsable el 2026-10-26

**Qué apareció.**
Probar el circuito de correos obligaba a ir a la consola a correr `revisar_casilla` (B-04-012) o
a esperar la frecuencia de Parámetros cada vez que un proveedor mandaba algo.

**Qué dice la especificación.**
`Nada` sobre un disparo manual: `CO-016` lo ejecuta el Temporizador según la frecuencia
configurada, y `CU-PRV-COL` empieza con los correos ya en la cola.

**Qué se hizo.**
La cola de correos gana el botón **«Revisar la casilla»**, sólo para el Administrador y sólo
cuando la casilla está configurada. Corre el mismo ciclo de `CO-016` en el momento, sin mirar la
frecuencia: deja en la cola lo nuevo, **Pendiente, sin procesar nada** —el modelo sigue leyendo
cada correo recién cuando se aprueba (`CO-017`)— y dice cuántos entraron, que no había nada o que
no se pudo conectar (con el mismo aviso a los administradores que da el Temporizador). La
pantalla muestra cuándo se revisó la casilla por última vez. Revisarla dos veces seguidas no
duplica nada (I-16).

**Qué habría que cambiar.**
`CU-PRV-COL`: un flujo alternativo «Revisar la casilla ahora», que ejecuta `CO-016` sin esperar la
frecuencia. `CO-016`, Referencias Cruzadas: también `CU-PRV-COL`, con el Administrador como actor.
El DSS de `CU-PRV-COL` muestra el evento.

---

### B-04-014 · El volumen pegado al título se separa, y la pre-venta elegida de la lista recibe la fecha del aviso

**Tipo:** Agregado · **Fecha:** 2026-10-26 · **Alcance:** `CU-ALT-NOV`, `CU-PRV-COL`, `CU-ALT-DEM`, `CO-017`
**Estado:** Abierta — observada por el responsable el 2026-10-26, probando un aviso real

**Qué apareció.**
Un aviso de demora de «Ichi The Witch #1»: el modelo copió el título con el «#1» y dejó el
volumen vacío, así que la propuesta no reconoció el tomo, que estaba en pre-venta. Al buscarlo a
mano en la lista de las demás pre-ventas (41, sin buscador), la fila no traía la fecha que el
aviso sí daba: había que escribirla de nuevo en la pantalla de la demora.

**Qué dice la especificación.**
`Nada` sobre el volumen escrito dentro del título. `CO-017` pide copiar los datos y no completarlos.

**Qué se hizo.**
- Si el modelo deja el volumen vacío y el título termina con una marca explícita —«#1», «vol. 5»,
  «Tomo 24», «Nº 109»—, el número pasa al volumen y sale del título. Sin marca no se toca: en
  «Kaiju No. 8», «Mono 3» o «Another 0» el número es parte del título. Vale para las novedades y
  para las demoras, y el cruce con las pre-ventas lo aplica también a lo extraído antes. El prompt
  pide además separarlos (versión 4).
- La pre-venta que se elige de la lista recibe como propuesta la fecha general del aviso o, si el
  aviso da una sola, esa. Con dos fechas distintas no se propone ninguna. Sigue sin aplicarse
  nada hasta confirmar la demora.
- La lista de las demás pre-ventas tiene un buscador por título, número o código.
- La fecha de lo que se atrasa se muestra como el resto del sistema (dd/mm/aaaa).

**Qué habría que cambiar.**
`CO-017`, Notas: el volumen que el modelo deja dentro del título con una marca explícita se
separa; sin marca, el título queda como vino.

---

### B-04-015 · La casilla se revisa cada pocos minutos, no cada horas

**Tipo:** Corrección · **Fecha:** 2026-10-27 · **Alcance:** `CO-016`, `CO-130`, `CU-CFG-PAR`
**Estado:** Abierta — pedido del responsable el 2026-10-27

**Qué apareció.**
Con los avisos por Telegram (B-19-004), un correo de un proveedor tiene que llegar al teléfono enseguida.
La frecuencia de la casilla se medía en horas, el valor era de 24, y el Temporizador de la VM corre una
vez por día: un correo podía esperar un día entero, y el aviso en el teléfono no servía de nada.

**Qué dice la especificación.**
> «frecuencia de monitoreo de la casilla (horas) : entero ≥ 1» (modelo de dominio, ConfiguracionSistema)

**Qué se hizo.**
- La frecuencia pasa a **minutos**, con 5 por defecto. Los valores guardados se convirtieron: el 24
  de fábrica pasó a 5, y cualquier otro valor se multiplicó por 60.
- En la VM, una tarea propia corre **cada minuto** y revisa la casilla **sólo si ya le toca** según
  Parámetros. El Temporizador diario sigue haciendo lo suyo.
- En la PC de desarrollo, el bot escuchando (`telegram escuchar`) revisa la casilla entre consulta y
  consulta, con la misma frecuencia. El botón «Revisar la casilla» de la cola sigue revisando al
  momento (B-04-013).
- Revisar sigue siendo sólo encolar: el procesamiento lo dispara una persona (`CO-017`).

**Qué habría que cambiar.**
Modelo de dominio, ConfiguracionSistema: «frecuencia de monitoreo de la casilla (minutos) : entero ≥ 1».
`CU-CFG-PAR` y `CO-130`: el parámetro en minutos. `CO-016`: el ciclo corre cada minuto y respeta la
frecuencia, y no una vez por día junto con el Temporizador.
