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
**Estado:** Resuelta

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
