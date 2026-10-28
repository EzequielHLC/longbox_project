> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Tope de reservas, pantallas de error y capa de carga

**Estado del plan:** Aprobado el 2026-10-26, con las respuestas del responsable a las dos
preguntas de la sesión · **Fecha:** 2026-10-26

Tres arreglos pedidos por el responsable antes de seguir con lo pendiente. Ninguno agrega un caso
de uso; el primero **cambia lo que dice el documento** y queda como corrección en la bitácora.

---

## 1. Qué cubre

| # | Arreglo | Casos de uso | Contratos |
| --- | --- | --- | --- |
| A | **Tope de reservas de pre-venta por Cliente y producto** | `CU-TDA-CRA`, `CU-TDA-CRM`, `CU-TDA-CRC`, `CU-TDA-CMP`, `CU-CFG-PAR` | `CO-083`, `CO-084`, `CO-086`, `CO-178`, `CO-179`, `CO-180`, `CO-130` |
| B | **Pantallas de error propias** (400, 403, CSRF vencido, 404, 500) con el meme de `referencias-pantallas/Error_Screen.gif` | — | — |
| C | **La capa de carga**: que no quede pegada, y que también esté en la tienda | — | — |

### A · El tope

Hoy la especificación dice lo contrario: «la reserva no tiene tope, y las unidades que no cubra el
ingreso pasan a demora» (`CU-TDA-CRA` A1; `CO-083` y `CO-084`, notas). Un Cliente puede reservar
9999 unidades de un tomo. Decisión del responsable (2026-10-26):

- **Parámetro nuevo** en `ConfiguracionSistema`, «máximo de unidades por reserva», **5 por
  defecto**, en Parámetros globales → Compra online → Comercial.
- **Cuenta por Cliente y producto**: la línea del carrito **más** lo que ya tiene reservado de ese
  tomo en pedidos en curso (ni cancelados ni entregados). Así no se esquiva comprando de a cinco.
- **Se aplica en el servidor** en las tres puertas: al agregar (`CO-083`) y al cambiar la cantidad
  (`CO-084`) la línea queda en el máximo y se avisa, como hoy con el stock (E1); al fusionar el
  carrito del invitado (`CO-086`), también; y la consulta del carrito (`CO-178`) marca la línea que
  se pasa, de modo que proceder al pago (`CO-179`) y el checkout (`CO-180`) no avanzan. Lo último
  cubre la reserva hecha en otra pestaña mientras la línea esperaba en el carrito.
- Un invitado no compra pre-ventas (`CU-TDA-INV`): su tope cuenta sólo la línea.

### B · Pantallas de error

Hoy, con `DEBUG` apagado, un error muestra la página en blanco de Django («Server Error (500)»,
«Not Found»). Una sola plantilla base, **sin depender de la base de datos ni de la sesión**: la
del 500 se dibuja sin contexto de pedido, cuando algo ya falló. Cada página dice qué pasó en la
voz del sistema, ofrece volver, y muestra el meme convertido a un WebP animado liviano (el GIF
pesa 6,6 MB). La de CSRF vencido explica que el formulario venció y hay que volver a enviarlo.

### C · La capa de carga

- **Se queda pegada**: se activa con cualquier clic en un enlace interno, también con Ctrl, Cmd,
  Mayúsculas o la rueda (que abren otra pestaña), y con un enlace que descarga un archivo. En esos
  casos la pantalla queda tapada hasta recargar. Se filtran esos clics, se admite
  `data-sin-capa` en enlaces, y si a los 12 segundos la página sigue ahí, la capa se va sola.
- **Falta en la tienda**: pasa a un parcial compartido por el panel y la tienda. Aparece recién a
  los 300 ms: una navegación rápida no parpadea y la transición de vistas de la tienda no se
  pierde.
- **Tapa el error 500**: lo resuelve B; la capa se va con la página nueva.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `ConfiguracionSistema` | Sí | Gana el máximo de unidades por reserva |
| `LineaCarrito`, `LineaPedido` | Sí | Sólo se leen para contar lo reservado |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | Qué es «lo ya reservado» | Sólo el carrito / el carrito más los pedidos en curso | **Carrito más pedidos en curso**, decidido por el responsable |
| 2 | El tope al bajar el parámetro | Recortar los carritos que ya lo superan / marcarlos | **Marcarlos**: la consulta los muestra para ajustar y el pago no avanza. Nadie pierde una línea sin verla |

---

## 4. Orden de construcción

| # | Qué | Motivo |
| --- | --- | --- |
| 1 | A, con sus pruebas por contrato | Cambia un contrato y una migración |
| 2 | B | Independiente |
| 3 | C | Toca las bases de las dos superficies; se verifica con capturas |
| 4 | Cierre | Las siete puertas, `ESTADO.md`, `COBERTURA.md`, bitácoras 07 y 00 |

---

## 5. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Pruebas que reservan más de 5 unidades de una pre-venta | Se ajustan; las que prueban el «sin tope por stock» siguen valiendo con el tope del parámetro |
| La página 500 falla al dibujarse | Plantilla sin consultas ni sesión; prueba que fuerza un 500 por la dirección real |
| La capa tapa la transición de vistas | Aparece a los 300 ms; captura en la tienda |

---

## 6. Fuera de alcance

- Un cupo total de reservas por producto (la tercera opción que no se eligió).
- El indicador de carga dentro de las acciones con guion (el carrito lateral, los diálogos): ya
  tienen el suyo.
