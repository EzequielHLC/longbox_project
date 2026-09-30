> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Estilo preliminar

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

No es un caso de uso y no tiene contratos. Reemplaza el sistema visual entero por el estilo plano
de `.contexto-ia/identidad_visual.md`, con los valores de `.contexto-ia/TOKENS_VISUALES.md`. Va
primero para que cada caso de uso que se cierre después ya quede con este estilo.

Pasa por las puertas que le corresponden: suite, cobertura, análisis estático y formato. Suma una
prueba propia que impide que el estilo se degrade.

---

## 1. Qué cubre

| Pieza | Hoy | Después |
| --- | --- | --- |
| Tokens | En un `tailwind.config` dentro de `templates/base.html`, con la paleta retirada | Una sola declaración `:root` con las variables CSS de `TOKENS_VISUALES.md`, en una hoja estática servida por `static/` |
| Estilo de los componentes | Bloques `<style>` repartidos en 14 plantillas, más clases utilitarias de Tailwind en todas (1468 atributos `class`) | Una hoja estática con los componentes por nombre de clase. Ninguna plantilla lleva `<style>` ni `style=""` con valores |
| `base.html`, `base_publico.html`, `base_operativo.html` | Tema oscuro, fuentes web, efectos | Las dos cáscaras de `identidad_visual.md`: columna centrada y columna de alto completo con menú |
| Parciales compartidos (`templates/_*.html`) | 21 parciales | Los mismos nombres donde la función se conserva; se borran los que sólo existían por lo retirado |
| Pantallas de las cuatro apps | 55 plantillas | Mismo contenido y mismo comportamiento, marcado con las clases nuevas |
| Prueba del estilo | No existe | `apps/core/tests/test_estilo_preliminar.py` |

### Qué se quita, archivo por archivo

- `templates/base.html`: el `<script>` de `cdn.tailwindcss.com`, el `tailwind.config`, los tres
  `<link>` de Google Fonts.
- `templates/_desplegable.html`: el desplegable propio. Vuelve el `<select>` nativo, así que el
  archivo se elimina.
- `static/img/login-akihabara.jpg`: la foto del inicio de sesión. Se elimina.
- De `base_publico.html`: glitch, grano, ticker, halftone, barrido entre vistas, fondo fotográfico
  con velos, cuadrícula animada, fondos duotono. De `base_operativo.html`: los `@keyframes` del
  loader y de la capa de carga, las transiciones del menú y el estilo del `select` con flecha
  propia. De `_botones.html`: barras que crecen, subrayados que entran, la copia en `data-texto`
  y los paralelogramos. De `_campos.html` y `_casilla.html`: la casilla con `clip-path`, el
  interruptor sesgado y la inversión del ícono del almanaque.
- Los guiones que sólo manejaban efectos: el barrido, el glitch y el repintado de texto. Los
  guiones con función se conservan: selector de etiquetas, control de ámbito, catálogo al vuelo,
  tabla filtrable, vista previa de imagen, autocompletado, ver contraseña y aviso de sesión.

### Qué se conserva y se vuelve a dibujar

Todo lo que lista «Qué se conserva» de `identidad_visual.md`, con los mismos nombres de clase y
de parcial: la jerarquía `.boton-primario` / `.boton-seccion` / `.boton-menor` / `.boton-texto` y
sus variantes, `_campo.html`, `_campos.html`, `_casilla.html`, `_archivo.html`, `_etiquetas.html`,
`_selector_etiquetas.html`, `_ambito.html`, `_catalogo_rapido.html`, `_tabla_filtrable.html`,
`_menu_lateral.html`, `_iconos.html`, `_loader.html`, `_boton_texto.html`, `_aviso_de_duplicado.html`,
`_autocompletado.html` y `_ver_contrasena.html`.

### La prueba del estilo

`test_estilo_preliminar.py` recorre la hoja estática y todas las plantillas (`templates/` y
`apps/*/templates/`), y falla si encuentra:

| Qué | Cómo se detecta |
| --- | --- |
| `animation`, `transition`, `@keyframes` | Propiedad o regla presente |
| `clip-path` | Propiedad presente |
| `border-radius` distinto de `0` | Propiedad con un valor que no es `0` ni `var(--radio)` |
| `box-shadow`, `text-shadow` | Propiedad con un valor que no es `none` ni `var(--sombra)` |
| Gradientes | `linear-gradient`, `radial-gradient`, `conic-gradient` |
| Fuentes web | `@import`, `@font-face`, `fonts.googleapis`, `fonts.gstatic` |
| Filtros y efectos | `filter`, `backdrop-filter`, `transform` y `background-image` con `url(` |
| Colores fuera de los tokens | Cualquier `#hex`, `rgb(`, `rgba(`, `hsl(` o nombre de color fuera del bloque `:root` que declara los seis tokens. Se admiten `transparent`, `currentColor`, `inherit` y `var(--…)` |
| Valores literales en plantillas | Un atributo `style=""` con color, tamaño o espaciado, o un bloque `<style>` en una plantilla |
| Recursos externos de estilo | Cualquier `<script>` o `<link>` a un CDN |

Además verifica que los seis colores de `TOKENS_VISUALES.md` estén declarados una sola vez y con
su valor exacto. Y que las variables `--tienda-*` sólo aparezcan en `base_publico.html` y en la
parte pública de la hoja, nunca en `base_operativo.html` ni en parciales del modo operativo.

Las pruebas actuales que dependen de lo retirado se revisan una por una:

| Prueba | Qué verifica | Qué pasa |
| --- | --- | --- |
| `test_el_boton_de_texto_lleva_su_copia_para_el_barrido` | Un efecto | Se reemplaza por la regla nueva: `_boton_texto.html` no lleva `data-texto` |
| `test_el_paralelogramo_vive_solo_donde_hay_filas` | Un comportamiento, con nombre de efecto | Se conserva la regla, que `identidad_visual.md` mantiene: `.boton-menor` sólo donde hay filas. Cambia el nombre |
| `test_el_desplegable_propio_no_toca_los_multiples` | Un control retirado | Se reemplaza: el formulario dibuja un `<select>` nativo |
| Las que buscan `signal`, `azure`, `font-display` y otras clases viejas en `test_inventario.py`, `test_alta_*`, `test_edicion_producto.py`, `test_parametros.py`, `test_registro_cliente.py`, `test_listado_usuarios.py`, `test_diagnostico_llm.py`, `test_pipeline_de_novedades.py`, `test_remitentes.py`, `test_cotizaciones.py` | En la mayoría, que un significado se marca (stock bajo, valor calculado, error) | Se conserva el significado y cambia la señal, según la tabla «Lo que antes decía el color» |

---

## 2. Conceptos que toca

Ninguno del modelo de dominio. `IdentidadVisual` no existe todavía: hasta `CU-CFG-VIS`, las
cuatro variables `--tienda-*` toman sus valores iniciales de los tokens.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | «Ninguna plantilla escribe un color, un tamaño ni un espaciado literal» | **(a)** Se retira Tailwind y todo se dibuja con una hoja estática de componentes. **(b)** Se conserva Tailwind con un tema reducido a los tokens (`bg-papel`, `p-esp-4`). **Recomiendo (a).** Una clase `px-4` es un espaciado literal escrito en la plantilla. Con (b) los tokens se declaran dos veces, en CSS y en la configuración de Tailwind, y la interfaz depende de un guion de un CDN que corre en el navegador. | Confirmación. Cambia el tamaño del trabajo: con (a) se reescribe el marcado de las 77 plantillas |
| 2 | `identidad_visual.md`, modo público: «El encabezado muestra el nombre y el logo de la tienda; el pie, los datos de contacto y las redes» | Esos datos son de `IdentidadVisual`, que no existe hasta `CU-CFG-VIS`. **(a)** Hasta entonces el encabezado dice «Longbox» sin logo y el pie queda vacío. **(b)** Se inventan valores de contacto provisionales. **Recomiendo (a)** | Confirmación |
| 3 | Pilas tipográficas de `TOKENS_VISUALES.md` | Cada `--texto-*` junta tamaño, peso e interlineado. Se declaran como el valor del atajo `font` sin familia (`--texto-base: 400 16px/1.5`) y se combinan con la familia en la hoja. No cambia ningún valor | Nada, salvo objeción |
| 4 | El aviso de vencimiento de sesión (barra fija inferior) | No aparece en `identidad_visual.md`. Se lo trata como un **Mensaje** de tipo «Atención:», fijo al pie | Confirmación |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | La prueba del estilo, en rojo | — | Primero la regla. Su lista de fallas es el inventario exacto de lo que hay que retirar |
| 2 | Hoja estática con tokens, cáscaras y parciales compartidos | 1 | Los parciales los usan todas las pantallas |
| 3 | Pantallas del modo público: inicio de sesión, registro, recuperación, activación, política de privacidad, tienda | 2 | Son pocas y fijan el uso de `--tienda-*` |
| 4 | Pantallas del modo operativo, app por app: `accounts`, `core`, `suppliers`, `catalog` | 2 | `catalog` al final: es la más grande, con el alta de lotes de 861 líneas |
| 5 | Ajuste de las pruebas que dependían de lo retirado | 3, 4 | Según la tabla del apartado 1 |
| 6 | Borrado de los archivos sin uso y revisión a mano de cada pantalla en los dos modos | 5 | La prueba no ve si una pantalla se entiende; la revisión sí |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Romper un comportamiento al cambiar el marcado | Guiones que buscan elementos por clase (selector de etiquetas, tabla filtrable, catálogo al vuelo) | Los nombres de clase con función se conservan. Las pruebas de comportamiento existentes corren sin cambios |
| Perder una señal que hoy sólo da el color | Stock bajo, valor calculado, error, rol, pantalla actual | La tabla «Lo que antes decía el color» es exhaustiva y cada fila tiene una prueba que busca el texto o el atributo, no el color |
| Volumen | 77 plantillas, 10 000 líneas de marcado | Se trabaja app por app y la suite corre al terminar cada una |
| La prueba se vuelve frágil | Un hallazgo falso en un comentario o en un SVG | Se excluyen los comentarios de plantilla y los atributos `stroke`/`fill` con `currentColor` o `none` |

---

## 6. Fuera de alcance

- El diseño definitivo. No se adelanta ninguna decisión.
- Las pantallas que todavía no existen (tienda, carrito, banners, FAQ). Nacen con este estilo
  cuando se construyan.
- La edición de `IdentidadVisual`. Eso es `CU-CFG-VIS`; acá sólo quedan declaradas las cuatro
  variables con sus valores iniciales.
