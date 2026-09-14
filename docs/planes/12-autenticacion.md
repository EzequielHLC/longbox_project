> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `12` Autenticación

**Estado del plan:** Propuesto · **Fecha:** 2026-09-14

**Qué clase de plan es éste.** No planifica construir el módulo: el módulo está construido desde
antes de que existieran los contratos. Planifica **verificarlo** contra ellos, que es la única
puerta que le falta. La plantilla se usa igual porque las preguntas que hace —qué cubre, qué
conceptos toca, qué ambigüedades hay— son las mismas.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-AUT-INI` | `CO-114`, `CO-115` | 2 | 0 |
| `CU-AUT-FIN` | `CO-116` | 1 | 0 |
| `CU-AUT-REC` | `CO-117`, `CO-118` | 2 | 0 |
| `CU-AUT-ACT` | `CO-119`, `CO-122`, `CO-196` | 2 | 1 |

**Total del módulo:** 6 contratos propios (`CO-114` a `CO-119`), más `CO-122` y `CO-196` que
pertenecen al módulo 13 y al capítulo de consultas y se verifican allí.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Usuario` | Sí | Lo modifica: estado y credencial |
| `IntentoFallido` | Sí | Lo crea |
| `RegistroAuditoria` | Sí | Lo crea |
| `ConfiguracionSistema` | Sí | Sólo lo lee — y hoy **no**: ver la ambigüedad 1 |
| `TokenRecuperacion` | **No** | `CO-117` y `CO-118` lo crean y lo consumen |
| `EnlaceActivacion` | **No** | `CO-119` lo consume |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-114`, postcondición | «Expiración por inactividad según `ConfiguracionSistema`»: o la entidad debe ganar ese campo, o el contrato debe decir que el plazo es de configuración de despliegue | Una decisión del responsable. Registrada en `bitacora/12-autenticacion.md`, B-12-001 |
| 2 | `CO-117`, `CO-118`, `CO-119` | Las postcondiciones nombran instancias de dos conceptos `<<planificado>>`: o se construyen las entidades, o las postcondiciones se reescriben sobre lo observable | Una decisión del responsable. Registrada en B-12-002 |
| 3 | `CO-114`, precondición | «El usuario no tiene una sesión activa vigente en ese dispositivo»: ¿es un resguardo que el sistema debe imponer, o la descripción de la situación normal? Hoy iniciar sesión sobre una sesión abierta simplemente la reemplaza | Una decisión del responsable. No bloquea: no hay prueba escrita para esa precondición |

**Ninguna de las tres bloquea el módulo.** Las dos primeras impiden que `CU-AUT-REC` y
`CU-AUT-ACT` pasen la puerta de contratos en sentido estricto, y eso queda declarado en
`docs/ESTADO.md` en vez de disimularse.

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CU-AUT-INI` | — | Es la operación que todas las demás presuponen |
| 2 | `CU-AUT-FIN` | `CU-AUT-INI` | Necesita una sesión que cerrar |
| 3 | `CU-AUT-REC` | `CU-AUT-INI` | Verifica que la credencial nueva sirve para entrar |
| 4 | `CU-AUT-ACT` | `CU-USR-ALT` (módulo 13) | Necesita una cuenta pendiente, que la crea `CO-120` |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| El bloqueo por intentos depende de una ventana temporal | `CO-114` E1 | Con `freeze_time`, adelantando el reloj más allá de la ventana y verificando que el bloqueo se levanta solo. Nunca con una fecha fija |
| La invalidación de sesiones es «en cualquier dispositivo» en `CO-118` y «sólo el actual» en `CO-116` | Las dos postcondiciones se parecen y son opuestas | Dos clientes HTTP distintos en la misma prueba, y una postcondición negativa explícita para `CO-116` |
| Enviar correo sale del sistema | `CO-117`, `CO-119` | La red está cortada por la fixture `sin_red`; el correo se inspecciona en `mail.outbox` |

---

## 6. Fuera de alcance

- **La capa de flujo.** Este pase cubre contrato y acceso. El recorrido de punta a punta de cada
  caso de uso ya está en las pruebas descriptivas que existían (`test_login.py`,
  `test_recuperar_contrasena.py`, `test_activacion_cuenta.py`) y no se duplica.
- **Verificar `CO-122` y `CO-196`** desde acá: se verifican con el módulo 13, que es donde viven.
- **Renombrar las pruebas descriptivas existentes.** Conviven con las de contrato; la decisión de
  unificarlas o no está abierta en `docs/DEUDA.md`.
