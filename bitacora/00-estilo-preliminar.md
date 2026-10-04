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

---

### B-00-005 · Viñeta Nocturna reemplaza al estilo preliminar plano

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** todas las pantallas
**Estado:** Abierta — documentos nuevos del responsable del 2026-10-02; lo que falta está abajo

**Qué apareció.**
El responsable reemplazó `TOKENS_VISUALES.md` e `identidad_visual.md` y sumó `tokens.css` y
`RECURSOS_VISUALES.md`. B-00-001 a B-00-004 quedan sin efecto: describían el estilo anterior.

**Qué dice la especificación.**
> «**Viñeta Nocturna** reemplaza al estilo preliminar plano.» (`TOKENS_VISUALES.md`)

**Qué se hizo.**
`static/css/tokens.css` es copia exacta de `.contexto-ia/tokens.css`, y una prueba lo vigila. Las
fuentes están autoalojadas en `static/fuentes/`. `longbox.css` se reescribió sobre los semánticos,
con los mismos nombres de clase, los cuatro niveles de botón, la capa de corte, las sombras duras y
las diecisiete animaciones del catálogo. La prueba del estilo preliminar se reemplazó por
`test_estilo_vineta.py`: tokens idénticos, fuentes presentes, ningún color ni radio en los
componentes, sombras sin desenfoque, animaciones sólo del catálogo, movimiento reducido declarado,
la tienda leída sólo en el público y el sticker fuera del mostrador.

Quedan sin construir del documento: el menú plegado (`--ancho-menu-plegado`), la cifra que cuenta
desde 0, `destello-fila` conectado a las filas recién guardadas, el `barrido-diagonal` entre
páginas con `view-transition-name` por portada, y la pantalla partida en diagonal del inicio de
sesión y el registro.

**Qué habría que cambiar.**
`identidad_visual.md`: nada. `CLAUDE.md`: el apartado «Diseño visual» que sugiere
`RECURSOS_VISUALES.md`, si el responsable quiere sumarlo.

---

### B-00-006 · La imagen de fondo de la tienda sigue disponible con Viñeta Nocturna

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-VIS`, `CO-131`
**Estado:** Abierta

**Qué apareció.**
`TOKENS_VISUALES.md` declara `--tienda-fondo` como color. El responsable decidió el 2026-09-30 que
el fondo de la tienda puede ser una imagen (C-07), y está construido.

**Qué dice la especificación.**
> «`--tienda-fondo` · `--noche` · El fondo de las superficies noche públicas» (`TOKENS_VISUALES.md`)

**Qué se hizo.**
Se conserva la variable `--tienda-fondo-imagen`, que la hoja de la tienda sólo declara cuando el
Administrador eligió fondo de imagen. Sin elegirlo, la tienda se ve exactamente como el documento.
Además, al guardar se rechazan el secundario o el acento con menos de 4,5:1 contra el fondo, y el
texto sobre el primario lo elige el sistema, como pide `identidad_visual.md`.

**Qué habría que cambiar.**
`TOKENS_VISUALES.md`, Identidad configurable: sumar el fondo de imagen, o confirmar que se retira.

---

### B-00-007 · La guía `Viñeta Nocturna.html` se aplica como referencia de composición

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** todas las pantallas
**Estado:** Abierta

**Qué apareció.**
El responsable dejó `.contexto-ia/Viñeta Nocturna.html`, una maqueta del sistema con la portada,
los botones, la estantería y el mostrador. Lo construido seguía los documentos pero no la
composición de la maqueta.

**Qué dice la especificación.**
La maqueta no figura en `TOKENS_VISUALES.md` ni en `identidad_visual.md`; donde difiere de ellos,
mandan los documentos normativos.

**Qué se hizo.**
- **Rótulos de estado:** borde y texto en el color funcional. Disponible y Activo en lima,
  Pre-venta en celeste, atención en naranja, apagado en humo. Sobre papel queda sólo la palabra.
- **Mensajes:** el prefijo y el ícono van en el color de su tipo.
- **Valores calculados:** en celeste con «ƒ» y borde de trazos.
- **Tablas:** la fila bajo el puntero lleva la barra en la primera celda.
- **Menú del mostrador:** los títulos de grupo pasan a ser rótulos.
- **Encabezado operativo:** el rol va en un rótulo con borde.
- **Tienda:**
  - El menú va sin íconos y con la barra sesgada del actual.
  - La marca lleva un rombo.
  - Los botones del escaparate miden 48 px de alto con 24 px de relleno.
  - El ticker va inclinado con bordes negros.
  - Los rótulos de las tarjetas van en blanco, en cinta o en noche.
  - La estantería entra en diagonal.
  - El globo tiene cola doble.
  - El pie lleva su cinta.
- **Importes:** se escriben «$ 18.500», con punto de miles y sin «,00».

Donde la maqueta usaba un tamaño que no está en la escala, se usó el token más cercano: el título
de tarjeta es `--pub-titulo-3`, como manda `TOKENS_VISUALES.md`.

**Qué habría que cambiar.**
`identidad_visual.md`, Indicadores: nombrar los colores de cada rótulo de estado y el formato
«$ 18.500» de los importes, que hoy sólo muestra la maqueta.

---

### B-00-008 · Los correos salen por SMTP, con copia en la consola y con el estilo del sistema

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-USR-ALT`, `CU-CLI-ALT`, `CU-AUT-INI`,
`CU-AUT-REC`, `CU-RST-PED`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-02

**Qué apareció.**
Los cinco correos del sistema (activación, bienvenida, aviso de bloqueo, recuperación de contraseña
y pedido a proveedor) se imprimían en la consola y no salían. El responsable pidió que se envíen
de verdad, que la copia en la consola siga, y que el correo tenga el estilo visual del sistema.

**Qué dice la especificación.**
Las fichas dicen que el sistema «envía un correo»; sobre su formato visual: `Nada`.

**Qué se hizo.**
- **Envío:** el backend `apps.core.mail.CorreoConCopia` imprime la copia (cabeceras y texto plano,
  donde están los enlaces) y después manda por SMTP. Sin `EMAIL_HOST` el correo queda sólo en la
  consola. Un fallo del servidor levanta, así el pedido a proveedor sigue reintentando tres veces.
  La configuración pasó a `base.py`, con un tiempo de espera de 15 s.
- **Dos versiones:** cada correo lleva el texto plano de siempre y una alternativa HTML con el
  mismo enlace. El cliente de correo elige cuál mostrar.
- **Estilo:** fondo noche, panel asfalto con borde duro en naranja, rombo y nombre de la tienda,
  cinta de peligro en celdas, botón naranja con texto noche, antetítulo en mono y aviso de bloqueo
  con prefijo en alarma. El pedido va en tabla, con ISBN en mono y total.
- **Excepción a la regla de estilos:** los correos son las únicas plantillas con `style=`, porque un
  cliente de correo no lee hojas, variables, `clip-path` ni degradés. Los estilos salen todos de
  `apps/core/templatetags/correo.py` y una prueba verifica que sus colores sean los de
  `tokens.css`. Las fuentes no viajan: Archivo y JetBrains Mono se usan si el lector las tiene.

**Qué habría que cambiar.**
`identidad_visual.md`: una sección «Correo» con la adaptación de arriba. Las fichas que envían
correo pueden remitir a ella.

---

### B-00-009 · Desplegables y barras de desplazamiento con el diseño del sistema

**Tipo:** Agregado · **Fecha:** 2026-10-04 · **Alcance:** todas las pantallas
**Estado:** Abierta — pedido explícito del responsable el 2026-10-03

**Qué apareció.**
El responsable pidió que los desplegables y las barras de desplazamiento tengan diseño propio y no
el del navegador. El desplegable cerrado ya lo tenía; la lista que se abre y las barras, no.

**Qué dice la especificación.**
`TOKENS_VISUALES.md` no dibuja ni la lista abierta de un desplegable ni las barras de desplazamiento.

**Qué se hizo.**
- **Lista del desplegable:** borde duro, fondo del panel, sombra de golpe y la opción elegida en el
  acento, con un rombo como marca. Usa `appearance: base-select`, que hoy admiten Chrome y Edge;
  en los demás navegadores queda la lista nativa y nada se rompe.
- **Barras de desplazamiento:** angostas, en los colores del sistema y con el acento al pasar el
  puntero.

**Qué habría que cambiar.**
`TOKENS_VISUALES.md`: el desplegable abierto y las barras de desplazamiento.
