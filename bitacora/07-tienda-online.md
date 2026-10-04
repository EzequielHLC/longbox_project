# Bitácora — `07` Tienda Online

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-07-001 · El catálogo público excluye los productos para adultos

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-TDA-CAT`, `CO-176`, `CO-177`
**Estado:** Abierta — plan 07, ambigüedad 2

**Qué apareció.**
`Producto` tiene «solo para adultos» y ningún caso de uso dice qué ve de ellos el catálogo
público. No hay verificación de edad.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
No aparecen en el catálogo ni en su ficha pública, para nadie: la ficha responde como si no
existieran.

**Qué habría que cambiar.**
`CU-TDA-CAT`, Comentarios: decir qué ve el catálogo de un producto para adultos.

---

### B-07-002 · Las acciones de la ficha pública se muestran deshabilitadas

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-177`, `CU-TDA-CRA`, `CU-RST-SUS`
**Estado:** Abierta — hasta que existan el carrito y las suscripciones

**Qué apareció.**
«Agregar al carrito», «Avisarme cuando haya stock» y «Reservar» inician casos de uso que no están
construidos.

**Qué dice la especificación.**
> «Presentar la ficha con la acción según estado» (`CO-177`, Responsabilidades)

**Qué se hizo.**
La ficha presenta la acción que corresponde a su estado, deshabilitada y con la línea «Disponible
próximamente». Un producto Activo sin stock y uno en estado Agotado se presentan los dos como
«Sin stock». El catálogo es público, como dice la precondición de `CO-176`; la portada sigue siendo
de la cuenta de cliente hasta que se responda C-20.

**Qué habría que cambiar.**
Nada.

---

### R-07-001 · Resolución parcial de B-07-002

**Fecha:** 2026-10-03 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Con el carrito construido, «Agregar al carrito» y «Reservar» dejan de estar deshabilitados.

**Qué se hizo.**
Los dos botones de la ficha inician `CU-TDA-CRA` (`CO-083`), con la cantidad al lado. «Avisarme
cuando haya stock» sigue deshabilitado hasta que exista `CU-RST-SUS`: B-07-002 queda abierta sólo
por esa acción.

---

### B-07-003 · La línea de carrito guarda dos importes

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `LineaCarrito`, `CO-083`, `CO-084`,
`CO-178`, `CO-048`, `CO-053`
**Estado:** Abierta — decidido por el responsable el 2026-10-03 (plan 07, segunda parte, ambigüedad 1)

**Qué apareció.**
`CO-048`, `CO-053` y los contratos de oferta terminan en «las `LineaCarrito` afectadas quedaron
actualizadas». `CU-TDA-CRC` A2 pide avisar «El precio de este producto ha cambiado» cuando el precio
cambió desde que se agregó. Si la propagación pisa el único importe de la línea, la consulta ya no
tiene contra qué comparar y el aviso no aparece nunca.

**Qué dice la especificación.**
> «precio vigente : importe «al momento de la última consulta»» (`MODELO_DE_DOMINIO.md`, `LineaCarrito`)

**Qué se hizo.**
La línea guarda el **precio vigente**, que la propagación actualiza, y el **precio visto**, el que el
Cliente tenía a la vista la última vez que agregó o cambió la cantidad. La consulta muestra el precio
visible de hoy y avisa cuando no es el visto, con el importe anterior al lado. Cambiar la cantidad
apaga el aviso. La consulta no escribe nada, como dice `CU-TDA-CRC`.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, `LineaCarrito`: agregar «precio visto : importe» y corregir la nota de
«precio vigente», que hoy dice «al momento de la última consulta» y la consulta no modifica nada.

---

### B-07-004 · La disponibilidad de la línea se deriva y tiene tres valores

**Tipo:** Corrección · **Fecha:** 2026-10-03 · **Alcance:** `LineaCarrito`, `CO-178`
**Estado:** Abierta — plan 07, segunda parte, ambigüedad 2

**Qué apareció.**
El modelo declara la disponibilidad como atributo de la línea con dos valores. `CO-178` la deriva del
producto con tres.

**Qué dice la especificación.**
> «disponibilidad : {Disponible, Producto no disponible}» (`MODELO_DE_DOMINIO.md`, `LineaCarrito`)

> «La disponibilidad de cada línea se deriva del producto: «Producto no disponible» si está
> Descatalogado, Cancelado por editorial o Agotado; «Stock insuficiente», con la cantidad máxima, si
> está Activo con menos stock que la cantidad de la línea; «Disponible» en los demás casos» (`CO-178`, Notas)

**Qué se hizo.**
Se deriva en cada consulta, con los tres valores, y no se guarda. Un producto Activo con stock cero
se lee como «Producto no disponible», igual que en el catálogo público (plan 07, ambigüedad 4):
ofrecer «reducí la cantidad a cero» no resuelve nada.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, `LineaCarrito`: quitar el atributo o marcarlo «derivado», con los tres
valores. `CO-178`, Notas: nombrar el caso del Activo con stock cero.

---

### B-07-005 · Quién tiene carrito y cuánto dura el del invitado

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CU-TDA-CRC`, `CRA`, `CRM`, `CRB`, `CO-086`
**Estado:** Abierta — plan 07, segunda parte, ambigüedades 3 y 4

**Qué apareció.**
Los casos de uso del carrito nombran al Cliente y al invitado. No dicen qué pasa con el personal que
entra a la tienda con su cuenta. Del invitado dicen que su carrito «se destruye al cerrar el
navegador», y la sesión del sistema ya vence a los 30 minutos sin actividad.

**Qué dice la especificación.**
> «El de un invitado es de sesión y se destruye al cerrar el navegador» (`CU-TDA-CRC`, Comentarios)

Sobre el personal: `Nada.`

**Qué se hizo.**
- **El personal no tiene carrito.** Cualquier dirección del carrito le responde 403, y la ficha le
  dice «La compra es para cuentas de cliente». Si inicia sesión con un carrito de invitado armado,
  ese carrito se descarta.
- **El carrito de invitado vive lo que vive su sesión:** se pierde al cerrar el navegador o tras 30
  minutos sin actividad. No se abrió una segunda política de sesión.
- **Fusión con un producto sin stock.** `CO-086` suma con tope en el stock. Si el producto ya no
  tiene stock, la línea conserva la suma y la consulta la marca no disponible: el Cliente decide.

**Qué habría que cambiar.**
`CU-TDA-CRC`, Comentarios: «el carrito de invitado vence con su sesión» y «el personal no tiene
carrito». `CO-086`, Notas: el caso del producto sin stock.

---

### B-07-006 · El carrito quedó construido; el pago espera a `CU-TDA-CMP`

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CU-TDA-CRC`, `CO-179`
**Estado:** Abierta — hasta que exista `CU-TDA-CMP`

**Qué apareció.**
`CU-TDA-CRC` paso 3 ofrece avanzar al pago, que inicia `CU-TDA-CMP`.

**Qué dice la especificación.**
> «Desde el carrito, el Cliente puede iniciar CU-TDA-CRM o CU-TDA-CRB, o avanzar al pago» (`CU-TDA-CRC`, paso 3)

**Qué se hizo.**
«Ir a pagar» se muestra deshabilitado. Debajo dice que el pago estará disponible próximamente, o,
si hay líneas marcadas, qué hay que resolver antes: la condición de `CO-179` ya se calcula. El
encabezado de la tienda muestra «Carrito» con las unidades que lleva.

**Qué habría que cambiar.**
Nada.

---

### Nota de cierre de tanda · 2026-10-03

El carrito quedó construido y verificado (`CU-TDA-CRC`, `CRA`, `CRM`, `CRB`), y las ofertas del
módulo 03 ya se ven en la tienda y en el carrito. Lo que sigue en este módulo es la compra
(`CU-TDA-CMP`, `CU-TDA-INV`, `CO-179`), que necesita `Pedido` y `TransaccionPago`: es la
dependencia raíz de `docs/DEUDA.md`. «Ir a pagar» espera deshabilitado (B-07-006).

---

### B-07-007 · El catálogo público hacía una consulta por cada artículo no editorial

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** `CO-176`, RNF-02
**Estado:** Resuelta — corregido el código el 2026-10-04, encontrado en el ensayo de la demostración (plan 00, D5-04)

**Qué apareció.**
La prueba de volumen cuenta las consultas de una página con pocos productos y de una página llena.
El catálogo público pasaba de 8 a 15: la tarjeta lee la marca de cada artículo no editorial, y esa
tabla no venía en la consulta de la página, así que cada uno costaba una consulta más (el problema
N+1). Con 20 000 productos la página seguía siendo de 24, pero hasta 24 consultas extra por página.

**Qué dice la especificación.**
> «Operaciones interactivas en 2 segundos como máximo» (RNF-02)

**Qué se hizo.**
La consulta de los productos visibles trae las dos especializaciones juntas. La prueba
(`test_volumen_consultas.py`, que cubre también los siete listados del mostrador) se escribió antes
y fallaba.

**Qué habría que cambiar.**
Nada en el documento.

---

### B-07-008 · Flechas de cantidad y el ícono de pausa del carrusel

**Tipo:** Agregado · **Fecha:** 2026-10-04 · **Alcance:** `CU-TDA-CRA`, `CU-TDA-CRM`, la portada
**Estado:** Abierta — pedido explícito del responsable el 2026-10-03

**Qué apareció.**
El responsable pidió flechas para subir y bajar la cantidad en la ficha y en el carrito, y que el
botón «Pausar» del carrusel cambie también de ícono cuando pasa a «Reanudar».

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
- La cantidad lleva botones − y + a los lados. No bajan de 1 ni pasan del stock de un producto
  Activo. Sin JavaScript los botones no aparecen y el número se escribe a mano. El servidor valida
  la cantidad igual (`CO-083`, `CO-084`): las flechas son comodidad, no el control.
- El botón del carrusel muestra el ícono de pausa mientras pasa solo y el de reproducir cuando
  está pausado, igual que su texto.

**Qué habría que cambiar.**
Nada en el documento.

---

### B-07-009 · Filas de productos en la portada, por etiqueta o por grupo de etiquetas

**Tipo:** Agregado · **Fecha:** 2026-10-04 · **Alcance:** la portada de la tienda, `CO-176`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-04; falta decidir si lleva caso de uso propio

**Qué apareció.**
El responsable pidió que la portada muestre grupos del catálogo como barras que se recorren de
costado, armadas por etiqueta («Shonen») o por grupo de etiquetas entero («Demografía»), para ir
mostrándole al cliente lo que hay.

**Qué dice la especificación.**
`Nada.` Ningún caso de uso describe la portada más allá del carrusel de banners (`CU-CFG-BNC`).

**Qué se hizo.**
- El Administrador configura las filas desde «Tienda → Filas de la portada»: para cada una elige
  una etiqueta o un grupo, un título opcional (si falta, el nombre de la etiqueta o del grupo), el
  orden y si está activa. Se guardan todas juntas y el cambio queda en la auditoría como
  «Modificación de las filas de la portada», con la lista de antes y la de después.
- Cada fila muestra hasta 12 productos, de lo más nuevo a lo más viejo, y sólo los que el catálogo
  público mostraría (`CO-176`): nada descatalogado ni, para quien no está habilitado, sólo para
  adultos. Una fila sin productos, inactiva, o cuya etiqueta o grupo está dado de baja, no se
  dibuja.
- «Ver todo» lleva al catálogo filtrado por esa etiqueta o, para un grupo, por el grupo: el
  catálogo público suma ese filtro.
- La portada sigue siendo sólo de la cuenta de cliente.

**Qué habría que cambiar.**
- `MODELO_DE_DOMINIO`: el concepto **FilaPortada** (etiqueta **o** grupo, título, orden, activa).
- Un caso de uso de configuración para administrarlas, con el código que el responsable asigne,
  junto a los de banners en el módulo 17.
- `CO-176` no cambia: la fila reusa su consulta. Sí suma el filtro por grupo de etiquetas al
  catálogo público, que el contrato hoy no enumera.
