# Bitácora — `16` Auditoría

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-16-001 · El filtro por tipo de acción ofrece las acciones del log, agrupadas

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-AUD-CON` paso 3, `CO-205`
**Estado:** Abierta — recomendación del plan aplicada (consulta C-15)

**Qué apareció.**
La ficha enumera nueve categorías de acción. El log guarda un enumerado cerrado de acciones
concretas, hoy 41, y ninguna parte del documento dice qué acción cae en qué categoría.

**Qué dice la especificación.**
> «tipo de acción (alta / modificación / eliminación / cobro / cancelación / cambio de rol /
> inicio de sesión / cierre de sesión / exportación)» (`CU-AUD-CON`, paso 3)

**Qué se hizo.**
El filtro ofrece las acciones del enumerado, agrupadas por área para encontrarlas: sesiones,
cuentas, productos, catálogos, precios y parámetros, proveedores y correos, contenido de la
tienda y exportaciones. No se inventó el mapeo a las nueve categorías.

**Qué habría que cambiar.**
`CU-AUD-CON`, paso 3: reemplazar la lista de categorías por «tipo de acción, entre las acciones
declaradas en `RegistroAuditoria`», o declarar en el modelo de dominio a qué categoría pertenece
cada acción.

---

### B-16-002 · El filtro por rol usa el rol que la cuenta tiene hoy

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-AUD-CON` paso 3
**Estado:** Abierta — recomendación del plan aplicada (consulta C-15)

**Qué apareció.**
La entrada del log guarda la cuenta y el correo del actor, no el rol que tenía al actuar.

**Qué dice la especificación.**
> «actor (usuario específico o tipo de rol)» (`CU-AUD-CON`, paso 3)

**Qué se hizo.**
El filtro por rol usa el rol **actual** de la cuenta. Una cuenta eliminada no aparece en ningún
rol, pero sí buscándola por su correo, que la entrada conserva. La pantalla lo dice debajo de los
filtros.

**Qué habría que cambiar.**
Si se quiere el rol al momento de actuar: `MODELO_DE_DOMINIO.md`, `RegistroAuditoria`, agregar
«rol del actor» y registrarlo en cada entrada.

---

### B-16-003 · La exportación neutraliza las celdas que una planilla leería como fórmulas

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-129`, `CO-037`
**Estado:** Abierta

**Qué apareció.**
El correo de un actor o el detalle de una entrada pueden empezar con `=`, `+`, `-` o `@`. Al abrir
el archivo, la planilla de cálculo los ejecutaría como fórmulas.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Esas celdas se exportan precedidas por un apóstrofo, que la planilla muestra como texto. El
archivo lleva además la marca de codificación para que los acentos se lean bien.

**Qué habría que cambiar.**
`CO-129`, Notas: «Las celdas que empiezan con un carácter de fórmula se exportan como texto».

---

### Nota de cierre · 2026-10-02

`CU-AUD-CON` completo: consulta paginada con filtros, detalle y exportación CSV auditada. El log
responde 403 a toda escritura. No queda nada pendiente del módulo salvo las enmiendas de las tres
entradas.

---

### B-16-004 · La inmutabilidad del log pasa a la base de datos

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** I-13, `RegistroAuditoria`
**Estado:** Resuelta — decidido por el responsable el 2026-10-04 (plan 00, decisión 4: «hay que hacer las cosas bien»)

**Qué apareció.**
Preparando la demostración (D3-10) se verificó hasta dónde llega la garantía. `save()` y
`delete()` del modelo rechazaban la escritura, pero un `update()` o `delete()` de queryset y una
sentencia SQL directa modificaban y borraban entradas sin obstáculo. `DEUDA.md` decía que I-13 la
respetaba «cualquier escritura», y no era cierto.

**Qué dice la especificación.**
> «Una entrada del log no se modifica ni se borra, por ningún rol ni por ningún camino» (I-13)

**Qué se hizo.**
Un disparador de PostgreSQL (`core.0023`) rechaza toda modificación y todo borrado de una entrada,
con el mensaje «El log de auditoría es inmutable». Admite una sola escritura: la que hace la
propia base al eliminar una cuenta o un tipo de objeto, que pone en nulo `actor_id` u
`objetivo_tipo_id` sin tocar nada más; el correo del actor queda en la entrada. Las pruebas
(`test_inmutabilidad_auditoria_en_la_base.py`) se escribieron antes y fallaban 6 de 8.

**Límite conocido:** `TRUNCATE` sobre la tabla no lo detiene un disparador de fila. Exige ser el
dueño de la tabla, y Django lo usa para vaciar la base entre pruebas.

**Qué habría que cambiar.**
Nada en el documento.

---

### B-16-005 · Cada modificación guarda qué se cambió y cómo estaba antes, también las imágenes

**Tipo:** Corrección · **Fecha:** 2026-11-17 · **Alcance:** `CO-206`, `CO-131`, `CO-133`, `CO-134`, `CO-135`, `CO-253`, `CO-255`, `RegistroAuditoria`
**Estado:** Resuelta — pedido del responsable del 2026-11-17, por exigencia de la cátedra (plan 16, segunda parte, aprobado con las recomendaciones)

**Qué apareció.**
La cátedra exige que toda modificación deje registrado qué se cambió y cómo estaba antes: un
valor, un banner, una imagen. El log guardaba el par anterior → nuevo dentro de un texto libre, y
en cinco operaciones lo anterior se perdía. Al reemplazar un banner, el logo, el fondo o la imagen
del ingreso, el archivo viejo se borraba y el log decía sólo «imagen reemplazada». Al eliminar un
banner se borraba su imagen. La FAQ guardaba sólo el largo del contenido anterior. Los canales de
aviso guardaban cómo quedaron, no cómo estaban. Las secciones de la portada decían «imagen
cambiada en …» sin la anterior. Lo mismo pasaba con las imágenes adicionales que se quitan de un
producto.

**Qué dice la especificación.**
> «Presentar timestamp, actor, acción, entidad, identificador, valor anterior y valor nuevo cuando aplican.» (`CO-206`)
>
> «La imagen anterior no se conserva.» (`CO-133`, Notas)

**Qué se hizo.**
Cada entrada guarda, además del texto, la lista de lo que cambió: el campo, cómo estaba antes y
cómo quedó. El detalle de la entrada lo presenta en una tabla «Qué se cambió · Cómo estaba antes ·
Cómo quedó», y cuando el valor es una imagen muestra las dos. Las imágenes reemplazadas o quitadas
**ya no se borran**: banner, logo, fondo, imagen del ingreso, imagen de una sección o de una
tarjeta, e imágenes adicionales de un producto. La FAQ guarda el contenido anterior entero; los
canales, cómo estaban; el producto, la sinopsis completa y la portada como imagen. La clave del
modelo de lenguaje nunca entra al log: queda «(oculta) → reemplazada». Las entradas anteriores a
este cambio no tienen la lista y se siguen viendo por su texto: el log es inmutable y no se
reescriben. Las bajas y reactivaciones quedan como estaban, porque la acción ya dice el estado,
salvo la eliminación de un banner, que ahora deja su imagen en el log.

**Qué habría que cambiar.**
- `CO-133`, Notas: «La imagen anterior se conserva y el registro de auditoría la presenta como
  valor anterior». En las postcondiciones, la entrada de auditoría lleva también la imagen
  anterior y la nueva, no sólo la posición.
- `CO-131`: lo mismo para el logo, la imagen de fondo y la del ingreso.
- `CO-134`: la entrada de auditoría conserva la imagen del banner eliminado.
- `CO-135` y `CO-136`: la entrada lleva el contenido anterior.
- `RegistroAuditoria` en el modelo de dominio: el atributo «cambios» (campo, valor anterior,
  valor nuevo).
- `CU-AUD-CON` paso 5: la presentación en tabla, con las imágenes.
- El plan 16, ambigüedad 3 de la primera parte, queda superada por esta parte.

---

### B-16-006 · Las entradas viejas muestran sus reemplazos en la tabla, leídos del detalle

**Tipo:** Agregado · **Fecha:** 2026-11-17 · **Alcance:** `CO-206`
**Estado:** Resuelta — pedido del responsable del 2026-11-17

**Qué apareció.**
Las entradas anteriores a B-16-005 no tienen la lista de cambios, y sus reemplazos se leían en una
sola línea («nombre: «Ivra» → «Ivrea»; activa: «no» → «sí»»), difícil de seguir cuando cambian
varios campos.

**Qué dice la especificación.**
Nada sobre la forma de presentarlos. El plan 16, ambigüedad 3 de la primera parte, había decidido
no separar el detalle con un análisis de texto.

**Qué se hizo.**
El detalle de una entrada vieja arma la misma tabla leyendo los reemplazos de su texto, con un
aviso de que salen del detalle. Se reconocen sólo las dos formas que el sistema escribió:
`campo: «antes» → «después»` en cualquier acción, y `campo: antes → después` en las acciones que
modifican. Lo que no tiene esa forma queda sólo en el texto, para que la tabla nunca diga algo que
la entrada no dice. La entrada no se modifica. Sobre la base de la presentación, las 71
modificaciones viejas con un reemplazo se leen enteras.

**Qué habría que cambiar.**
Nada en el documento: es presentación.
