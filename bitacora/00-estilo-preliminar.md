> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `00` Estilo preliminar

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-00-001 · La interfaz deja de depender de Tailwind y de un CDN

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** todas las pantallas
**Estado:** Resuelta — decisión del responsable el 2026-09-30 (consulta C-01)

**Qué apareció.**
Toda la interfaz se dibujaba con clases utilitarias de Tailwind, cargado en el navegador desde
`cdn.tailwindcss.com`. Una clase como `px-4` o `text-sm` es un espaciado o un tamaño literal
escrito en la plantilla.

**Qué dice la especificación.**
`Nada.` `TOKENS_VISUALES.md` dice que ninguna pantalla inventa un valor, pero no dice con qué
herramienta se aplican los tokens.

**Qué se hizo.**
Se retira Tailwind. Una sola hoja estática, `static/css/longbox.css`, declara los tokens como
variables CSS y los componentes por nombre de clase. La interfaz ya no pide nada a un servidor
ajeno para dibujarse.

**Qué habría que cambiar.**
Nada.

---

### B-00-002 · El encabezado público no tiene de dónde sacar el nombre, el logo ni el contacto

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** modo público, `CU-CFG-VIS`
**Estado:** Resuelta — recomendación del plan, sin objeción del responsable (consulta C-02)

**Qué apareció.**
`identidad_visual.md` dice que el encabezado público muestra el nombre y el logo de la tienda, y
el pie, los datos de contacto y las redes. Esos datos son de `IdentidadVisual`, que no existía.

**Qué dice la especificación.**
> «El encabezado muestra el nombre y el logo de la tienda; el pie, los datos de contacto y las
> redes.» (`identidad_visual.md`, Modo público)

**Qué se hizo.**
Mientras no haya identidad guardada, el encabezado dice «Longbox» sin logo y el pie queda vacío.
Cuando existe, se usan sus datos.

**Qué habría que cambiar.**
Nada.

---

### B-00-003 · El aviso de vencimiento de sesión se dibuja como un mensaje de atención

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** `CU-AUT-INI`
**Estado:** Resuelta — recomendación del plan, sin objeción del responsable (consulta C-02)

**Qué apareció.**
La barra fija que avisa que la sesión está por expirar no figura en `identidad_visual.md`.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Se dibuja como un **Mensaje** de `identidad_visual.md`, precedido por «Atención:», fijo al pie de
la pantalla, con borde superior `--borde-fuerte`.

**Qué habría que cambiar.**
`identidad_visual.md`, Indicadores: agregar el aviso de sesión, si se quiere que quede escrito.

---

### B-00-004 · El modo operativo deja de ser compacto: más aire, filetes e iconos de trazo

**Tipo:** Desvío · **Fecha:** 2026-09-30 · **Alcance:** modo operativo, todas las pantallas
**Estado:** Resuelta — pedido explícito del responsable el 2026-09-30. Enmienda pendiente

**Qué apareció.**
La primera versión del estilo seguía la densidad compacta de los tokens y las pantallas se
leían amontonadas. El responsable pidió «un sistema plano y simple, pero no descuidado», con
separadores, tablas, líneas e iconos, inspirado en los lectores de libros electrónicos.

**Qué dice la especificación.**
> «Densidad compacta: tablas en `--texto-chico`, separación entre bloques `--esp-3`.»
> (`identidad_visual.md`, Modo operativo) · «Compacta: `--esp-3` entre bloques»
> (`TOKENS_VISUALES.md`, Los dos modos)

**Qué se hizo.**
Sin agregar ningún valor nuevo: todo sale de los tokens existentes. Las secciones de una
pantalla se separan con `--esp-6` y llevan un título con filete `--borde-fuerte`. El título de
la pantalla lleva un filete debajo. Las fichas de datos van un dato por renglón, separados por
`--gris-linea`. Los filtros van en una barra entre dos filetes. Los estados van en una marca
encerrada. Los botones, el menú y los mensajes llevan iconos de trazo en `currentColor`, siempre
junto a un texto que dice lo mismo.

**Qué habría que cambiar.**
`TOKENS_VISUALES.md`, «Los dos modos», y `identidad_visual.md`, «Modo operativo»: la
separación entre bloques pasa a `--esp-6` para secciones y `--esp-4` dentro de una sección. Y
agregar a `identidad_visual.md` los componentes nuevos: encabezado de pantalla con filete,
título de sección, barra de herramientas, ficha de datos por renglones y marca de estado.
