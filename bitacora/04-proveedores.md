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
