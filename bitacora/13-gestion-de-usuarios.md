# Bitácora — `13` Gestión de Usuarios

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-13-001 · Dos pantallas se construyeron como agregados y el esquema vigente las describe

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-USR-ELI`, `CU-USR-REA`, `CO-124`, `CO-125`
**Estado:** Resuelta — comentarios vencidos; corregido el código el 2026-09-22

**Qué apareció.**
`UsuarioEliminarPendienteView` y `UsuarioReactivarView` llevan escrito en su docstring que son
«Agregado al CU» y remiten a un documento que no existe en el repositorio:
`/docs/modulos/gestion_usuarios.md`. Esa ruta aparece citada en cuatro archivos del módulo y en
uno de proveedores (`/docs/modulos/proveedores.md`), y ninguno de los dos archivos está.

El esquema vigente describe las dos pantallas:

- `CU-USR-ELI` · Eliminar Cuenta Nunca Activada, con `CO-125 confirmarEliminacionDeCuentaPendiente`
  y `CO-200 solicitarEliminacionDeCuentaPendiente`.
- `CU-USR-REA` · Reactivar Cuenta de Usuario del Sistema, con `CO-124`, `CO-199` y `CO-122`.

**Qué dice la especificación.**
> `CU-USR-ELI` · Eliminar Cuenta Nunca Activada — 13 Gestión de Usuarios.
> `CU-USR-REA` · Reactivar Cuenta de Usuario del Sistema — 13 Gestión de Usuarios.

Las dos existen con ficha y contratos. Lo que ya no existe es la justificación que el código cita:
los archivos de `/docs/modulos/` desaparecieron en la reorganización de la documentación, y con
ellos el razonamiento de por qué cada agregado se tomó.

**Qué se hizo.**
Nada sobre el comportamiento. Se registra la pérdida de la referencia, que es lo que no se puede
reconstruir: si el documento de análisis absorbió esos agregados, el material que explicaba por
qué se habían tomado ya no está en ninguna parte del repositorio.

**Qué habría que cambiar.**
En el documento, probablemente nada. En el código, reemplazar las cinco citas a
`/docs/modulos/gestion_usuarios.md` por la referencia al caso de uso que hoy describe cada cosa. Y verificar lo construido contra los
contratos: `CU-USR-REA` referencia cuatro y `CU-USR-ELI` tres, y ninguno tiene prueba.

---

### B-13-002 · La reactivación no recibe el rol que el contrato le exige elegir

**Tipo:** Desvío · **Fecha:** 2026-09-14 · **Alcance:** `CU-USR-REA`, `CO-124`, `CO-199`
**Estado:** Resuelta — desvío confirmado; manda el contrato, construido el 2026-09-22

**Nota sobre el tipo.** Se registra después de tomado porque no se tomó como desvío: la vista es
anterior al contrato, y la divergencia apareció al escribir la prueba de `CO-124`.

**Qué apareció.**
`CO-124` declara la operación como `confirmarReactivacionDeUsuario(usuario, rol)`. La vista de
reactivación no recibe ningún rol: reactiva la cuenta conservando el que tenía antes de la baja.
La pantalla de confirmación muestra el rol como texto, sin control para cambiarlo.

Tres postcondiciones quedan incumplidas:

| Contrato | Lo declarado | Lo que hace el sistema |
| --- | --- | --- |
| `CO-124` | «u.rol quedó con el valor declarado» | Conserva el rol anterior |
| `CO-124` | La auditoría incluye «el rol asignado» | El detalle registra sólo la transición de estado |
| `CO-199` | «presentar el rol […] permitiendo modificarlo antes de confirmar» | Lo presenta, no deja modificarlo |

**Qué dice la especificación.**
> `CO-124`, Notas — «El rol se elige acá y queda registrado junto con la reactivación, en lugar de
> restaurarse el que tenía. Es lo que impide dejar preparado un cambio de rol sobre una cuenta
> dormida (ver CO-121).»

El contrato no sólo lo pide: explica para qué. `CO-121` prohíbe editar una cuenta Inactiva
justamente para que nadie deje un cambio de rol agazapado; elegir el rol en la reactivación es la
otra mitad de esa defensa, y hoy falta. Con lo construido, reincorporar a alguien devuelve
automáticamente los permisos que tenía cuando se fue, sin que nadie los vuelva a mirar.

**Qué se hizo.**
Nada sobre el comportamiento: cambiarlo es implementar una parte de `CU-USR-REA` que no está, y
eso se consulta antes. Las tres postcondiciones quedaron escritas como pruebas, marcadas
`xfail(strict=True)`. El `strict` es deliberado: el día que la reactivación acepte un rol, la
prueba deja de fallar y la suite avisa en vez de dejar un xfail viejo pasando desapercibido.

**Qué habría que cambiar.**
En el documento, nada: el contrato está bien y es el código el que se aparta. Lo que hace falta es
la decisión de construirlo. Es un formulario con un desplegable y un campo más en el detalle de
auditoría; el riesgo de dejarlo como está no es de tamaño sino de silencio.

---

### B-13-003 · La baja del último Administrador se ofrece y recién se rechaza al confirmar

**Tipo:** Desvío · **Fecha:** 2026-09-14 · **Alcance:** `CU-USR-BAJ`, `CO-198`, `CO-123`
**Estado:** Resuelta — desvío confirmado; manda el contrato, construido el 2026-09-22

**Qué apareció.**
`CO-198` declara como excepción E1 que la solicitud de baja sobre la única cuenta Administrador
activa se bloquea. El resguardo existe, pero vive sólo en el `POST`: la pantalla de confirmación se
sirve igual, con su texto normal, y el rechazo llega recién cuando el Administrador confirma.

**El sistema no queda expuesto.** `CO-123` E1 sí rechaza la baja, y su prueba pasa: la cuenta
permanece Activa. Lo que falla es que la operación se ofrece.

**Qué dice la especificación.**
> `CO-198`, Excepciones — «Última cuenta Administrador activa (E1): se bloquea (I-12).»

Y el principio general, enunciado en `CO-202`:

> «Presentar la acción de modificar sobre una cuenta inactiva, aunque el servidor luego la rechace,
> invita a intentar algo que el sistema no permite: la interfaz no decide, refleja.»

El documento enuncia la regla y el módulo la cumple en el otro caso —la edición de una cuenta
Inactiva sí se bloquea en el `GET`—, así que la asimetría es entre dos partes del mismo módulo.

**Qué se hizo.**
Nada. La prueba está escrita como el contrato la declara y marcada `xfail(strict=True)`.

**Qué habría que cambiar.**
En el documento, nada. En el código es la misma comprobación que ya existe en el `POST`, movida
también al `GET`. Se anota y no se corrige acá porque el trabajo del día era verificar, no
modificar.

---

### B-13-004 · Dos referencias de CO-125 y CO-124 no cierran

**Tipo:** Corrección · **Fecha:** 2026-09-14 · **Alcance:** `CO-124`, `CO-125`
**Estado:** Resuelta — corrección aceptada y ampliada el 2026-09-22

**Qué apareció.**
Dos detalles de redacción que aparecieron al transcribir los contratos a pruebas. Ninguno cambia
el comportamiento; los dos confunden a quien los lea para implementar.

**1. `CO-125` cita el invariante equivocado.** Su precondición dice:

> «La cuenta existe en estado Pendiente de activación y no registra ningún inicio de sesión
> (I-14).»

`I-14` en `MODELO_DE_DOMINIO.md` es «Existe exactamente una `ConfiguracionSistema`». No tiene
relación con inicios de sesión. La misma cita aparece repetida en las Notas del contrato. No hay
ningún invariante numerado que exprese «una cuenta pendiente que nunca inició sesión»: o falta, o
la cita sobra.

**2. `CO-124` declara una excepción que I-10 vuelve inalcanzable.** Su excepción E2 dice:

> «El correo de la cuenta colisiona con el de otra creada durante la inactividad (E2): se informa
> la colisión y no se reactiva.»

`I-10` dice que el correo identifica una sola cuenta **en cualquier estado**, y el sistema lo
sostiene con una restricción de unicidad en la base que no distingue estado. Mientras la cuenta
inactiva conserve su correo, ninguna otra puede haberse creado con él. La colisión que E2 describe
no puede ocurrir, así que no se pudo escribir prueba para esa excepción.

**Qué dice la especificación.**
Las dos citas de arriba, más `I-10` y `I-14` del modelo de dominio.

**Qué se hizo.**
Nada sobre el comportamiento. `CO-125` se probó contra su precondición real —la cuenta no registra
inicio de sesión—, que es lo que el código verifica y lo que las Notas del contrato explican bien.
De `CO-124` E2 no hay prueba.

**Qué habría que cambiar.**
`CO-125`, precondición y Notas: reemplazar la cita a `I-14` por el invariante correcto, o agregar
al modelo de dominio el que falta. `CO-124`, excepción E2: o se elimina, o se explica bajo qué
circunstancia `I-10` deja de bloquear el correo de una cuenta inactiva —si esa circunstancia
existe, es información que el modelo de dominio hoy no tiene.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-13-001 · Resolución de B-13-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Como en `B-02-001`, `B-04-002` y `B-11-001`: **`CU-USR-ELI` y `CU-USR-REA` se incorporaron al
documento el 05/09**, después de que las pantallas existieran.

Sobre los archivos de `/docs/modulos/` que el código citaba: **no se reponen.** El razonamiento
que contenían es el que el documento de análisis absorbió al incorporar los dos casos de uso; lo
que se perdió es la forma en que estaba escrito, no su contenido. Las citas se reemplazan por el
caso de uso que hoy describe cada cosa.

Con esto se cierra la decisión transversal «Referencias a documentación que ya no existe» de
`docs/DEUDA.md`.

**Qué se hizo.**
Las nueve citas del código quedaron reemplazadas:

| Cita vieja | Dónde | Por qué se reemplazó |
| --- | --- | --- |
| `/docs/modulos/gestion_usuarios.md` (5) | `accounts/views.py` (2), `accounts/forms.py`, `test_eliminar_pendiente.py`, `test_reactivacion_usuario.py` | `CU-USR-REA` y `CU-USR-ELI`, con sus contratos |
| `/docs/modulos/proveedores.md` (1) | `suppliers/extraccion.py` | `CU-PRV-ALT` y los campos del modelo |
| `/docs/diseno/sistema-visual.md` (3) | `templates/base.html`, `base_operativo.html`, `base_publico.html` | `.contexto-ia/TOKENS_VISUALES.md` |

---

### R-13-002 · Resolución de B-13-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna · **Tipo confirmado:** Desvío

**Qué se decidió.**
**Manda el contrato.** La reactivación recibe el rol —`CO-124 confirmarReactivacionDeUsuario(usuario, rol)`—
y la auditoría lo registra, y `CO-199` presenta el rol permitiendo modificarlo antes de confirmar.

El motivo que `CO-124` da en sus Notas es el que decide: `CO-121` prohíbe editar una cuenta
Inactiva justamente para que nadie deje un cambio de rol preparado sobre una cuenta dormida.
Elegir el rol en la reactivación es la otra mitad de esa defensa. Sin ella, reincorporar a alguien
le devuelve automáticamente los permisos que tenía cuando se fue, sin que nadie los vuelva a mirar.

**Qué se hizo.**
Construido. Las tres pruebas que estaban en `xfail(strict=True)` perdieron la marca y pasan.

---

### R-13-003 · Resolución de B-13-003

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna · **Tipo confirmado:** Desvío

**Qué se decidió.**
**Manda el contrato.** `CO-198` E1 bloquea la **solicitud** de baja sobre la única cuenta
Administrador activa, no sólo su confirmación. El principio que `CO-202` enuncia —«la interfaz no
decide, refleja»— vale para las dos mitades del par, y el módulo ya lo cumple en el otro caso.

**Qué se hizo.**
La comprobación que ya existía en el `POST` se aplica también en el `GET`. La prueba perdió el
`xfail` y pasa.

---

### R-13-004 · Resolución de B-13-004

**Fecha:** 2026-09-22 · **Enmienda al documento:** pendiente

**Qué se decidió.**
La corrección **se acepta y se amplía**. Los dos puntos de la entrada son ciertos, y el segundo
arrastra un tercero que la entrada no había visto: si la colisión de `CO-124` E2 no puede ocurrir,
entonces lo que hay que decir explícitamente es que el correo **no se libera nunca**, en ningún
estado. Eso es una precondición de `CO-120`, no una excepción de `CO-124`.

**Enmiendas pendientes.**

| Contrato | Qué cambia |
| --- | --- |
| `CO-120` | Precondición y excepción E2 pasan a «el correo no pertenece a ninguna cuenta, **en cualquier estado**» |
| `CO-124` | Pierde la precondición de colisión y la excepción E2: `I-10` las vuelve inalcanzables |
| `CO-125` | Pierde la cita a `I-14`, que es «existe exactamente una `ConfiguracionSistema`» y no tiene relación con inicios de sesión |

`CO-125` no queda sin invariante que citar: su precondición real —la cuenta no registra ningún
inicio de sesión— es una regla del caso de uso y no un invariante del modelo, y las Notas del
contrato ya la explican bien. No hace falta agregar un invariante nuevo.

**Qué se hizo.**
Se verificó que `CO-120` rechaza el correo de una cuenta **Inactiva**, que era el estado que
ninguna prueba miraba. No existía y se escribió:
`test_CO120_un_correo_de_cuenta_inactiva_no_crea_la_cuenta`. Pasa: la restricción de unicidad de
la base no distingue estado, así que la regla ya se sostenía; lo que faltaba era la prueba que lo
afirmara.

Las otras dos pruebas de E2 quedaron con su redacción alineada a la enmienda.
