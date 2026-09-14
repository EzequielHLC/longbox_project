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
**Estado:** Abierta

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
**Estado:** Abierta

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
