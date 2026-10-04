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
