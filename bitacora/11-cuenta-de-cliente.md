# Bitácora — `11` Cuenta de Cliente

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-11-001 · La consulta de cuentas de Cliente se construyó declarándose fuera de todo caso de uso

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-CLI-CON`, `CU-CLI-BAJ`, `CO-194`, `CO-195`
**Estado:** Resuelta — comentario vencido; corregido el código el 2026-09-22

**Qué apareció.**
`ClienteListaView` lleva escrito en su docstring que no es un caso de uso, que es la contraparte de
lectura del registro público, y que dar de baja una cuenta de Cliente «es el `CU-CLI-BAJ`, que
todavía no está documentado». Las dos afirmaciones son falsas contra el esquema vigente:

- `CU-CLI-CON` · Consultar Cuentas de Cliente existe, con `CO-194 consultarCuentasDeCliente` y
  `CO-195 consultarFichaDeCliente`.
- `CU-CLI-BAJ` · Dar de Baja Cuenta existe, con ficha completa —mapeo de impacto sobre pedidos
  activos, stock almacenado y saldo de puntos, confirmación con contraseña, invalidación de
  sesiones— y con `CO-112` y `CO-113`.

La segunda afirmación es además la que más engaña: quien la lea va a creer que la baja de cuenta
está sin especificar y la va a resolver por su cuenta, cuando la ficha ya declara reglas que no se
adivinan.

**Qué dice la especificación.**
> `CU-CLI-BAJ` — «El sistema mapea el impacto sobre pedidos activos, stock almacenado y saldo de
> puntos, e informa al Cliente de las implicaciones antes de solicitar confirmación explícita con
> contraseña. Si existen condiciones bloqueantes no resueltas, el sistema las indica y no permite
> continuar hasta su resolución.»

**Qué se hizo.**
Nada sobre el comportamiento. La pantalla sigue siendo de sólo lectura, que es lo que corresponde:
la baja la pide el Cliente desde su panel, no el Administrador desde el listado, y el panel del
Cliente todavía no existe.

**Qué habría que cambiar.**
En el documento, nada. Hay que sacar del código la afirmación de que la baja no está documentada
—es la que puede inducir a implementarla mal— y verificar el listado contra `CO-194`. Queda
pendiente decidir si la ficha de cliente de `CO-195` se construye ahora o junto con el resto del
módulo: hoy no existe.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-11-001 · Resolución de B-11-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Como en `B-02-001` y `B-04-002`: **`CU-CLI-CON` y `CU-CLI-BAJ` se incorporaron al documento el
05/09**, después de que la pantalla existiera. Las dos afirmaciones del docstring fueron ciertas
cuando se escribieron.

La segunda —que la baja de cuenta «todavía no está documentada»— es la que había que sacar con
urgencia, porque induce a implementarla por las propias reglas en vez de por la ficha, que ya
declara el mapeo de impacto y la confirmación con contraseña.

**Qué se hizo.**
`ClienteListaView`: la referencia pasa a `CU-CLI-CON`, con `CO-194` y `CO-195`, y la nota sobre la
baja dice ahora lo que la ficha declara —la pide el Cliente desde su panel, que no existe— en vez
de decir que no está documentada. Queda dicho también que `CO-195` no está construido: hoy la
pantalla cubre el listado de `CO-194` y nada más.
