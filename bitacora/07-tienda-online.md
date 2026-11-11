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
**Estado:** Resuelta — el 2026-10-09 existe `CU-TDA-CMP` y «Ir a pagar» lleva al checkout (plan 07, sexta parte)

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
**Estado:** Abierta — pedido explícito del responsable el 2026-10-04. El caso de uso quedó decidido el 2026-11-11: `CU-CFG-SEC` (B-07-046)

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

---

### B-07-010 · El gestor de filas por tarjetas que se reordenan, y una imagen por fila

**Tipo:** Agregado · **Fecha:** 2026-10-04 · **Alcance:** las filas de la portada (B-07-009)
**Estado:** Abierta — pedido explícito del responsable el 2026-10-04

**Qué apareció.**
El responsable pidió administrar las filas «por tarjetas, así como en las cargas de catálogo, pero
deslizables/acomodables», y poder poner una imagen en el título de cada fila de la portada.

**Qué dice la especificación.**
`Nada.` Las filas no tienen caso de uso (B-07-009).

**Qué se hizo.**
- Cada fila es una tarjeta, como los ítems de la carga de lotes. El orden se cambia arrastrando
  la tarjeta por su asa, o con «Subir» y «Bajar», que funcionan con teclado y lector de pantalla y
  anuncian el lugar nuevo. Nada se guarda al soltar: el orden queda al apretar «Guardar las
  filas», junto con el resto de los cambios.
- «Agregar fila» suma una tarjeta vacía. Una fila marcada para quitar queda tachada hasta guardar.
- Cada fila puede llevar una imagen. Se procesa como toda imagen del sistema (RNF-05) y en la
  portada abre la fila en una tarjeta titular que lleva a «Ver todo». Sin imagen, la tarjeta
  titular muestra en abanico las primeras portadas de la fila.
- Cambiar sólo la imagen de una fila también queda en la auditoría.

**Qué habría que cambiar.**
- `MODELO_DE_DOMINIO`, en **FilaPortada** (B-07-009): el atributo imagen, opcional.
- `identidad_visual.md`: el patrón de arrastrar y soltar, que la guía manda consultar (ver
  B-00-010).

---

### B-07-011 · El encabezado de la tienda acompaña al bajar, con búsqueda y menú de cuenta

**Tipo:** Desvío · **Fecha:** 2026-10-04 · **Alcance:** la cáscara pública
**Estado:** Abierta — consultado: es el pedido explícito del responsable del 2026-10-04

**Qué apareció.**
El responsable pidió «un header que se mueve contigo al bajar de los banners con su barra de
búsqueda y acceso al perfil personal».

**Qué dice la especificación.**
> «Al desplazar hacia abajo el encabezado se esconde (`translateY(-100%)`, `--dur-3`); al subir,
> vuelve.» (`identidad_visual.md`, Modo público · Encabezado)

**Qué se hizo.**
- El encabezado queda fijo arriba todo el tiempo. Pasada la portada se vuelve más bajo y marca su
  borde con una sombra dura; el cambio es de golpe, sin animar el alto.
- Suma la búsqueda del catálogo (título, autor o editorial), que lleva al catálogo con todos los
  estados.
- «Mi cuenta» abre un menú con el correo, el carrito, las preguntas frecuentes y «Cerrar sesión».
  Es un control nativo: funciona sin JavaScript, se cierra con Escape o con un clic afuera. No hay
  panel del Cliente todavía (`CU-CLI-DAT` pendiente): el menú reúne lo que la cuenta ya puede
  hacer.

**Qué habría que cambiar.**
`identidad_visual.md`, Encabezado: reemplazar «se esconde al bajar» por «queda fijo y se compacta
pasada la portada», y sumar la búsqueda y el menú de cuenta.

---

### B-07-012 · Cinta de accesos, globo de preguntas frecuentes y un pie completo

**Tipo:** Agregado · **Fecha:** 2026-10-04 · **Alcance:** la cáscara pública
**Estado:** Abierta — pedido explícito del responsable el 2026-10-04

**Qué apareció.**
El responsable pidió, debajo del encabezado, «la cinta para acceder a los distintos filtros»; que
el botón de preguntas frecuentes sea «más bonito, como un estilo burbuja de chat» y esté más abajo;
y un pie mejor.

**Qué dice la especificación.**
`Nada` sobre la cinta de accesos. Sobre el resto:

> «Citas, reseñas y FAQ: dentro de globos de diálogo cuadrados (borde `--trazo-fuerte`, un
> triángulo de cola hecho con `clip-path`).» · «Pie: Superficie noche con una franja de `--cinta`
> arriba. Datos de contacto, redes con íconos de trazo, horarios en `--fuente-datos`.»
> (`identidad_visual.md`)

**Qué se hizo.**
- **Cinta de accesos**, en todas las pantallas de la tienda: «Novedades», «Pre-ventas» y una
  entrada por cada fila activa de la portada, que lleva al catálogo con el mismo filtro que su
  «Ver todo». La entrada en la que se está queda marcada con fondo, borde y peso, no sólo con
  color. Quien administra las filas administra la cinta.
- **Globo de preguntas frecuentes**: un globo de diálogo cuadrado de papel con su cola, fijo abajo
  a la derecha, junto a un bloque con el ícono. Sale del menú y de la estantería. No aparece en la
  propia página de preguntas ni si no hay nada publicado. En el teléfono queda sólo el ícono.
- **Pie**: la marca en grande con la descripción de la tienda; «Tienda» con el catálogo y los
  accesos; «Ayuda»; «Contacto» con el correo, el teléfono y las redes con íconos de trazo; y una
  base con el año y «Volver arriba». Los horarios no están porque la identidad visual no los
  guarda.

**Qué habría que cambiar.**
- `identidad_visual.md`: describir la cinta de accesos y el globo fijo de preguntas.
- Si el pie tiene que mostrar horarios, `CU-CFG-VIS` necesita un campo para cargarlos.

---

### B-07-013 · El catálogo filtra desde un panel lateral, con varios valores y mientras se cambia

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-TDA-CAT`, `CO-176`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El responsable pidió que los filtros se apliquen «a tiempo real», en una barra al costado con
interruptores, con sólo la búsqueda arriba. El botón «Limpiar filtros» aparecía al lado de
«Filtrar» recién después de filtrar, y lo corría de lugar.

**Qué dice la especificación.**
> «El Cliente aplica uno o más filtros disponibles: búsqueda por texto libre (título, autor o
> editorial), tipo de material, franquicia, editorial, rango de precio y estado del producto.» ·
> «El sistema actualiza el listado con los filtros aplicados y muestra el total de resultados
> encontrados.» (`CU-TDA-CAT`, pasos 3 y 4)

**Qué se hizo.**
- Arriba, sólo la búsqueda. Los filtros van en un panel al costado; en el teléfono, plegado
  detrás de «Filtros».
- Tipo, editorial, etiqueta y estado son interruptores y admiten **varios valores**. Dos etiquetas
  del mismo grupo suman («Shonen» o «Seinen»); de grupos distintos restringen («Seinen» y
  «Acción»). El panel sólo ofrece opciones que tienen algún producto visible.
- Se aplican al cambiar: los interruptores al instante, la búsqueda y el precio al dejar de
  escribir. Cambian sólo los resultados y la dirección, así «volver» desde la ficha conserva los
  filtros (paso 7). Sin guion, el panel muestra «Aplicar filtros».
- Se puede ordenar por lo más nuevo (lo de siempre), por próximos a llegar o por título.
- «Limpiar» queda fijo en la cabecera del panel: aparece y desaparece sin mover nada.

**Qué habría que cambiar.**
`CU-TDA-CAT`, paso 3: decir que un filtro admite varios valores y cómo se combinan. `CO-176`:
sumar el orden elegido (hoy el contrato fija la fecha de alta descendente; queda como orden por
defecto).

---

### B-07-014 · Agregar al carrito desde la tarjeta

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-TDA-CRA`, `CO-083`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El responsable pidió agregar al carrito desde la tarjeta del catálogo y de la portada, sin abrir
la ficha.

**Qué dice la especificación.**
> «Desde la ficha del producto (CU-TDA-CAT), el Cliente selecciona «Agregar al carrito» o, si el
> producto está en Pre-venta, «Reservar».» (`CU-TDA-CRA`, paso 1)

**Qué se hizo.**
- Cada tarjeta lleva un botón que agrega **una** unidad (o la reserva, en pre-venta). Es la misma
  operación de la ficha, con las mismas validaciones en el servidor: el tope de stock se avisa
  igual que desde la ficha.
- Con guion, no se cambia de pantalla: aparece un aviso y el contador del encabezado se actualiza.
  Sin guion, el formulario se envía y vuelve a la pantalla de origen con el mismo mensaje.
- Lo ven el invitado y el cliente. El personal no (no tiene carrito) y un producto sin stock
  tampoco.

**Qué habría que cambiar.**
`CU-TDA-CRA`, paso 1: sumar la tarjeta del catálogo como otro punto de partida, con cantidad 1.

---

### B-07-015 · «Lo que se viene»: las pre-ventas, la más próxima primero

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la portada de la tienda
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El responsable pidió mostrar en la portada «Lo que se viene»: las pre-ventas ordenadas por fecha
de llegada.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
- Una fila más de la portada, antes de las que arma el Administrador, con las pre-ventas
  ordenadas por la fecha en que hoy se espera cada una: la estimada si la hay, si no la
  programada. Las que no tienen fecha van al final.
- Cada tarjeta de pre-venta dice «Llega el» con el día y el mes.
- «Ver todo» lleva al catálogo de pre-ventas ordenado por llegada.
- Sin pre-ventas, la fila no aparece.

**Qué habría que cambiar.**
Si se le da caso de uso a la portada (B-07-009), que la incluya.

---

### B-07-016 · Correcciones gráficas de la tienda

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la cáscara pública y la portada
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El responsable marcó para corregir el botón de preguntas frecuentes, la barra de búsqueda, las
flechas de las filas y una doble barra de desplazamiento.

**Qué dice la especificación.**
`Nada` más que lo citado en B-07-012.

**Qué se hizo.**
- **Preguntas frecuentes:** el globo quedó más chico, a la izquierda del ícono y con la cola hacia
  él. Pasada la portada se pliega y queda el ícono; vuelve al pasar el puntero.
- **Búsqueda:** el campo heredaba el recuadro de los campos comunes y se dibujaba un cuadro dentro
  del marco. Ahora el marco sesgado es el único borde.
- **Flechas de las filas:** pestañas sesgadas sobre los bordes de la pista, a la altura de las
  portadas. Sólo aparecen si la fila no entra entera y se esconden en cada extremo.
- **Doble barra:** cada fila mostraba la barra del navegador y, debajo, la de recorrido. Ahora queda
  una sola, la de recorrido. Sin guion vuelve la del navegador.

**Qué habría que cambiar.**
`identidad_visual.md`, Modo público: describir el globo plegable y las flechas de las filas.

---

### B-07-017 · Carteles «¡TOMO 1!» y «¡ÚLTIMO TOMO!»

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la tarjeta de producto
**Estado:** Resuelta el 2026-10-05 — el responsable cambió el cartel por «¡NOVEDAD!» (B-07-024)

**Qué apareció.**
El responsable pidió carteles de historieta «¡TOMO 1!» y «¡ÚLTIMO TOMO!» en las tarjetas. «Último
tomo» puede ser el más reciente que salió o el tomo final de una serie terminada, y el modelo no
sabe si una serie terminó.

**Qué dice la especificación.**
`Nada.` El modelo de dominio no tiene ningún dato de serie completa. La regla 3 del proyecto
impide sacarlo de una etiqueta («lo que cambia el comportamiento del sistema es campo»).

**Qué se hizo.**
- «¡TOMO 1!» en el tomo 1 de una serie con más de un tomo.
- «¡ÚLTIMO TOMO!» en el tomo de número más alto **ya a la venta**: el último que salió. Las
  pre-ventas no lo llevan, porque ya tienen su rótulo.
- Una serie de un solo tomo no lleva cartel.

**Qué habría que cambiar.**
Si «último» tiene que ser el tomo final, hace falta un dato en el modelo (por ejemplo, la cantidad
de tomos de la serie o una marca de serie terminada) y su caso de uso de carga. Mientras tanto,
se queda como «el último que salió».

---

### B-07-018 · Las pantallas de acceso, partidas en diagonal

**Tipo:** Corrección · **Fecha:** 2026-10-05 · **Alcance:** `CU-AUT-INI`, `CU-CLI-ALT`, recuperación de contraseña
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
Con el encabezado nuevo, la pantalla de ingreso heredaba la búsqueda, la cinta de accesos y el
globo de preguntas, y el formulario iba en una columna suelta. La guía pide otra composición.

**Qué dice la especificación.**
> «Pantalla partida en diagonal: a la izquierda, noche con una portada grande y `--trama-puntos`;
> a la derecha, papel con el formulario. En móvil, sólo el formulario con una franja de `--cinta`
> arriba.» (`identidad_visual.md`, Registro e inicio de sesión)

**Qué se hizo.**
Ingreso, registro y las cuatro pantallas de recuperación usan esa composición. La portada es la
del producto más nuevo con imagen; en el registro, que es largo, acompaña al bajar. Sin búsqueda,
cinta ni globo.

**Qué habría que cambiar.**
Nada en el documento: la corrección es del código, que no seguía la guía.

---

### B-07-019 · La portada de la tienda es pública

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la portada de la tienda
**Estado:** Resuelta — responde C-20

**Qué apareció.**
C-20 preguntaba si la portada se tiene que ver sin iniciar sesión. El responsable respondió: «Un
invitado debería poder ver la pantalla de inicio de la tienda».

**Qué dice la especificación.**
`Nada` sobre la portada. El catálogo y la ficha ya eran públicos (`CO-176`, `CO-177`).

**Qué se hizo.**
La portada la ve cualquiera, con sesión o sin ella, y la raíz del sitio lleva a ella (antes llevaba
al ingreso). Las pruebas de sesión que usaban la portada como dirección protegida pasaron a otra
que sí exige sesión.

**Qué habría que cambiar.**
Nada, salvo incluirla si la portada recibe caso de uso (B-07-009).

---

### B-07-020 · Las pantallas de acceso muestran una imagen configurable o el logo

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-CFG-VIS`, `CO-131`, las pantallas de acceso
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
La escena de las pantallas de acceso (B-07-018) mostraba la portada del producto más nuevo. El
responsable pidió «una imagen personalizable (en la configuración de la tienda) o bien, el Logo de
la tienda».

**Qué dice la especificación.**
> «a la izquierda, noche con una portada grande y `--trama-puntos`» (`identidad_visual.md`, Registro
> e inicio de sesión)

`CU-CFG-VIS` no prevé una imagen para el ingreso.

**Qué se hizo.**
- La identidad visual suma **«Imagen del ingreso»**, opcional. Se procesa como el resto de las
  imágenes (RNF-05) y su carga o reemplazo queda en la auditoría de `CO-131`, igual que el logo y el
  fondo.
- La escena muestra esa imagen a todo el alto, con sus colores. Sin ella, el logo sobre la trama.
  Sin logo, el nombre de la tienda en grande con el cartel «¡BIENVENIDO!». Nunca la portada de un
  producto.

**Qué habría que cambiar.**
- `CU-CFG-VIS` y `CO-131`: sumar el atributo «imagen del ingreso».
- `identidad_visual.md`, Registro e inicio de sesión: cambiar «una portada grande» por «la imagen
  del ingreso, o el logo».

---

### B-07-021 · Se quita la cinta de accesos

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la cáscara pública
**Estado:** Resuelta — reemplaza la parte de la cinta de B-07-012

**Qué apareció.**
El responsable pidió quitar la cinta de accesos de debajo del encabezado: «no tiene sentido
teniendo el catálogo a mano».

**Qué dice la especificación.**
`Nada.` La cinta era un agregado (B-07-012).

**Qué se hizo.**
Se quitó del encabezado y de la pantalla de filas. Los mismos accesos (novedades, pre-ventas y las
filas activas) siguen en el pie, en la columna «Tienda».

**Qué habría que cambiar.**
Nada.

---

### B-07-022 · La búsqueda sin recuadro de foco, «Buscar» con relieve y flechas sin la franja

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la cáscara pública y la portada
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
Al tomar foco, la búsqueda del encabezado y la del catálogo quedaban rodeadas por un recuadro
naranja además de su marco. Las flechas de las filas tenían una franja de cinta abajo que cambiaba
al pasar el puntero y se veía mal.

**Qué dice la especificación.**
> «Foco: Contorno `2px` `--foco` con `outline-offset: 2px`. Siempre visible con teclado»
> (`TOKENS_VISUALES.md`, Estados de un control)

**Qué se hizo.**
- El foco de la búsqueda lo marca el marco mismo: pasa al acento y se engrosa. Sigue visible con
  teclado, y no por el color solo: cambia el grosor.
- «Buscar» tiene el relieve del botón de preguntas frecuentes: borde oscuro, y al pasar el puntero
  sube con una sombra dura.
- Las flechas de las filas perdieron la franja de cinta.

**Qué habría que cambiar.**
`TOKENS_VISUALES.md`, Estados de un control: admitir que un campo con marco propio muestre el foco
en ese marco, más grueso, en lugar del contorno.

---

### B-07-023 · El ticker nombra cada serie una vez

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la portada de la tienda
**Estado:** Resuelta

**Qué apareció.**
Sin mensajes cargados, el ticker de la portada dice «Llegó» con lo recién llegado. Si llegaban dos
tomos de la misma serie, la serie salía dos veces.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Cada serie aparece una sola vez, en el orden de llegada.

**Qué habría que cambiar.**
Nada.

---

### B-07-024 · «¡NOVEDAD!» en lugar de «¡ÚLTIMO TOMO!»

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la tarjeta de producto
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05; resuelve la consulta de B-07-017

**Qué apareció.**
El responsable eligió cambiar «¡ÚLTIMO TOMO!» por «Lo último» o «Novedad»: «queda redundante con
las novedades, pero es mejor y trabaja menos datos».

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
- «¡NOVEDAD!» en lo que se dio de alta en los últimos **30 días** y ya está a la venta. Las
  pre-ventas no lo llevan: tienen su rótulo.
- «¡TOMO 1!» sigue igual y gana si un tomo 1 también es novedad.
- La serie ya no se recorre para buscar su tomo más alto: sólo se consulta, en una consulta por
  estantería, si los tomos 1 de la pantalla tienen más tomos.

**Qué habría que cambiar.**
Si se quiere configurar cuántos días dura una novedad, un parámetro en `CU-CFG-PAR`.

---

### B-07-025 · El logo y la imagen del ingreso se pueden quitar

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-CFG-VIS`, `CO-131`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
Una vez cargados, el logo y la imagen del ingreso no se podían sacar: sólo reemplazar.

**Qué dice la especificación.**
`Nada` sobre quitar una imagen de la identidad.

**Qué se hizo.**
- «Quitar el logo» y «Quitar la imagen del ingreso», cada una junto a su imagen. Quitar borra el
  archivo y queda en la auditoría de `CO-131` («logo quitado»).
- Cada imagen se ve en la pantalla con su vista: la cargada o, sin ella, la **predeterminada**,
  dibujada como la tarjeta «Ver todo» de las filas: el nombre de la tienda sobre la trama y el
  rótulo «Predeterminado». Para el ingreso, la predeterminada es el logo si lo hay.

**Qué habría que cambiar.**
`CO-131`: sumar quitar el logo y la imagen del ingreso a sus postcondiciones.

---

### B-07-026 · Encabezado a todo el ancho, «Buscar» dentro de la barra y el botón de la tarjeta en su base

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la cáscara pública y la tarjeta de producto
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05; reemplaza el relieve de «Buscar» de B-07-022

**Qué apareció.**
En una pantalla ultra ancha, la marca, la búsqueda y el menú quedaban encerrados en la columna de
contenido. El borde de «Buscar» no coincidía con el de la barra, y su borde naranja se confundía
con el relleno. En la tarjeta, el precio quedaba pegado al botón de agregar.

**Qué dice la especificación.**
> «Contenido hasta `--ancho-escaparate`» (`TOKENS_VISUALES.md`, Los dos modos)

**Qué se hizo.**
- El encabezado ocupa todo el ancho: la marca al borde izquierdo, el menú al derecho y la búsqueda
  en el medio, hasta 640 px. El contenido de las secciones sigue en la columna.
- «Buscar» va dentro del marco de la barra y comparte sus bordes: el mismo alto, el mismo sesgo y
  el mismo color de borde. Relleno noche y letras de acento; al puntero se llena de acento.
- En la tarjeta, el precio va arriba y el botón ocupa la base, a lo ancho, con su palabra:
  «Agregar» o «Reservar».

**Qué habría que cambiar.**
`identidad_visual.md`, Encabezado: el encabezado público no se limita a `--ancho-escaparate`.

---

### B-07-027 · El menú de la tienda, todo texto

**Tipo:** Corrección · **Fecha:** 2026-10-05 · **Alcance:** la cáscara pública
**Estado:** Resuelta · reemplazada el 2026-11-11 por B-07-048 (botonera de íconos)

**Qué apareció.**
El responsable preguntó por qué «Carrito» era el único enlace del menú con ícono. El ícono lo
agregó el encabezado nuevo (B-07-011) contra la regla del propio sistema.

**Qué dice la especificación.**
> «Menú en `--pub-rotulo`» (`identidad_visual.md`, Encabezado). La hoja lo dice así: «Los enlaces
> del menú público: rótulos, sin íconos».

**Qué se hizo.**
«Carrito» quedó como los demás: texto, con su contador en el rombo de acento.

**Qué habría que cambiar.**
Nada en el documento: el error era del código.

---

### B-07-028 · El carrito se actualiza solo al cambiar una cantidad

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-TDA-CRM`, `CU-TDA-CRB`, `CO-084`, `CO-085`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El responsable pidió que el carrito actualice el precio solo al cambiar las cantidades, verificando
el stock, en lugar de un botón «Actualizar».

**Qué dice la especificación.**
> «El Cliente modifica la cantidad de una línea.» (`CU-TDA-CRM`) — no dice si hace falta confirmar.

**Qué se hizo.**
- Con las flechas, la cantidad se aplica al instante; escribiendo, cuando se deja de tipear. Quitar
  una línea tampoco recarga la pantalla.
- Es la misma operación (`CO-084`, `CO-085`), con la misma verificación de stock en el servidor. El
  servidor devuelve el carrito recalculado: precio de cada línea, disponibilidad y total salen de
  la misma consulta de `CO-178`, nunca de una cuenta en el navegador. Si hubo que topear por stock,
  aparece el aviso; el contador del encabezado se actualiza.
- Sin guion, cada línea conserva su botón «Actualizar».

**Qué habría que cambiar.**
`CU-TDA-CRM`: decir que la cantidad se aplica al cambiarla, sin confirmación aparte.

---

### B-07-029 · Ajustes de la portada, del ingreso y del catálogo en pantallas anchas

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** la tienda pública
**Estado:** Resuelta — pedido explícito del responsable el 2026-10-05

**Qué apareció.**
El contador «01 / 12» de las filas sobraba. En una pantalla ultra ancha, el nombre predeterminado
del ingreso se cortaba en medio de la palabra («LONGB / OX») y el catálogo dejaba márgenes vacíos
con cuatro tarjetas por renglón.

**Qué dice la especificación.**
> «Contenido hasta `--ancho-escaparate`» (`TOKENS_VISUALES.md`, Los dos modos)

**Qué se hizo.**
- Las filas no tienen contador: quedan las flechas y la barra de recorrido.
- El nombre del ingreso va en una sola línea y su tamaño sigue el ancho de la escena, entre los
  extremos de `--pub-mega`.
- El catálogo (cabecera, panel y resultados) usa el ancho de la pantalla: en una pantalla ancha
  entran más tarjetas por renglón. Las demás secciones siguen en la columna.

**Qué habría que cambiar.**
`TOKENS_VISUALES.md`: exceptuar el catálogo de `--ancho-escaparate`, como el encabezado (B-07-026).

---

### B-07-030 · «Más de la serie» en la ficha y «/» para buscar

**Tipo:** Agregado · **Fecha:** 2026-10-05 · **Alcance:** `CU-TDA-CAT`, `CO-177`
**Estado:** Abierta — propuesta aceptada por el responsable el 2026-10-05 («cualquier otro
agregado de QoL que consideres»)

**Qué apareció.**
En una tienda de historietas, quien mira un tomo casi siempre busca el siguiente o el anterior, y
para eso tenía que volver al catálogo y buscar la serie.

**Qué dice la especificación.**
> «El Cliente puede navegar de regreso al catálogo conservando los filtros activos, o continuar la
> navegación a otra ficha.» (`CU-TDA-CAT`, paso 7)

**Qué se hizo.**
- La ficha de un tomo muestra, debajo, **«Más de la serie»**: los demás tomos visibles del mismo
  título y editorial, en orden, en una fila como las de la portada. «Ver todo» lleva al catálogo
  con la serie ordenada por título. Un tomo único no la muestra.
- **«/»** lleva a la búsqueda desde cualquier pantalla de la tienda (la del catálogo o la del
  encabezado), salvo que se esté escribiendo en un campo. El atajo está declarado para lectores de
  pantalla y en el texto de ayuda del campo.

**Qué habría que cambiar.**
`CO-177`: sumar a la salida de la ficha los demás tomos de la serie.

---

### B-07-031 · La Pasarela de Pago tiene una versión simulada, y MercadoPago va detrás de la misma interfaz

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-TDA-CMP`, `CU-TDA-INV`, `CO-088`, `CO-089`, `CO-091`, ACT-04
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 1)

**Qué apareció.**
Para cobrar hace falta una pasarela concreta. Con una sola pasarela real, la compra no se puede
probar sin red ni demostrar sin una cuenta del proveedor.

**Qué dice la especificación.**
> «Pasarela de Pago: Sistema externo (p. ej. MercadoPago) que procesa y confirma las transacciones
> de pago online (ACT-04).» (Glosario)

> «el sistema debe estar diseñado con una arquitectura modular que permita incorporar nuevas
> funcionalidades o integraciones con servicios externos (como nuevas pasarelas de pago […])»
> (RNF-07)

**Qué se hizo.**
- Hay **dos pasarelas** detrás de una misma interfaz: una **pasarela de prueba**, que es parte del
  sistema, y **MercadoPago** en modo de prueba. Cuál se usa se elige en Parámetros.
- La pasarela de prueba muestra el importe y dos botones, «Aprobar» y «Rechazar» (con el motivo).
  Avisa el resultado por el mismo aviso firmado que usaría una pasarela real, y acepta reembolsos.
  Es la que usan las pruebas y la demostración sin red.
- **Un aviso de pago no se cree por sí mismo**: el de la pasarela de prueba lleva firma, y el de
  MercadoPago se confirma consultando el pago a la API antes de generar el pedido.

**Qué habría que cambiar.**
ACT-04 y el glosario: declarar que la pasarela es intercambiable y que el sistema incluye una de
prueba. Si se quiere, `CU-CFG-PAR`: sumar la elección de pasarela a la ficha.

---

### B-07-032 · El costo de envío es un importe fijo de Parámetros, gratis desde el monto mínimo

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-TDA-CMP` paso 2, `CU-TDA-INV` paso 5, `CO-087`, `CU-CFG-PAR`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 2)

**Qué apareció.**
La compra presenta un «costo de envío calculado», y `CO-087` lo recalcula al cambiar la
dirección. Ningún artefacto dice cómo se calcula.

**Qué dice la especificación.**
> «dirección de envío predeterminada del perfil del Cliente (editable en este paso), costo de envío
> calculado y subtotal monetario» (`CU-TDA-CMP`, paso 2)

> «Logística: […] Monto mínimo para envío gratuito en $ ARS (decimal > 0)» (`CU-CFG-PAR`, paso 2)

Sobre el costo en sí: `Nada`.

**Qué se hizo.**
- Parámetros, sección Logística, suma el **costo de envío** (un importe fijo, mayor o igual a
  cero) junto al **monto mínimo de envío gratuito**, que ya estaba especificado. Los dos los fija
  el Administrador.
- Una compra cuyo subtotal de productos alcanza el monto mínimo no paga envío; las demás pagan el
  costo fijo. El costo no depende del destino: cambiar la dirección la guarda y devuelve el mismo
  costo.
- **Correo Argentino, verificado a pedido del responsable.** Tiene una API de cotización (MiCorreo,
  operación `/rates`), pero exige una cuenta comercial de MiCorreo y **el peso y las medidas del
  paquete**, que el sistema no registra: `Producto` no tiene peso, y `Formato` tiene medidas pero
  no peso. Sus tarifas públicas dependen del peso y de la zona (regional o nacional). Las dos
  opciones necesitan, como mínimo, el peso de cada producto. Queda para más adelante, como pidió el
  responsable.

**Qué habría que cambiar.**
`CU-CFG-PAR` paso 2, sección Logística: sumar el costo de envío. `ConfiguracionSistema`: sumar el
atributo. `CU-TDA-CMP` paso 2: «costo de envío según la política de Parámetros». Si más adelante
se cotiza con un operador logístico, `Producto` (o `Formato`) tiene que ganar el peso.

---

### B-07-033 · Cómo se calculan los puntos y el envío en la compra

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-089`, `CO-103`, RF-19, RF-20, `CU-TDA-CMP` A2, `CU-PTS-CJE`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 7 a 10)

**Qué apareció.**
Para acreditar puntos, canjearlos y cobrar el envío hay que decidir cuatro cosas que la
especificación deja abiertas.

**Qué dice la especificación.**
> «el saldo del cliente debe incrementarse en M / E puntos» (RF-19, condición de verificación)

> «calcula los puntos a debitar (precio del ítem dividido por la equivalencia ARS por punto
> configurada)» (`CU-PTS-CJE`, paso 4)

> «Los puntos se acreditan únicamente sobre el subtotal abonado en dinero, excluyendo los ítems
> cubiertos con puntos.» (RF-20)

> «si el total monetario es cero porque todos los ítems fueron cubiertos con puntos, el sistema
> omite la redirección a la Pasarela de Pago» (`CU-TDA-CMP`, A2)

**Qué se hizo.**
1. **Redondeo.** Los puntos son enteros. La acreditación redondea **hacia abajo** (M / E sin la
   fracción) y los puntos que pide un canje, **hacia arriba**: ninguna de las dos operaciones
   favorece al error.
2. **El envío no genera puntos ni se paga con puntos.** Se acredita sobre los productos pagados en
   dinero. Consecuencia: **A2 sólo ocurre con envío gratuito**; con envío a pagar, aun con todos los
   productos cubiertos, la compra pasa por la pasarela por el costo del envío.
3. **El monto mínimo de envío gratuito se compara con el subtotal de los productos** a su precio
   con oferta, antes del canje: canjear puntos nunca encarece el envío.
4. **Un ítem del canje es una línea entera**, con todas sus unidades, como declara el modelo
   (`cubierta con puntos` está en `LineaCarrito` y en `LineaPedido`).

**Qué habría que cambiar.**
RF-19: declarar el redondeo hacia abajo. `CU-PTS-CJE` paso 4: «redondeado hacia arriba».
`CU-TDA-CMP` A2: «si el total monetario es cero porque todos los ítems fueron cubiertos con
puntos **y el envío es gratuito**». `CU-CFG-PAR`, Logística: aclarar contra qué se compara el monto
mínimo.

---

### B-07-034 · Lo que se cobra queda congelado al confirmar, en un registro fuera del modelo

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-088`, `CO-089`, `CO-091`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 4 y 5)

**Qué apareció.**
Entre «Confirmar y pagar» y el aviso de la pasarela pasa tiempo, y el aviso llega de servidor a
servidor, sin la sesión del Cliente. Algo tiene que recordar qué se cobró, a quién y a dónde se
envía. Mientras tanto, el Cliente puede cambiar el carrito en otra pestaña.

**Qué dice la especificación.**
> «Si el total es mayor que cero: ninguna [postcondición] sobre el dominio. Se emitió una
> solicitud de cobro con su referencia.» (`CO-088`)

> «Existe un checkout confirmado asociado a la referencia.» (`CO-089`, precondiciones)

> «(a) Se creó pe : Pedido […] y tp : TransaccionPago.» (`CO-089`, postcondiciones)

**Qué se hizo.**
- Al confirmar, el sistema guarda un **cobro en curso**: la referencia, quién compra, la dirección,
  las líneas con su precio de ese momento y si están cubiertas con puntos, el envío y el total. No
  es un concepto del dominio, como no lo es la sesión. `TransaccionPago` se crea recién con el
  pago aprobado, como dice `CO-089`.
- **El pedido es lo que se cobró**, no el carrito como esté al llegar el aviso. El carrito pierde
  sólo las líneas que se compraron; si en otra pestaña se agregó algo después de confirmar, queda.
- Un cobro que ya se procesó no se procesa otra vez: un aviso repetido no hace nada.

**Qué habría que cambiar.**
`CO-088`: «Se emitió una solicitud de cobro con su referencia, **y quedó registrado lo que se
cobra**». `CO-089` (a): «El Carrito del Cliente perdió las líneas compradas» en vez de «quedó
vaciado».

---

### B-07-035 · El último ejemplar pagado por dos clientes: el segundo se reembolsa

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-089` E3, RNF-06
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 6)

**Qué apareció.**
Agregar al carrito no reserva stock, y confirmar el pedido tampoco: la reserva ocurre al
aprobarse el pago. Dos clientes pueden estar pagando el último ejemplar a la vez.

**Qué dice la especificación.**
> «Agregar al carrito no reserva stock: la reserva ocurre en la transacción de CO-089» (`CO-083`,
> notas)

> «Ejecutando simultáneamente dos solicitudes de compra del último ejemplar disponible de un
> producto, el motor de base de datos debe garantizar que solo una transacción sea confirmada y la
> otra sea rechazada» (RNF-06)

> «si la transacción atómica falla después de la confirmación de pago (error técnico del sistema)»
> (`CU-TDA-CMP`, E3)

**Qué se hizo.**
El primer pago aprobado se lleva el ejemplar. El segundo encuentra el stock insuficiente y sigue
el camino de E3: no se crea nada, se pide el reembolso a la pasarela, el carrito queda como estaba
y el Cliente recibe el aviso de que el cargo se revierte. Lo mismo si el producto dejó de venderse
(se descatalogó, por ejemplo) mientras el Cliente pagaba.

**Qué habría que cambiar.**
`CU-TDA-CMP` E3 y `CU-TDA-INV` E4: «si la transacción atómica falla después de la confirmación de
pago (error técnico del sistema **o stock perdido mientras se pagaba**)».

---

### B-07-036 · El invitado ve la sugerencia de iniciar sesión dos veces

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-TDA-INV` A1, `CO-181`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 07, sexta parte, amb. 11)

**Qué apareció.**
A1 sugiere iniciar sesión «si el usuario tiene una cuenta registrada», en el paso 1, cuando el
sistema todavía no sabe quién es.

**Qué dice la especificación.**
> «En el paso 1, si el usuario tiene una cuenta registrada, el sistema sugiere iniciar sesión para
> completar la compra con su cuenta […]. El usuario puede ignorar la sugerencia y continuar como
> invitado.» (`CU-TDA-INV`, A1)

**Qué se hizo.**
- En el paso 1, el formulario del invitado ofrece siempre «¿Tenés cuenta? Iniciá sesión».
- Al declarar los datos, si el correo es de una cuenta de cliente, el resumen lo dice y vuelve a
  ofrecer el inicio de sesión. Se puede seguir como invitado.

Revela que un correo tiene cuenta, lo mismo que ya revela el aviso de duplicado del registro.

**Qué habría que cambiar.**
`CU-TDA-INV` A1: «En el paso 1, el sistema ofrece iniciar sesión. En el paso 4, si el correo
declarado pertenece a una cuenta, lo sugiere de nuevo».

---

### B-07-037 · Una barra muestra cuánto falta para el envío gratis

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-TDA-CRC`, `CO-178`, `CO-180`, `CO-090`
**Estado:** Abierta — pedido del responsable el 2026-10-09 (plan 07, séptima parte)

**Qué apareció.**
El responsable pidió mostrar el envío gratis «con una barrita de progreso». El carrito, además, no
mostraba el envío.

**Qué dice la especificación.**
`Nada`. `CU-CFG-PAR` declara el monto mínimo de envío gratuito y B-07-032 dice cómo se usa.

**Qué se hizo.**
- El carrito, el checkout y el resumen del invitado muestran el envío y una barra que se llena con
  el subtotal de los productos (a precio con oferta, antes del canje) sobre el monto mínimo:
  «Te faltan $ X para el envío gratis», o «Tenés envío gratis» al alcanzarlo.
- En el carrito se recalcula junto con todo lo demás cuando cambia una cantidad.
- La barra se anuncia como barra de progreso y el texto va al lado: no depende del color.

**Qué habría que cambiar.**
`CO-178`, salida: sumar el costo de envío y lo que falta para el envío gratis.

---

### B-07-038 · El pedido se puede retirar en el local

**Tipo:** Agregado · **Fecha:** 2026-10-19 · **Alcance:** `CU-TDA-CMP`, `CO-180`, `CO-087`, `CO-088`, `CO-089`, `CO-092`, `Pedido`, DME-07
**Estado:** Abierta

**Qué apareció.**
El responsable pidió (2026-10-19) que el Cliente pueda elegir, al pagar, retirar el pedido en el
local en vez de recibirlo en su casa, reutilizando el stock en local. Decidió además: que es un
flujo alternativo de la compra y no un caso de uso nuevo (D1), que queda listo cuando el local lo
arma (D2), que si no se retira vuelve al stock con reembolso en puntos (D3) y que es sólo para
compras con cuenta (D4). Plan 07, octava parte.

**Qué dice la especificación.**
> «dirección de envío predeterminada del perfil del Cliente (editable en este paso), costo de envío
> calculado» (`CU-TDA-CMP`, paso 2)

Nada sobre retirar en el local. DME-07 termina en Despachado.

**Qué se hizo.**

- En el checkout, «Entrega» ofrece «Envío a domicilio» o «Retiro en el local». Con retiro no se
  pide dirección, el envío dice «Retiro en el local» sin costo y la barra del envío gratis no
  aparece. Se puede volver a envío a domicilio antes de confirmar. La elección vive en la sesión,
  como la dirección: el perfil no cambia.
- El pedido nace con su **modalidad de entrega**. Uno para retirar es de una cuenta, no cobra
  envío ni guarda dirección: lo impide la base, no sólo la pantalla. Los puntos se acreditan como
  en cualquier compra.
- El pedido se arma como cualquier otro y pasa de Armado a un estado terminal nuevo, **En el
  local** (nunca a Empaquetado ni Despachado). Cada unidad entra al stock en local del Cliente y
  el correo del cambio de estado le avisa que está listo para retirar. Las líneas no cambian de
  estado.
- La ficha del pedido y la del artículo ofrecen «Entregar todo»: el mostrador verifica al titular
  una sola vez y registra el retiro de cada artículo disponible. Si alguno cambió mientras tanto,
  no se registra ninguno.
- Si una pre-venta del pedido se demora, la opción 2 dice «Retirar ahora lo disponible»: el pedido
  vuelve a la fila del armado y el artículo demorado queda a nombre del Cliente cuando llega.

**Qué habría que cambiar.**
`CU-TDA-CMP`: un flujo alternativo «retiro en el local» en el paso 2, con sus efectos sobre los
pasos 4 a 6. `CO-180`, `CO-087`, `CO-088` y `CO-089`: la modalidad. `CO-092` y `CU-PED-EST`: el
paso de Armado a En el local con el ingreso al stock en local. DME-07: el estado En el local.
`Pedido`: el atributo «modalidad de entrega». `CU-PED-OPC`: el texto de la opción 2 en un pedido
para retirar.

---

### B-07-039 · Los cobros abandonados se descartan, y un pago tardío se reembolsa solo

**Tipo:** Agregado · **Fecha:** 2026-10-19 · **Alcance:** `CO-088`, `CO-089`, P-05
**Estado:** Abierta

**Qué apareció.**
Un Cliente que iba a la pasarela y no volvía dejaba su cobro «Esperando el pago» para siempre
(anotado en `docs/DEUDA.md` desde el 2026-10-09).

**Qué dice la especificación.**
`Nada`: ningún contrato declara qué pasa con un cobro que la pasarela nunca confirma.

**Qué se hizo** (plan 00, C3).
El Temporizador descarta los cobros pendientes de más de 24 horas (estado «Abandonado»), el mismo
plazo después del cual dejan de comprometer los puntos de un canje (B-10-005). Si la pasarela
aprueba un pago después de descartado, **se reembolsa automáticamente**, se avisa al Cliente y queda
como incidente en la auditoría; no se genera el pedido, porque el carrito ya pudo cambiar. Es
idempotente.

**Qué habría que cambiar.**
Una operación del Temporizador para el descarte (código a asignar), y en `CO-089` la excepción del
pago tardío.

---

### B-07-040 · Sugerencias en el buscador y carrito lateral

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-TDA-CAT`, `CO-176`, `CO-083`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, U1 y U2)

**Qué apareció.**
Buscar obligaba a ir al catálogo para ver si había algo, y agregar desde una tarjeta sólo dejaba un
aviso que desaparecía.

**Qué dice la especificación.**
`Nada` sobre sugerencias ni sobre lo que se ve al agregar.

**Qué se hizo.**
Al escribir en el buscador del encabezado aparecen las cinco primeras coincidencias, con portada y
precio, y un enlace a todos los resultados: es la misma búsqueda del catálogo. Al agregar desde
una tarjeta se abre un panel lateral con lo agregado, el total, lo que falta para el envío gratis e
«Ir al carrito». Sin guion, todo funciona como antes. La compra muestra sus pasos: carrito, entrega,
pago y listo.

**Qué habría que cambiar.**
`CU-TDA-CAT` paso 2: «al escribir, el sistema sugiere coincidencias». Paso 6: «el sistema muestra lo
agregado y el total del carrito».

---

### B-07-041 · La reserva de pre-venta tiene un máximo por Cliente

**Tipo:** Corrección · **Fecha:** 2026-10-26 · **Alcance:** `CU-TDA-CRA` A1, `CU-TDA-CRM` A1, `CU-TDA-CRC`, `CU-TDA-CMP`, `CU-CFG-PAR`, `CO-083`, `CO-084`, `CO-086`, `CO-178`, `CO-179`, `CO-130`, `ConfiguracionSistema`
**Estado:** Abierta — decidida por el responsable el 2026-10-26 (plan 00 de tope de reservas y errores, A)

**Qué apareció.**
Un Cliente podía reservar cualquier cantidad de un tomo en pre-venta: 9999 unidades entraban al
carrito y al pedido, y las que el ingreso no cubriera pasaban a demora. Una sola compra así deja
sin el tomo a todos los demás suscriptores de la serie y llena de demoras la gestión de pedidos.

**Qué dice la especificación.**
> «si el producto está en Pre-venta, el sistema no verifica stock: la reserva no tiene tope, y las
> unidades que no cubra el ingreso pasan a demora» (`CU-TDA-CRA` A1) · «Un producto en Pre-venta se
> agrega sin tope por stock (M11).» (`CO-083`, notas) · «En Pre-venta no hay tope por stock.»
> (`CO-084`, notas)

**Qué se hizo.**
- Parámetros globales → Compra online → Comercial gana el **«máximo de unidades por reserva»**, 5 por
  defecto, al menos 1, con su entrada de auditoría como cualquier parámetro.
- El máximo cuenta **por Cliente y por tomo**: la línea del carrito más lo que ya tiene reservado en
  pedidos que no están cancelados ni entregados. Así no se esquiva comprando de a cinco.
- Al agregar y al cambiar la cantidad, la línea queda en el máximo y se avisa («Cada Cliente puede
  reservar hasta 5 unidades de «…», contando sus pedidos»), como con el stock. Si ya no le queda
  nada por reservar, no se agrega y se le dice cuánto tiene reservado. Al fusionar el carrito del
  invitado pasa lo mismo.
- La consulta del carrito marca la línea que se pasa («Pasa el máximo por reserva · podés tener N»)
  y el pago no avanza hasta ajustarla. Cubre la reserva hecha en otra pestaña mientras la línea
  esperaba, y el máximo que el Administrador baja con carritos armados: se marcan, no se recortan.
- La ficha de una pre-venta dice «Hasta N unidades por Cliente» y el selector no ofrece más de lo
  que le queda; con la reserva completa, en lugar de «Reservar» informa que ya tiene el máximo.
- El stock sigue sin limitar la reserva: lo que falte al llegar el ingreso pasa a demora, como
  antes.

**Qué habría que cambiar.**
`CU-TDA-CRA` A1 y `CU-TDA-CRM` A1: «el sistema no verifica stock; la cantidad tiene como tope el
máximo de unidades por reserva menos lo que el Cliente ya tiene reservado de ese producto en pedidos
en curso». `CO-083` y `CO-084`: la misma nota, y E1 también para ese tope. `CO-178`: la línea que
supera el tope se informa como cantidad a ajustar. `ConfiguracionSistema` en el modelo de dominio y
`CU-CFG-PAR` (sección Comercial): el máximo de unidades por reserva, 5 por defecto.

---

### B-07-042 · La pre-venta se reserva contra lo que viene en camino, hasta un cupo

**Tipo:** Corrección · **Fecha:** 2026-10-26 · **Alcance:** `CU-TDA-CRA`, `CU-TDA-CRM`, `CU-TDA-CMP`, `CU-RST-SUS`, `CU-CFG-PAR`, `CO-083`, `CO-084`, `CO-089`, `CO-075`, `CO-130`
**Estado:** Abierta — decidida por el responsable el 2026-10-26 (plan 00 del circuito de proveedores)

**Qué apareció.**
Con el máximo por Cliente (B-07-041) un Cliente ya no reserva cien tomos, pero cien Clientes
todavía pueden reservar cinco cada uno de algo de lo que se pidieron veinte. La reserva no sabía
cuánto venía en camino porque lo pedido no estaba registrado (B-05-010).

**Qué dice la especificación.**
> «si el producto está en Pre-venta, el sistema no verifica stock: la reserva no tiene tope, y las
> unidades que no cubra el ingreso pasan a demora» (`CU-TDA-CRA` A1) · «Un producto en Pre-venta se
> agrega sin tope por stock (M11).» (`CO-083`, notas)

**Qué se hizo.** Con las cuatro decisiones del responsable:
- **La pre-venta se abre contra un pedido enviado** (decisión 1): un producto editorial sin stock
  con unidades pendientes en un pedido pasa solo a Pre-venta, con la llegada estimada del pedido.
  Nunca se reserva lo que no se pidió.
- **El cupo** es lo pendiente de recibir menos un **margen** de Parámetros → Compra online (10 % por
  defecto, entre 0 y 50, global; decisión 2), hacia abajo, menos lo ya reservado. Cubre lo que el
  proveedor suele no mandar completo.
- **Con stock se vende el stock** (decisión 4): la reserva se abre recién cuando la venta, en la
  tienda o en el mostrador, deja el producto en cero y hay un pedido en camino.
- El cupo se controla al agregar, al cambiar la cantidad y en la consulta del carrito, que no lo
  reserva; y otra vez, con el producto bloqueado, al confirmar el pago. Si se llenó mientras se
  pagaba, el cobro se reembolsa como el último ejemplar perdido (B-07-035). Al Cliente se le dice
  cuántos lugares quedan, distinto del máximo por Cliente.
- **Con el cupo lleno**, la ficha dice «La pre-venta está completa» y ofrece **«Avisarme si llegan
  de más»**: la lista de espera de `CU-RST-SUS`, que se avisa con lo que sobre al llegar.
- Una pre-venta sin fecha estimada se admite: la ficha dice «Se envía cuando llegue».
- La pre-venta sigue siendo sólo editorial (decisión 3).

**Qué habría que cambiar.**
`CU-TDA-CRA` A1 y `CU-TDA-CRM` A1: la cantidad tiene como tope el menor entre el máximo por Cliente
(B-07-041) y el **cupo de la pre-venta**. `CO-083` y `CO-084`: la misma nota, con E1 para el cupo.
`CO-089`: con el producto bloqueado se vuelve a contar el cupo, y si se llenó el cobro se
reembolsa. `CO-075`, precondiciones: el producto está Agotado **o en Pre-venta con el cupo
completo**. `CU-CFG-PAR` y `CO-130`, sección Comercial: el margen del cupo de pre-venta. En el modelo
de dominio, el estado Pre-venta se define por el pedido en camino (B-05-010).

---

### B-07-043 · Un pago rechazado no cierra el cobro: se puede reintentar en la pasarela

**Tipo:** Agregado · **Fecha:** 2026-11-07 · **Alcance:** `CU-TDA-CMP`, `CU-TDA-INV`, `CO-088`, `CO-089`
**Estado:** Abierta

**Qué apareció.**
En MercadoPago, cuando le rechazan la tarjeta, el Cliente sigue en la página de la pasarela y
reintenta con otra. Cada intento es un pago distinto con la misma referencia del cobro. El sistema
cerraba el cobro con el primer rechazo e ignoraba el aprobado que llegaba después: el Cliente
pagaba y no se generaba pedido ni se reembolsaba (revisión integral, R-01, reproducido con una
prueba).

**Qué dice la especificación.**
> `CO-089`, Excepciones: «Pago rechazado o fallido (E2): no se genera pedido, no se modifica stock
> ni puntos. Se notifica al Cliente con el mensaje retornado por la pasarela y el carrito permanece
> intacto.»

No dice si después de un rechazo puede llegar un aprobado del mismo checkout.

**Qué se hizo.**
Un rechazo cumple E2 (no hay pedido ni cambios en stock o puntos, queda en la auditoría y el
Cliente ve el mensaje), pero el checkout sigue abierto: si después llega un aprobado, el pedido se
genera normalmente. Un aviso repetido del mismo pago rechazado se registra una sola vez. El
checkout se cierra cuando llega un pago aprobado, cuando el Cliente confirma de nuevo desde la
tienda o a las 24 horas, cuando se da por abandonado (B-07-039). Si el Cliente vuelve a confirmar,
el cobro anterior se descarta: así no deja puntos comprometidos ni genera un segundo pedido, y si
se aprobara igual, se reembolsa como cualquier pago tardío. La misma regla vale para el pago del
envío de stock almacenado. Si la pasarela devuelve al Cliente con un aprobado antes de que llegue
su aviso, la pantalla muestra la espera en vez del rechazo anterior.

**Qué habría que cambiar.**
`CO-089`, Excepciones (E2): agregar que un rechazo no cierra el checkout y que un pago aprobado
posterior de la misma referencia se materializa. `CO-088`, Notas: confirmar de nuevo reemplaza el
checkout abierto anterior.

---

### B-07-044 · Si el producto pasa a pre-venta mientras el invitado paga, se reembolsa

**Tipo:** Agregado · **Fecha:** 2026-11-07 · **Alcance:** `CU-TDA-INV`, `CO-181`, `CO-089`
**Estado:** Abierta

**Qué apareció.**
Mientras un invitado está en la pasarela, se puede vender la última unidad en el mostrador. Si hay
un pedido al proveedor en camino, el producto pasa a pre-venta (B-05-001). Al aprobarse el pago,
el pedido del invitado se generaba con una reserva. Sin cuenta, si la editorial cancela no hay a
quién devolverle los puntos, y ante una demora nadie puede decidir.

**Qué dice la especificación.**
> `CO-089`, Notas: «En la compra como invitado (CU-TDA-INV) […] el pedido nace en Pendiente de
> armado, porque el carrito de invitado no admite pre-ventas.»

Se verifica al iniciar la compra (`CO-181`), no al materializar el pago.

**Qué se hizo.**
Al materializar el pago de un invitado, una línea cuyo producto quedó en pre-venta se trata como
el stock perdido mientras se pagaba (E3): no se genera el pedido, se reembolsa y se le explica al
invitado por qué.

**Qué habría que cambiar.**
`CO-089`, Excepciones (E3): agregar, como caso de fallo, que un producto de un pago de invitado
haya pasado a pre-venta.

---

### B-07-045 · La preferencia de MercadoPago vence a las 24 horas, igual que el cobro

**Tipo:** Agregado · **Fecha:** 2026-11-07 · **Alcance:** `CU-TDA-CMP`, `CO-089`
**Estado:** Abierta

**Qué apareció.**
La preferencia de pago no tenía vencimiento. MercadoPago deja pagar un cupón en efectivo (Rapipago,
Pago Fácil) días después, pero el sistema da el cobro por abandonado a las 24 horas (B-07-039) y
reembolsa lo que llega tarde. El Cliente pagaba en una ventanilla y recibía un reembolso.

**Qué dice la especificación.**
`Nada.` La especificación no cubre el vencimiento del pago en la pasarela.

**Qué se hizo.**
La preferencia vence cuando el cobro se da por abandonado, y el cupón de pago en efectivo vence a
la misma hora. MercadoPago deja de aceptar el pago después de ese momento, en vez de aceptarlo para
que el sistema lo devuelva.

**Qué habría que cambiar.**
`CU-TDA-CMP`, requisitos de la integración con la pasarela: el plazo para pagar coincide con el de
abandono del checkout.

---

### B-07-046 · Las filas de la portada pasan a ser secciones de varios tipos

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-CFG-SEC` (antes `CU-CFG-FIL`), `CU-TDA-POR`, `guardarSeccionesDeLaPortada` (`NUEVO-CO-23`)
**Estado:** Abierta — pedido explícito del responsable el 2026-11-11 (plan 07, novena parte, aprobado)

**Qué apareció.**
El responsable pidió que la portada admita, además de las filas de productos, filas o carruseles
de fotos que se ordenen igual que ellas, y una fila de botones con foto que lleve directo a un
grupo de productos.

**Qué dice la especificación.**
`Nada.` Las filas no tienen caso de uso en el documento (B-07-009); `CU-CFG-FIL` se asignó el
2026-11-08 y su ficha no se escribió.

**Qué se hizo.**
- Cada elemento de la portada es una **sección** con un tipo: **Productos** (la fila de siempre,
  o una **vitrina** que destaca uno por vez), **Accesos con foto** (3 a 8), **Página de
  historieta** (3 a 6 viñetas), **Cinta de fotos** (4 a 12), **Panel destacado** (1 imagen, con
  texto y botón), y **Recién llegados** y **Lo que se viene**, que arma el sistema. Todas van en
  un solo orden, en el mismo gestor por tarjetas de B-07-010.
- Recién llegados y Lo que se viene existen siempre: se mueven y se apagan, no se borran. Al
  migrar quedaron primeras, en el orden en que la portada las mostraba, y las filas detrás.
- El tipo se elige al agregar la sección y después no cambia.
- Cada imagen puede llevar a una parte de la tienda, de una **lista cerrada**: sin enlace, las
  pre-ventas, un grupo, una etiqueta, un tipo de producto, una editorial o un producto, que se
  indica por su código. El servidor rechaza cualquier otro destino y la base exige que el destino
  tenga su dato.
- Un acceso cuyo destino se dio de baja, o que no tiene productos visibles, no se dibuja; una
  viñeta, una foto o el panel con el destino caído se muestran sin enlace.
- Una imagen sin archivo sólo se admite como onomatopeya de la página de historieta, que se
  dibuja sobre un panel de color.
- El título de un acceso o de una foto es su texto alternativo; una viñeta sin texto es
  decorativa.
- Las secciones alternan noche y papel según su lugar, como páginas de una revista, y llevan su
  número en el título.
- Guardar se audita como «Modificación de las secciones de la portada», con la lista anterior y
  la nueva, incluidas las imágenes y adónde lleva cada una. Los registros viejos conservan su
  acción.

**Qué habría que cambiar.**
- Identificación de los Casos de Uso › Mód. 17: `CU-CFG-SEC` Administrar Secciones de la Portada
  (reemplaza a `CU-CFG-FIL`, ya registrado en `CODIGOS.md`); ficha nueva, con su DSS.
- Contratos › Mód. 17: `guardarSeccionesDeLaPortada`, con número a asignar.
- `MODELO_DE_DOMINIO`: **SeccionPortada** reemplaza a FilaPortada (tipo, presentación, título,
  antetítulo, texto, texto del botón, etiqueta o grupo, imagen, orden, activa) e
  **ImagenDeSeccion** (imagen, título, texto, forma del texto, destino y su dato, orden).
- `CU-TDA-POR`: la portada dibuja las secciones activas en su orden.

---

### B-07-047 · El carrusel de banners se ve en un televisor dentro del hero

**Tipo:** Desvío · **Fecha:** 2026-11-11 · **Alcance:** `CU-CFG-BNC`, `CU-TDA-POR`
**Estado:** Abierta — consultado: plan 07, novena parte, ambigüedad 2, aprobada

**Qué apareció.**
El hero era texto sobre un fondo vacío y el carrusel quedaba debajo, como una sección aparte.

**Qué dice la especificación.**
> «**Transición**: `barrido-diagonal` […]. Controles «Anterior», «Siguiente» y «Pausar» como
> `.boton-texto`, más indicadores cuadrados» (`identidad_visual.md`, Carrusel de banners).

**Qué se hizo.**
El carrusel pasa al hero, dentro de un televisor: la pantalla con el rótulo de reproducción, el
canal y el tiempo, las perillas, un botón por banner que lo elige, y los controles de cinta
(anterior, pausar, siguiente). El cambio de banner es un **cambio de canal**: la imagen entra por
bandas y pasa una banda de ruido. El intervalo, la pausa con el puntero, con el foco y con el
botón, y el movimiento reducido siguen igual (`CO-132` no cambia). Sin banners, el televisor
pasa la portada destacada. La vista previa de la galería de banners sigue mostrando el carrusel
de siempre.

**Qué habría que cambiar.**
`identidad_visual.md`, Portada (hero) y Carrusel de banners: el televisor y sus controles (ver
B-07-049).

---

### B-07-048 · El menú de la tienda es una botonera de íconos

**Tipo:** Desvío · **Fecha:** 2026-11-11 · **Alcance:** la cáscara pública
**Estado:** Abierta — consultado: pedido explícito del responsable el 2026-11-11 («la barra de
arriba se ve muy sosa […] con iconitos»). Reemplaza a B-07-027.

**Qué apareció.**
El responsable pidió íconos en la barra de arriba, como en la referencia.

**Qué dice la especificación.**
> «Menú en `--pub-rotulo`; el enlace actual con un subrayado `--acento` de 3px sesgado»
> (`identidad_visual.md`, Encabezado). B-07-027 dejó el menú «todo texto».

**Qué se hizo.**
- La barra es un aparato: la marca en una pestaña, el buscador en una píldora y una botonera con
  un ícono por destino —Inicio, Catálogo, **Pre-ventas** (nuevo), los puntos, el carrito y la
  cuenta—. El nombre de cada destino aparece al pasar el puntero o con el foco, y está siempre
  en el enlace para el lector de pantalla. El actual va encendido. El invitado ve «Ingresar»
  con texto.
- Detrás de la barra fija hay un velo con desenfoque.
- En el celular quedan el catálogo, los puntos, el carrito y la cuenta, en la misma fila que la
  marca; el buscador va debajo.
- Todo lo de antes sigue: las sugerencias, el atajo «/», el contador que rebota, el menú de la
  cuenta y la barra que se compacta al bajar.
- El pie conserva su contenido —el botón de arrepentimiento, los accesos de la tienda, la ayuda,
  el contacto y las redes— con la línea «■ STOP · Fin de la cinta» arriba, íconos de contacto,
  «◀◀ Rebobinar» (vuelve arriba) y el nombre de la tienda gigante, cortado.

**Qué habría que cambiar.**
`identidad_visual.md`, Encabezado y Pie.

---

### B-07-049 · Aparatos e impresos: redondeados, lima y desenfoque en el escaparate

**Tipo:** Desvío · **Fecha:** 2026-11-11 · **Alcance:** el modo público
**Estado:** Abierta — consultado: pedido explícito del responsable el 2026-11-11 («Puedes usar
esquinas redondeadas y tonos verde lima, solo si son coherentes visualmente, lo mismo con
desenfoques, animaciones»); plan 07, novena parte, ambigüedad 8, aprobada. Espera la enmienda de
los documentos visuales.

**Qué apareció.**
El responsable pidió más personalidad, con el estilo retro, musical y de VHS de la referencia, y
admitió redondeados, lima y desenfoques si son coherentes.

**Qué dice la especificación.**
> «`--radio` `0` — **Nada redondeado.**» · «`--ok` […] Sólo modo operativo» · «Prohibido: […]
> `backdrop-filter` **salvo en el `::backdrop` de un `<dialog>`**» (`TOKENS_VISUALES.md`). «No se
> crean animaciones fuera de esta lista» (`identidad_visual.md`, Catálogo de animaciones).

**Qué se hizo.**
- Una regla: los **aparatos** (la barra, el televisor, la botonera, los controles de cinta, el
  reproductor de la vitrina, el riel, el globo de ayuda, el cajón del carrito) son redondeados
  —16px los contenedores, píldora los botones— y usan el color «Aparatos encendidos» (lima por
  defecto; B-17-021) para lo encendido, lo que se reproduce y lo elegido. Lo **impreso**
  (portadas, tarjetas, viñetas, fotos, títulos) sigue recto, con cortes y sombras duras. La acción
  sigue siendo el botón principal.
- Lo retro: líneas de barrido muy tenues sobre todo el escaparate; el título del hero con el
  corrimiento de color de una cinta gastada; los títulos de sección como lomos de cinta
  numerados; la radio («En rotación» con un ecualizador que se detiene con ella); el riel de
  secciones en escritorio ancho.
- Patrones nuevos: barra de aparato, televisor, radio, lomo de cinta, vitrina con reproductor,
  acceso inclinado, página de viñetas, foto con cinta, panel destacado, riel de secciones y pie
  «fin de la cinta».
- Animaciones nuevas: `cambio-canal`, `banda-ruido`, `texto-deriva` (atada al desplazamiento,
  nunca sola), `vitrina-entra` y `cajon-entra`. El ecualizador reutiliza `barras-carga`, la cinta
  de fotos `ticker` y la página `barrido-diagonal`. Con movimiento reducido no corre ninguna. La
  animación `tracking` que listaba el plan no se construyó: el título conserva `titulo-glitch`.

**Qué habría que cambiar.**
- `TOKENS_VISUALES.md`: Forma (radio de aparato y píldora, sólo en el público), Color (el rol
  «Aparatos encendidos» en el público), Prohibido (el desenfoque de la barra fija).
- `identidad_visual.md`: la regla de aparatos e impresos entre las siete reglas, los patrones del
  modo público y las cinco animaciones en el catálogo.

---

### B-07-050 · Recién llegados se arma con una vitrina y la grilla de siempre

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-TDA-POR`
**Estado:** Abierta — plan 07, novena parte

**Qué apareció.**
Con pocos productos, la estantería de recién llegados dejaba un hueco grande de papel.

**Qué dice la especificación.**
`Nada.` «Recién llegados» se agregó en la tercera parte sin caso de uso.

**Qué se hizo.**
Arriba, una vitrina con los seis primeros que tienen portada, que se recorren con un reproductor;
debajo, la grilla con los ocho siguientes, como antes. La vitrina usa el mismo botón de agregar
que la tarjeta, con el mismo cajón del carrito. La radio nombra lo llegado entre esos catorce. En
el celular, la grilla de la portada va de a dos.

**Qué habría que cambiar.**
La ficha de `CU-TDA-POR`, cuando se escriba.

---

### B-07-051 · El precio no se veía en las tarjetas sobre papel

**Tipo:** Corrección · **Fecha:** 2026-11-11 · **Alcance:** la estantería y las filas sobre papel
**Estado:** Resuelta

**Qué apareció.**
En las secciones de papel el precio de la tarjeta salía blanco sobre blanco. Ya pasaba con
«Recién llegados» antes de esta parte.

**Qué dice la especificación.**
> «Precios · `--rol-precios-texto` · Neutro» (`identidad_visual.md`, Mapa de colores).

**Qué se hizo.**
El neutro es el texto fuerte de la superficie de la tarjeta: noche sobre papel, blanco sobre
noche. Antes se resolvía una sola vez, con la superficie noche de toda la tienda.

**Qué habría que cambiar.**
Nada en el documento: el error era del código.

---

### B-07-052 · Casete en la vitrina, sin «¡NOVEDAD!» en recién llegados, rebobinar, carnet y ficha

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-TDA-POR`, `CU-TDA-CAT` (la ficha, `CO-177`), «Mi cuenta» (`CU-CLI-HIS`)
**Estado:** Abierta — pedidos explícitos del responsable el 2026-11-11, durante la construcción de la novena parte

**Qué apareció.**
Al revisar lo construido, el responsable pidió: elementos de casete, y que en «Recién llegados»
no se repita el cartel de novedad; que «Rebobinar» suba deslizándose; que el carnet del Cliente
se parezca a la ficha de un personaje de la referencia; y mejorar la ficha de producto. El plan
dejaba la ficha y la cuenta para una etapa posterior.

**Qué dice la especificación.**
`Nada.` La guía describe el carnet (`identidad_visual.md`, Compra y cuenta del Cliente) pero no
el casete, el rebobinado ni la ficha con este lenguaje.

**Qué se hizo.**
- **Casete.** El bloque de la vitrina muestra un casete: la etiqueta con el número de pista y el
  título, la ventana con dos carretes que giran una vez al cambiar de producto, y «Lado A ·
  Pista 01 de 06» arriba.
- **«¡NOVEDAD!»** no aparece en «Recién llegados» (vitrina y grilla): ahí todo es nuevo. Sigue en
  el catálogo, en las filas y en la ficha. «¡TOMO 1!» sigue en todos lados.
- **Rebobinar.** La página sube deslizándose, con el rótulo «◀◀ REW» y líneas de rebobinado; al
  llegar, el foco vuelve a la marca. Con movimiento reducido sube de golpe.
- **El carnet** es la credencial del socio: barra con el número de socio, retrato con las
  iniciales, el nombre, «Socio desde» con el año del alta, el código de cliente con un código de
  barras decorativo, y los puntos y lo guardado como estadísticas. Las secciones de la cuenta son
  una botonera, con la actual encendida. No muestra ningún dato nuevo.
- **La ficha de producto**: el título gigante en contorno detrás, la portada sobre la trama, el
  número del tomo rayado junto al título, la compra en una caja de aparato con su rótulo («En
  venta», «Pre-venta», «Sin stock») y la sinopsis en un recuadro. Lo que se puede hacer en la ficha
  no cambia.

**Qué habría que cambiar.**
`identidad_visual.md`: el casete y el rebobinado en los patrones y en el catálogo de animaciones
(`carrete-gira`, `rebobina`); el carnet y la ficha en Compra y cuenta del Cliente.

---

### B-07-053 · Catálogo con el lenguaje nuevo, barrido en negro, cintas en marcha y textos largos

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-TDA-CAT` (`CO-176`), `CU-TDA-POR`, la cáscara pública
**Estado:** Abierta — pedidos explícitos del responsable el 2026-11-11, durante la construcción de la novena parte

**Qué apareció.**
El responsable pidió actualizar el catálogo; una transición entre páginas «como un barrido en
negro»; algo en movimiento mientras se baja, para sostener la atención; que la galería de fotos
no se corte; y probar nombres muy largos en todos los campos.

**Qué dice la especificación.**
> «Entre páginas públicas, la vista nueva entra con `barrido-diagonal` en `--dur-4`»
> (`identidad_visual.md`, Transición entre vistas). Del resto, `Nada`.

**Qué se hizo.**
- **El catálogo**: el título en un lomo de cinta sobre la palabra gigante en contorno, el buscador
  en una píldora, una cinta en marcha con los tipos de material, el panel de filtros como aparato
  (lo prendido, encendido) y la cantidad de productos como contador. Los filtros, la búsqueda y la
  paginación no cambian.
- **El cambio de página** es un barrido en negro: la página que se va se corta en diagonal, queda
  el negro, y la nueva entra con otro corte. Dura unos 640 ms. Con movimiento reducido no ocurre.
- **Lo que se mueve al bajar**: una barra fina bajo el encabezado que crece con lo recorrido, y
  una cinta en marcha entre secciones con el nombre de la que viene. Las dos se mueven sólo
  mientras la persona se desplaza: nada corre solo, así que no hay nada que pausar.
- **La cinta de fotos** ya no se corta: con pocas fotos, cada vuelta las repite hasta llenar la
  pantalla, y el bucle empalma justo. Sólo la primera aparición de cada foto se anuncia.
- **Textos largos**: probados con un título de 130 letras y una palabra de 60 en cada campo, en
  escritorio y a 390 px. Se corrigieron cuatro desbordes (título de la tarjeta, globo de la
  viñeta, tarjeta titular de la fila, título de la ficha). Los títulos de tarjeta se acotan a
  cuatro líneas y los de acceso a tres; el título entero sigue en la ficha.

**Qué habría que cambiar.**
`identidad_visual.md`: Transición entre vistas (el barrido en negro, `vista-tapa` y
`vista-destapa`); el catálogo de animaciones (`progreso-lectura`, `cinta-avanza`); la regla de
acotar títulos en tarjetas.

---

### B-07-054 · El casete recortado y la ciudad: muro, cinta de película, pila de televisores y detalles

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-TDA-POR`, la cáscara pública
**Estado:** Abierta — pedido explícito del responsable el 2026-11-11, con referencias nuevas de la estética de ZZZ en `.contexto-ia/referencias-pantallas/`

**Qué apareció.**
El responsable pidió reemplazar el bloque naranja de la vitrina por el casete recortado, sin el
título del tomo (que ya está al lado), y dijo que la tienda seguía lejos de lo esperado: «falta
esa vista retro, con personalidad urbana, con pequeños detalles, lleno de vida».

**Qué dice la especificación.**
`Nada.` Viñeta Nocturna no describe estos elementos.

**Qué se hizo.**
- **El casete recortado** va suelto sobre la escena de la vitrina, con borde blanco de figura
  recortada, sombra dura y un trozo de cinta adhesiva. La carcasa lleva tornillos, la etiqueta
  con franjas, la marca de la tienda, el lado «A», el número de pista y renglones, la ventana con
  los carretes y la base. Entra con un golpe al cambiar de producto y los carretes giran.
- **El muro**: palabras gigantes en contorno, rótulos chicos y garabatos propios, casi invisibles,
  detrás del hero, la cabeza del catálogo, la ficha y las secciones de la portada. Se corre apenas
  al bajar.
- **La cinta de película**: la cinta entre secciones pasa a lima con perforaciones y los nombres en
  cuadros.
- **La pila de televisores**: dos televisores chicos detrás del principal, con lo último que llegó.
  En el celular no aparecen.
- **El sello circular** del hero, que gira con el desplazamiento.
- **Relieve en los aparatos**: un filo de luz arriba y uno de sombra abajo, sin desenfoque.
- **Detalles de imprenta**: texto chico en vertical con marcas de registro en el margen de cada
  sección y un código de barras en cada lomo.
- Nada se mueve solo: lo que se mueve está atado al desplazamiento, y con movimiento reducido se
  queda quieto.

**Qué habría que cambiar.**
`identidad_visual.md`: el muro, la cinta de película, la pila de televisores, el sello y el relieve
de los aparatos en los patrones del modo público; `casete-entra`, `muro-pasa` y `sello-gira` en el
catálogo de animaciones. La regla «Sigue fuera: los fondos fotográficos con velos» no se toca: el
muro es dibujo, no fotografía.

---

### B-07-055 · El barrido en negro es un telón propio; la ficha, un expediente; más detalles

**Tipo:** Corrección · **Fecha:** 2026-11-11 · **Alcance:** la cáscara pública, `CU-TDA-CAT` (`CO-177`), `CU-TDA-POR`
**Estado:** Resuelta — pedido explícito del responsable el 2026-11-11 («la transición con barrido a negro no funciona»)

**Qué apareció.**
El responsable no veía el barrido entre páginas. La transición nativa del navegador sí corría,
pero la capa de carga tapaba la pantalla a los 300 ms y el navegador fotografiaba la página que
se iba ya cubierta de negro: un barrido de negro sobre negro no se ve. Además, Firefox no tiene la
transición nativa y Chrome la cancela si la página nueva tarda varios segundos.

**Qué dice la especificación.**
> «`@view-transition { navigation: auto; }` en `tokens.css`. Entre páginas públicas, la vista
> nueva entra con `barrido-diagonal`» (`identidad_visual.md`, Transición entre vistas).

**Qué se hizo.**
- **El telón**: al llegar a una página de la tienda, un telón negro con líneas de pantalla se abre
  en diagonal; al hacer clic en un enlace de la tienda, se cierra desde la izquierda y, mientras el
  servidor responde, dice «Cargando» con un ecualizador. Se abre con CSS, así que un guion roto
  nunca lo deja cerrado. En la tienda la transición nativa se apaga y la capa de carga no se activa
  con los enlaces: el telón cumple las dos funciones. Con movimiento reducido no hay telón.
- **La ficha como expediente**: el número de expediente con código de barras arriba; la portada
  sujeta con cinta sobre una hoja de papel rayada con el borde cortado, la pestaña del tomo, el
  sello de goma del estado («En stock», «Pre-venta», «Sin stock») y el pie mecanografiado. El
  número rayado junto al título se quitó: chocaba con títulos largos.
- **El catálogo**: la pila con las tres primeras portadas de lo que se está viendo y un ticket con
  la cantidad; el panel de filtros acompaña al bajar, con su propio recorrido; «¡NOVEDAD!» pasa a
  una cinta cruzada en la esquina de la portada, más chica.
- **El sello del hero** se rehízo: el texto ocupa justo la vuelta sin pisarse, sobre un disco
  negro con aros, y se movió para no tapar los controles del televisor.
- **Anotaciones a mano** junto a algunos títulos de la portada («¡Recién salidos!», «¡Elegí tu
  cinta!», «¡Pasá a ver!»), con una flecha dibujada.

**Qué habría que cambiar.**
`identidad_visual.md`, Transición entre vistas: el telón reemplaza a la transición nativa en el
modo público. Y la ficha, el catálogo y las anotaciones en los patrones del modo público.

---

### B-07-056 · El tope de la cantidad avisa; el Cliente con el lenguaje nuevo; cajón, visor y barra propia

**Tipo:** Agregado · **Fecha:** 2026-11-11 · **Alcance:** `CU-TDA-CAT` (`CO-177`), `CU-TDA-CRA` (`CO-083`), `CU-TDA-CRC`, `CU-TDA-CMP`, «Mi cuenta», la cáscara pública
**Estado:** Abierta — pedidos explícitos del responsable el 2026-11-11

**Qué apareció.**
El responsable pidió: que el «+» de la ficha avise cuando no quedan más unidades; pasar el
carrito, la compra, el perfil y los pedidos del Cliente al diseño nuevo; un visor de imágenes con
más personalidad; una barra de desplazamiento propia; arreglar el cajón del carrito; corregir el
muro, que dejaba «LONGBOX» cortado; probar desbordes de texto y tamaños de pantalla; y, al final,
quitar el sello giratorio del hero.

**Qué dice la especificación.**
`Nada.` `CO-083` valida la cantidad en el servidor; la pantalla no tenía aviso propio.

**Qué se hizo.**
- **El tope de cantidad.** El máximo de la ficha descuenta lo que ya está en el carrito. Al
  llegar, el «+» se ve apagado y, si se lo aprieta, cae un globo que dice por qué: «no hay más
  unidades: hay 3 en stock», «… y ya tenés 2 en el carrito», o el máximo por Cliente de la
  pre-venta. Con todo el stock en el carrito, la ficha lo dice y no ofrece agregar. El servidor
  sigue validando igual. El mismo control sirve al carrito.
- **El Cliente**: títulos con corrimiento de color, paneles como aparatos, el estado vacío como
  un televisor sin señal, los pasos de la compra como el contador de una casetera, las líneas del
  carrito y del pedido como cajas de cinta, el resumen como un ticket de papel con código de barras,
  las tarjetas de entrega y pago con la elegida encendida, y los pedidos de la cuenta como tickets
  de alquiler con su talón.
- **El cajón del carrito**: rótulo de grabación, la portada sujeta con cinta, el tomo en el
  título, el ticket con unidades y total, un medidor del envío gratis que se llena al abrir y las
  acciones a lo ancho. A todo el ancho en el celular.
- **El visor**: la imagen se inclina al pasar, cada cambio entra por bandas, las miniaturas van en
  una tira de película y la ampliación es una pantalla de proyección.
- **La barra de desplazamiento**: riel oscuro con su guía y tirador lima con estrías, naranja al
  tomarlo; en Firefox, los colores. Las cintas giradas ya no generan barra horizontal.
- **El muro** se rearmó para que ninguna palabra cruce el borde de la baldosa.
- **El sello giratorio del hero se quitó**, a pedido del responsable.
- **Prueba de desbordes**: 18 pantallas públicas y del Cliente en 7 anchos (360 a 1920 px), con
  los datos reales y con textos de 130 letras y palabras de 60 en cada campo. Los globos de nombre
  del carrito y la cuenta se salían de la pantalla en el celular; corregido.

**Qué habría que cambiar.**
`CU-TDA-CAT`, paso de la ficha: el aviso al llegar al tope de unidades. `identidad_visual.md`:
el cajón, el visor, la barra de desplazamiento y las piezas del Cliente en los patrones del modo
público.
