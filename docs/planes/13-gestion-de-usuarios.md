> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `13` Gestión de Usuarios

**Estado del plan:** Propuesto · **Fecha:** 2026-09-14

**Qué clase de plan es éste.** Igual que el del módulo 12: no planifica construir sino verificar
lo construido contra sus contratos.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-USR-ALT` | `CO-120` | 1 | 0 |
| `CU-USR-MOD` | `CO-121`, `CO-122`, `CO-197` | 2 | 1 |
| `CU-USR-BAJ` | `CO-123`, `CO-156`, `CO-198` | 1 | 2 |
| `CU-USR-REA` | `CO-122`, `CO-124`, `CO-156`, `CO-199` | 2 | 2 |
| `CU-USR-ELI` | `CO-125`, `CO-156`, `CO-200` | 1 | 2 |
| `CU-USR-CON` | `CO-201`, `CO-202` | 0 | 2 |

**Total del módulo:** 6 contratos propios (`CO-120` a `CO-125`) más 7 de consulta (`CO-197` a
`CO-202`) y `CO-156`, compartido con otros seis módulos. 14 en total.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Usuario` | Sí | Lo crea, lo modifica y —único caso del sistema— lo elimina físicamente |
| `RegistroAuditoria` | Sí | Lo crea. `CO-125` depende del **orden**: primero la entrada, después el borrado |
| `EnlaceActivacion` | **No** | `CO-120`, `CO-122` y `CO-124` lo crean o lo invalidan |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-124`, firma y postcondición | «`confirmarReactivacionDeUsuario(usuario, rol)`» y «u.rol quedó con el valor declarado»: o la reactivación pide un rol, o restaura el anterior. Las Notas dicen explícitamente que **no** debe restaurarlo | Decisión del responsable: construirlo. Registrada en B-13-002 |
| 2 | `CO-198` E1 frente a `CO-123` E1 | El bloqueo del último Administrador: ¿en la solicitud, en la confirmación, o en las dos? `CO-202` enuncia el principio —«la interfaz no decide, refleja»— que resuelve a favor de las dos | Decisión del responsable. Registrada en B-13-003 |
| 3 | `CO-125`, precondición | Cita `I-14`, que es el invariante de `ConfiguracionSistema`. No hay invariante que exprese «nunca inició sesión» | Enmienda de redacción. Registrada en B-13-004 |
| 4 | `CO-124` E2 | Declara una colisión de correo que `I-10` vuelve imposible | Enmienda o explicación. Registrada en B-13-004 |
| 5 | `CO-202` | Declara `consultarFichaDeUsuario` como operación propia. El sistema no tiene pantalla de ficha: el listado y el formulario de edición cubren lo que pide mostrar | Decisión: o se construye la ficha, o `CO-202` se declara cubierto por las dos pantallas que existen |

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CU-USR-ALT` | — | Crea la cuenta que todo lo demás modifica |
| 2 | `CU-USR-CON` | `CU-USR-ALT` | Necesita cuentas que listar |
| 3 | `CU-USR-MOD` | `CU-USR-ALT` | — |
| 4 | `CU-USR-BAJ` | `CU-USR-ALT` | — |
| 5 | `CU-USR-REA` | `CU-USR-BAJ` | Necesita una cuenta dada de baja |
| 6 | `CU-USR-ELI` | `CU-USR-ALT` | Necesita una cuenta pendiente que nunca se usó |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| `I-12` se sostiene con un bloqueo de registro | `CO-121` E1, `CO-123` E1 | El resguardo usa `select_for_update()`. Este pase verifica el resultado, **no la carrera**: falta la prueba de concurrencia que pide el foco reforzado |
| El orden de `CO-125` es parte del contrato | `CO-125` | Se verifica por su consecuencia: la entrada de auditoría conserva el correo del titular después de que el registro dejó de existir |
| El control de acceso puede vivir en la pantalla y no en el servidor | Todo el módulo | Las pruebas de acceso ejercen el `POST` real con el rol equivocado, no la vista |
| La eliminación física no tiene vuelta atrás | `CO-125` | Se prueba que las tres condiciones que la impiden —Activa, Inactiva, Pendiente con historial— la rechazan por la dirección real |

---

## 6. Fuera de alcance

- **La prueba de concurrencia de `I-12`.** Dos administradores quitándose el rol a la vez es un
  caso declarado del foco reforzado y no está cubierto. Queda pendiente.
- **La capa de flujo**, ya cubierta por las pruebas descriptivas existentes.
- **Construir lo que las ambigüedades 1, 2 y 5 destraben.** Este pase las detecta y las deja
  escritas como `xfail(strict=True)`; implementarlas es otra unidad de trabajo.
