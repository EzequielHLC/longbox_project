# Bitácora — `12` Autenticación

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-12-001 · Los parámetros de sesión y de bloqueo son constantes, y el contrato los declara configurables

**Tipo:** Desvío · **Fecha:** 2026-09-14 · **Alcance:** `CU-AUT-INI`, `CO-114`, `CO-115`, `CU-CFG-PAR`
**Estado:** Resuelta — desvío confirmado; manda el contrato, decidido el 2026-09-22

**Nota sobre el tipo.** Un desvío se consulta antes de tomarlo, nunca se registra después. Éste se
registra después porque no se tomó como desvío: el código es anterior a la existencia del
contrato, y la divergencia recién se vio al comparar los dos el 2026-09-14.

**Qué apareció.**
Tres valores que gobiernan el acceso viven como constantes en `config/settings/base.py`:

- `LOGIN_INTENTOS_MAXIMOS = 5`
- `LOGIN_BLOQUEO_MINUTOS = 15`
- `SESSION_COOKIE_AGE = 30 * 60`

El propio archivo lo deja anotado: «Queda como constante hasta que Configuración del Sistema lo
haga parametrizable desde un panel». `ConfiguracionSistema` existe en el código y ya guarda el
margen de ganancia, el stock inicial por defecto y la configuración del modelo de lenguaje; estos
tres no están ahí.

**Qué dice la especificación.**
> `CO-114 iniciarSesion`, Excepciones — «Tras 5 intentos fallidos consecutivos desde el mismo
> dispositivo, se bloquea el acceso por el período **parametrizado** […]»

> `CO-114`, Postcondiciones — «Se estableció una sesión con el nivel de permisos del rol y un token
> con expiración por inactividad **según `ConfiguracionSistema`**.»

El contrato nombra a `ConfiguracionSistema` de forma explícita. No es una lectura: es el nombre de
la entidad.

**Qué se hizo.**
Se dejaron como constantes de entorno. El comportamiento observable es el que el contrato pide
—cinco intentos, bloqueo temporal, expiración por inactividad con renovación— pero un
Administrador no puede cambiar ninguno de los tres sin tocar código.

**Qué habría que cambiar.**
Nada en el documento: el contrato está bien y el código es el que se aparta. Lo que hace falta es
decidir **cuándo** se cierra la brecha, porque tiene dos consecuencias que no se ven:

1. `CO-114` y `CO-115` no se pueden verificar en su forma declarada mientras el origen del valor
   sea otro. Una prueba de contrato que lea el valor de `settings` estaría verificando el sistema
   que hay, no el que el contrato declara.
2. `CU-CFG-PAR` pide una sección «Seguridad» en el panel de parámetros. Esos tres valores son su
   contenido, así que la sección no se puede construir sin mover esto primero.

Anotado también como decisión transversal en `docs/DEUDA.md`.

---

### B-12-002 · Tres postcondiciones del módulo no tienen sujeto sobre el cual afirmarse

**Tipo:** Corrección · **Fecha:** 2026-09-14 · **Alcance:** `CO-117`, `CO-118`, `CO-119`, `CO-122`
**Estado:** Resuelta — es un desvío; se construye, decidido el 2026-09-22

**Qué apareció.**
Al escribir las pruebas de contrato del módulo, tres postcondiciones no se pudieron transcribir:

| Contrato | La postcondición | Por qué no se puede afirmar |
| --- | --- | --- |
| `CO-117` | «(a) se creó tr : TokenRecuperacion […] y se formó tr → Usuario» | `TokenRecuperacion` no existe como tabla |
| `CO-118` | «(c) tr.estado pasó de Vigente a Consumido» | Ídem: no hay instancia cuyo estado leer |
| `CO-119` | «(c) EnlaceActivacion.estado pasó de Vigente a Consumido» | `EnlaceActivacion` no existe como tabla |

Los dos conceptos están declarados `<<planificado>>` en `MODELO_DE_DOMINIO.md`, Área 1, con la
justificación de por qué son conceptos y no atributos. El sistema los resuelve hoy con tokens
firmados de Django: un token firmado distingue válido de inválido y nada más. No hay tres estados,
no hay instancia, no hay transición que mirar.

**Qué dice la especificación.**
> `CO-119`, Postcondiciones — «(c) EnlaceActivacion.estado pasó de Vigente a Consumido; no admite
> un segundo uso.»

La segunda mitad de esa misma frase —«no admite un segundo uso»— **sí** es observable, y es la que
la prueba afirma.

**Qué se hizo.**
Las pruebas afirman el efecto observable en lugar de la transición declarada, y lo dicen en el
nombre: `test_CO118_el_token_queda_consumido_efecto_observable`,
`test_CO119_el_enlace_no_admite_un_segundo_uso_efecto_observable`. El sufijo está puesto para que
nadie lea la suite y crea que la postcondición literal está verificada. **No lo está, y no puede
estarlo hasta que los dos conceptos existan.**

**Qué habría que cambiar.**
Nada en el documento: el modelo de dominio ya justifica por qué son conceptos, y los contratos son
coherentes con él. Lo que hay que decidir es **cuándo** se construyen las dos entidades. Mientras
no existan, `CU-AUT-REC` y `CU-AUT-ACT` no pueden pasar la puerta de contratos en sentido estricto,
por más que su comportamiento observable sea el correcto. Está anotado así en `docs/ESTADO.md`.

---

### B-12-003 · EnlaceActivacion y TokenRecuperacion existen como conceptos con estado

**Tipo:** Agregado · **Fecha:** 2026-09-22 · **Alcance:** `CO-117` a `CO-120`, `CO-122`, `CO-124`, `CO-125`
**Estado:** Resuelta — construido el 2026-09-22

**Qué apareció.**
Al construir los dos conceptos que `B-12-002` dejaba pendientes apareció una pregunta que el
modelo de dominio no resuelve y los contratos tampoco: **qué relación guarda la fila con la
credencial que viaja en el correo.** El modelo declara el concepto —vigencia, estado, momento de
emisión— y no dice si el enlace del correo *es* esa fila, ni cómo llega el sistema de una a la
otra.

No es una pregunta ociosa. Si la fila fuera la credencial, su identificador tendría que viajar en
la URL, y un identificador de fila es adivinable: el enlace de activación de la cuenta 41 sería
`/activar/41/`.

**Qué dice la especificación.**
> `MODELO_DE_DOMINIO.md`, Área 1 — «class EnlaceActivacion <<planificado>> { vigencia : 48 horas ·
> estado : {Vigente, Consumido, Vencido} · emitido en : fecha y hora }»

Declara los atributos. Sobre la forma de la credencial, nada, y es correcto que no diga nada: es
una decisión de implementación y no de dominio.

**Qué se hizo.**
**La fila acompaña al token, no lo reemplaza.** La credencial sigue siendo el token firmado de
Django, que se deriva del hash de la contraseña y por eso se invalida solo al usarse. La fila es
el **sujeto** de las postcondiciones: es la que tiene estado, la que pasa de Vigente a Consumido y
la que puede decir *por qué* un enlace fue rechazado.

Esa última es la ganancia que el modelo de dominio anticipaba y que ahora se puede ver en
pantalla: `CU-AUT-ACT` E1 («vencido») y E2 («ya utilizado») decían lo mismo porque el token no
distingue más que válido de inválido. Ahora dicen cosas distintas, y `CU-AUT-REC` E1 también.

Tres decisiones que conviene tener a la vista:

| Decisión | Por qué |
| --- | --- |
| `estado` es un campo y no un derivado | Los contratos declaran que el estado **pasó** de un valor a otro, y un campo derivado no puede haber pasado de nada |
| El vencimiento por reloj se resuelve al leer (`estado_actual`) | Nadie está mirando en el instante en que un plazo se cumple. Lo que sí se escribe es la transición que alguien provoca: consumirlo o reemplazarlo |
| Al emitir uno nuevo, el anterior queda Vencido y **no se borra** | Cuántos enlaces hizo falta emitir para una cuenta es un dato; una fila borrada no lo cuenta |

Las dos clases comparten una base abstracta: son el mismo concepto con distinta vigencia y
distinto caso de uso. `EnlaceActivacion` dura 48 horas y lo emite un Administrador sobre una
cuenta que acaba de crear; `TokenRecuperacion` dura 30 minutos y lo pide cualquiera que sepa un
correo.

Las siete pruebas que llevaban `_efecto_observable` verifican ahora la postcondición literal y
perdieron el sufijo. Varias se partieron en dos, porque la frase del contrato declara dos cosas
—«pasó a Consumido» y «no admite un segundo uso»— y agrupar dos postcondiciones en una prueba
deja sin saber cuál falló.

**Qué habría que cambiar.**
Nada obligatorio. Dos cosas que convendría que el documento dijera, ahora que hay dónde decirlas:

- **`MODELO_DE_DOMINIO.md`, Área 1: los dos conceptos pasan de `<<planificado>>` a
  `<<construido>>`.** Con eso el conteo queda en 21 construidos y 18 planificados.
- **El modelo declara la vigencia y el estado, pero no la regla de que sólo puede haber un enlace
  Vigente por cuenta**, que es lo que `CO-122` implica al mandar vencer el anterior. Hoy esa regla
  vive en el código. Si es una invariante, merece número.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-12-001 · Resolución de B-12-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna · **Tipo confirmado:** Desvío

**Qué se decidió.**
**Manda el contrato**, y el código es el que se aparta. Pero no los tres valores por igual: la
resolución los separa.

| Valor | Dónde vive | Por qué |
| --- | --- | --- |
| Expiración de sesión por inactividad | `ConfiguracionSistema`, sección **Seguridad** de `CU-CFG-PAR` | Parametrizable |
| Período de bloqueo por intentos fallidos | Ídem | Parametrizable |
| Cantidad de intentos fallidos (5) | **Fijo** | `CO-114` lo declara como número, no como parámetro |

`CO-114` dice «tras 5 intentos fallidos consecutivos […] se bloquea el acceso por el período
**parametrizado**». El adjetivo cae sobre el período, no sobre la cantidad. Los 5 intentos son
fijos por contrato y no van al panel.

La sección Seguridad de `CU-CFG-PAR` tiene entonces **dos** valores, no tres.

**Una corrección a la entrada original.** El punto 1 afirma que `CO-114` y `CO-115` no se pueden
verificar mientras el origen del valor sea otro. Es cierto de `CO-114` y **no** de `CO-115`:
`CO-115 extenderSesion` declara que el plazo de expiración por inactividad **queda renovado**, y
eso es verdadero cualquiera sea el origen del plazo. **`CO-115` está verificado.** Lo que el
desvío bloquea es únicamente la mitad de `CO-114` que nombra a `ConfiguracionSistema`.

**Qué se hizo.**
Nada todavía en el código. El trabajo —mover los dos valores a `ConfiguracionSistema` y abrir la
sección Seguridad— **va al plan del módulo 17**, que es donde `CU-CFG-PAR` se reconcilia.

---

### R-12-002 · Resolución de B-12-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna · **Tipo confirmado:** Desvío

**Qué se decidió.**
La entrada se registró como `Corrección` y **no lo es**: la especificación dice algo, lo dice bien
—el modelo de dominio justifica por qué `EnlaceActivacion` y `TokenRecuperacion` son conceptos y
no atributos— y el código se aparta igual. Eso es un **desvío**.

La distinción no es de etiqueta. Una corrección se salda enmendando el documento; un desvío se
salda construyendo lo que el documento declara, o consultando para apartarse. Acá se construye.

**Qué se hizo.**
Los dos conceptos se construyen con sus tres estados —Vigente, Consumido, Vencido— según el Área 1
del modelo de dominio y los contratos `CO-117` a `CO-120` y `CO-122`. Con eso, las postcondiciones
que hoy se afirman por su efecto observable pasan a afirmarse literalmente y las pruebas pierden
el sufijo `_efecto_observable`.

Queda registrado en la entrada `B-12-003`.

---

### B-12-004 · El bloqueo y la expiración de la sesión salen de Parámetros

**Tipo:** Agregado · **Fecha:** 2026-10-19 · **Alcance:** `CO-114`, `CU-CFG-PAR` (Seguridad), B-12-001
**Estado:** Abierta

**Qué apareció.**
B-12-001 había decidido que manda el contrato: los valores tenían que salir de
`ConfiguracionSistema`. Faltaba construirlo.

**Qué dice la especificación.**
> «se bloquea el acceso por el período parametrizado»; «un token con expiración por inactividad
> según `ConfiguracionSistema`» (`CO-114`)

**Qué se hizo** (plan 00, A3).
Parámetros gana la sección Seguridad: expiración de la sesión por inactividad (30 minutos) y
bloqueo tras intentos fallidos (15 minutos). Cada pedido autenticado renueva la sesión por el
tiempo configurado, y el aviso previo al vencimiento usa el mismo valor. El tope de 5 intentos
queda fijo, como lo escribe el contrato. Los cambios se auditan como el resto de los parámetros.

**Qué habría que cambiar.**
`ConfiguracionSistema`: los dos atributos, que la ficha de `CU-CFG-PAR` ya nombra.
