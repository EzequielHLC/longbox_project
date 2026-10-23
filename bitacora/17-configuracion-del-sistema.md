# Bitácora — `17` Configuración del Sistema

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-17-001 · El diagnóstico del modelo se construyó declarándose fuera de todo caso de uso, y trae contenido de prueba propio

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-CFG-LLM`, `CO-149`, `CO-150`
**Estado:** Resuelta — no hay vacío; enmienda pendiente en las Notas, el 2026-09-22

**Qué apareció.**
La ruta del diagnóstico lleva escrito en `apps/suppliers/urls.py` que es «herramienta de operación,
no de ningún CU». El esquema vigente lo describe: `CU-CFG-LLM` · Diagnosticar el Servicio de Modelo
de Lenguaje, con `CO-149 ejecutarDiagnosticoDelModelo`, `CO-150 verificarDisponibilidadDelModelo` y
`CO-214 consultarConfiguracionDeDiagnostico`.

Hay además una diferencia de alcance que el contrato no resuelve. La pantalla no sólo ejecuta el
diagnóstico: trae un **banco de muestras propio** (`apps/suppliers/muestras.py`) que fabrica
correos de novedades de mentira —con ISBN inventados a propósito— para dárselos al modelo y ver
qué entiende. El contrato no dice si el contenido de prueba lo provee el sistema o lo pega el
Administrador.

**Qué dice la especificación.**
> `CU-CFG-LLM` · Diagnosticar el Servicio de Modelo de Lenguaje — 17 Configuración del Sistema.

Existe. Sobre el origen del contenido de prueba, `CO-149` no dice nada.

**Qué se hizo.**
El banco de muestras vive en `apps/suppliers/muestras.py` y no en `apps/catalog/isbn.py`, que sólo
verifica ISBN y nunca los genera. La separación es deliberada y está anotada en el propio módulo:
un generador de ISBN al alcance del código de catálogo termina completando el ISBN que falta en un
borrador, y un ISBN inventado es matemáticamente válido y no identifica nada.

**Qué habría que cambiar.**
`CO-149`, campo Precondiciones o Notas: declarar de dónde sale el contenido con el que se
diagnostica. Si el banco de muestras es parte del caso de uso, decirlo; si el Administrador debe
pegar un correo real, decir eso, porque entonces el banco sobra.

---

### B-17-002 · La baja de los catálogos de parámetros es una casilla, y los contratos declaran un par solicitar/confirmar

**Tipo:** Desvío · **Fecha:** 2026-09-14 · **Alcance:** `CU-CFG-EDT`, `CU-CFG-TIP`, `CU-CAT-ETQ`
**Estado:** Resuelta — desvío confirmado; manda el contrato, decidido el 2026-09-22

**Nota sobre el tipo.** Como en `B-12-001`, se registra después porque no se tomó como desvío: el
código es anterior a la existencia de los contratos.

**Qué apareció.**
Las seis pantallas de catálogos de parámetros —editorial, grupo de etiqueta, etiqueta, tipo,
formato y tabla de precios— comparten una misma vista genérica (`ParametroFormularioMixin`) que
guarda, audita y vuelve. Dar de baja cualquiera de ellos es destildar una casilla `activa` /
`activo` dentro del formulario de edición, en un solo paso y sin informe previo.

Los contratos declaran otra cosa: `CO-139`/`CO-140` para editorial, `CO-147`/`CO-148` para formato,
`CO-040`/`CO-041` para grupo de etiqueta y `CO-044`/`CO-045` para etiqueta son **pares
solicitar/confirmar**, y el primero de cada par existe para mostrar el impacto antes de que la baja
ocurra.

**Qué dice la especificación.**
> `CO-040 solicitarBajaDeGrupoDeEtiqueta` / `CO-041 confirmarBajaDeGrupoDeEtiqueta`
> `CO-139 solicitarBajaDeEditorial` / `CO-140 confirmarBajaDeEditorial`
> `CO-147 solicitarBajaDeFormato` / `CO-148 confirmarBajaDeFormato`

El patrón es el mismo que la baja de producto y la de proveedor, que sí están construidas con dos
pasos e informe de impacto.

**Qué se hizo.**
Quedó la casilla. La pantalla de edición de editorial avisa en su descripción que desactivarla la
saca de los desplegables de alta pero conserva sus productos y su historial, así que la
consecuencia está dicha; lo que no hay es la cifra de cuántos elementos quedan afectados, que es lo
que el informe de impacto aporta a la decisión.

**Qué habría que cambiar.**
Nada en el documento: los contratos están bien y el código es el que se aparta. Está registrado
como `Parcial` en `docs/ESTADO.md` para `CU-CFG-EDT`, `CU-CFG-TIP` y `CU-CAT-ETQ`. Lo que conviene
decidir es si el par solicitar/confirmar se construye para los seis catálogos de una vez —comparten
vista, así que se hace una sola— o caso de uso por caso de uso.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-17-001 · Resolución de B-17-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** pendiente (de redacción)

**Qué se decidió.**
**No hay vacío de especificación.** El **paso 2 de `CU-CFG-LLM`** ya declara que el contenido de
prueba lo provee el sistema: el banco de muestras es parte del caso de uso, no un agregado. La
entrada buscó la respuesta en `CO-149` y ahí no está, pero la ficha sí la tiene.

Es la situación que `CLAUDE.md` describe cuando dice que la ficha y el contrato no dicen lo mismo
y hacen falta los dos: el contrato declara el efecto y la ficha narra el flujo, y de dónde sale el
contenido con el que se diagnostica es parte del flujo.

La separación entre `apps/suppliers/muestras.py` y `apps/catalog/isbn.py` se confirma tal cual
está, y por el motivo que la entrada da: un generador de ISBN al alcance del código de catálogo
termina completando el ISBN que falta en un borrador, y un ISBN inventado es matemáticamente
válido y no identifica nada.

**Enmienda pendiente.**
`CO-149`, campo Notas: remitir al paso 2 de la ficha para el origen del contenido de prueba. Es
redacción, no alcance — evita que el próximo que lea sólo el contrato vuelva a abrir esta misma
pregunta.

**Qué se hizo.**
`DiagnosticoLLMView` y su plantilla dejaron de declararse fuera de todo caso de uso: citan
`CU-CFG-LLM` con `CO-149`, `CO-150` y `CO-214`, y dicen que el banco de muestras es el contenido
de prueba que el paso 2 declara.

---

### R-17-002 · Resolución de B-17-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna · **Tipo confirmado:** Desvío

**Qué se decidió.**
**Manda el contrato.** La baja de un catálogo de parámetros es un par solicitar/confirmar con
informe de impacto, no una casilla dentro del formulario de edición. Es el mismo patrón que la
baja de producto y la de proveedor, que ya están construidas así.

Y se decide la pregunta que la entrada dejaba abierta: **el par se construye una sola vez para los
seis catálogos**. Comparten `ParametroFormularioMixin`, así que construirlo caso de uso por caso
de uso sería escribir seis veces la misma vista y dejar que diverjan.

**Qué se hizo.**
Nada todavía. El trabajo **va al plan del módulo 17**, organizado por contrato y no por caso de
uso: los `Gestionar`/`Administrar` se van a separar en alta, baja y modificación, y una
reconciliación organizada por caso de uso quedaría invalidada cuando eso llegue.

---

### B-17-003 · El intervalo del carrusel es un parámetro que el modelo de dominio todavía no declara

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** `CU-CFG-PAR`, `CU-CFG-BNC`, `CO-130`
**Estado:** Abierta — decidido; falta la enmienda del modelo, anunciada para la sección 5

**Qué apareció.**
La ficha de `CU-CFG-PAR` ya lista la sección Tienda con el intervalo de rotación del carrusel, y
`CU-CFG-BNC` dice que la portada alterna los banners «con el intervalo que fija CU-CFG-PAR».
`ConfiguracionSistema`, en `MODELO_DE_DOMINIO.md`, no tiene el atributo.

**Qué dice la especificación.**
> «Tienda: intervalo de rotación del carrusel de banners, en segundos (entero ≥ 1).»
> (`CU-CFG-PAR`, paso 2)

El modelo de dominio: `Nada`.

**Qué se hizo.**
Se agrega el atributo a `ConfiguracionSistema`, entero de 1 en adelante, editable desde
Parámetros globales. **Valor inicial: 10 segundos, fijado por el responsable** el 2026-09-30
(consulta C-05).

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 7, `ConfiguracionSistema`: agregar «--- Tienda --- intervalo del
carrusel (s) : entero ≥ 1 «default 10»».

---

### B-17-004 · «Aplica a todos los tipos» es un atributo de Formato

**Tipo:** Corrección · **Fecha:** 2026-09-30 · **Alcance:** `CU-CFG-FMA`, `FMM`, `FMC`, `TPA`, `TPM`, `CO-144`, `CO-145`, `CO-146`, `CO-049`
**Estado:** Resuelta en el código — decisión del responsable el 2026-09-30 (consulta C-03). Enmienda pendiente

**Qué apareció.**
Los contratos del formato declaran «f.aplica a todos los tipos» como atributo que se fija y
cambia. El modelo de dominio no lo tiene, y el código lo deducía de la lista vacía de tipos. Con
esa deducción, declarar un formato universal desde un tipo (`CO-146`) lo convertía en particular
sin que nadie lo decidiera.

**Qué dice la especificación.**
> «(c) f.nombre quedó con el valor normalizado, f.medidas y f.aplica a todos los tipos con los
> valores declarados» (`CO-144`, Postcondiciones)

`MODELO_DE_DOMINIO.md`, Área 2, `Formato`: nombre, medidas y activo. Nada más.

**Qué se hizo.**
`Formato` gana el atributo. Una migración marca como «aplica a todos» a cada formato que tenía la
lista de tipos vacía, para que ninguno cambie de alcance al migrar.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 2, `Formato`: agregar «aplica a todos los tipos : sí / no».

---

### B-17-005 · Acciones de auditoría para los catálogos y el contenido de la tienda

**Tipo:** Agregado · **Fecha:** 2026-09-30 · **Alcance:** módulos 02, 03 y 17
**Estado:** Resuelta en el código — el responsable delegó la elección el 2026-09-30 (consulta C-04). Enmienda pendiente

**Qué apareció.**
Las operaciones de alta, modificación y baja de editoriales, tipos, formatos, grupos y etiquetas
se auditaban como «Modificación de parámetros globales», y `CO-130` dice que un catálogo no es un
parámetro. FAQ, identidad visual y banners no tenían ninguna acción aplicable. El enumerado es
cerrado y sólo se amplía declarándolo en el modelo.

**Qué dice la especificación.**
> «El enumerado sigue siendo cerrado: cualquier operación de escritura nueva que se incorpore
> debe declarar su propio valor acá antes de poder auditarse.» (`MODELO_DE_DOMINIO.md`, Área 7,
> nota sobre `RegistroAuditoria`)

Los contratos dicen «una entrada en el registro de auditoría de la operación» y no nombran la
acción.

**Qué se hizo.**
Se agregan estas acciones, con el objeto afectado y los valores anterior y nuevo en el detalle:

| Acción | La usan |
| --- | --- |
| Alta de catálogo | `CO-137`, `CO-141`, `CO-144`, `CO-038`, `CO-042` |
| Modificación de catálogo | `CO-138`, `CO-142`, `CO-145`, `CO-146`, `CO-039`, `CO-043` |
| Baja de catálogo | `CO-140`, `CO-221`, `CO-148`, `CO-041`, `CO-045` |
| Alta de precio de referencia | `CO-049` |
| Baja de precio de referencia | `CO-051` |
| Publicación de FAQ | `CO-135`, `CO-136` |
| Modificación de identidad visual | `CO-131` |
| Alta de banner · Modificación de banner · Baja de banner | `CO-132` · `CO-133` · `CO-134` |

Se suman las tres que el modelo ya declara en INC-06 y el código no tenía: «Modificación de
precio de referencia» (`CO-048`), «Exportación de inventario» (`CO-037`) y «Exportación del log
de auditoría» (`CO-129`). Las entradas que ya existen no se reescriben: el log es inmutable.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 7, nota de INC-06: agregar las once acciones nuevas de la tabla.

---

### B-17-006 · El reparo por un catálogo dado de baja se calcula al mirar el borrador

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-EDB`, `TPB`, `FMB`, `CO-140`, `CO-221`, `CO-148`, `CU-ALT-REV`
**Estado:** Abierta

**Qué apareció.**
La baja de una editorial, un tipo o un formato puede llegar cuando ya hay borradores generados
que los usan, y la reactivación posterior tiene que destrabarlos sin que nadie regenere el
correo.

**Qué dice la especificación.**
> «Desde la baja, la editorial no se asigna a productos nuevos por ninguna vía: deja de ofrecerse
> en los formularios, y un borrador que la hereda de su proveedor registra un reparo y no puede
> confirmarse hasta cambiarla o reactivarla (CO-138).» (`CO-140`, Notas; igual en `CO-221` y `CO-148`)

No dice cuándo se registra el reparo.

**Qué se hizo.**
El reparo no se guarda con el borrador: se calcula cada vez que se lo mira o se lo intenta
confirmar. Aparece en «Datos descartados por el sistema» junto a los demás, nombra el catálogo y
dice qué hacer. La confirmación, individual o en lote, lo excluye con el motivo «Tiene una
editorial, un tipo o un formato dados de baja». Cambiar el dato en el borrador o reactivar el
catálogo lo destraba en el acto.

**Qué habría que cambiar.**
`CO-140`, `CO-221` y `CO-148`, Notas: «registra un reparo» por «presenta un reparo mientras la
entrada siga dada de baja».

---

### B-17-007 · La edición ofrece el valor actual aunque esté dado de baja

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-140`, `CO-221`, `CO-148`, `CO-045`, `CU-CAT-EDI`, `CU-PRV-MOD`, `CU-ALT-REV`
**Estado:** Abierta

**Qué apareció.**
Los formularios de edición de producto, de proveedor y de borrador ofrecían sólo lo activo. Un
producto con una editorial dada de baja no la encontraba entre las opciones: guardar cualquier
otro cambio la perdía o hacía fallar el formulario. Con las etiquetas pasaba lo mismo, y se
perdían en silencio.

**Qué dice la especificación.**
> «Las asociaciones ProductoEditorial → Editorial, Proveedor → Editorial y TablaPrecioReferencia →
> Editorial se conservaron.» (`CO-140`, Postcondiciones)
> «En la edición de un producto que la tiene asignada se presenta marcada y puede quitarse
> (CO-030).» (`CO-045`, Notas)

Para la editorial, el tipo y el formato: `Nada` sobre la edición.

**Qué se hizo.**
La edición ofrece lo activo **más el valor que el registro ya tiene**, esté como esté. Se puede
conservar o cambiar por uno activo; no se puede elegir otro dado de baja. Es la regla de `CO-045`
para las etiquetas, extendida a los tres catálogos que deciden.

**Qué habría que cambiar.**
`CO-140`, `CO-221` y `CO-148`, Notas: agregar que la edición del producto, del proveedor y del
borrador presenta el valor dado de baja y permite conservarlo.

---

### B-17-008 · Las ofertas vigentes del informe de baja de tipo se informan como «No disponible»

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-TPB`, `CO-220`
**Estado:** Abierta — recomendación del plan aplicada sin objeción (consulta C-12)

**Qué apareció.**
El informe de baja de un tipo cuenta las ofertas Programadas o Activas que lo referencian, y
`Oferta` todavía no existe.

**Qué dice la especificación.**
> «Informar cuántos productos, filas de la tabla de precios, proveedores y ofertas Programadas o
> Activas referencian el tipo antes de darlo de baja.» (`CO-220`, Responsabilidades)

**Qué se hizo.**
La cantidad de ofertas se presenta como «No disponible todavía», nunca como 0: un cero diría que
se verificó que no hay ninguna. Es el mismo criterio que `CO-163` pide para los indicadores que
dependen de módulos no construidos. Hasta que exista `Oferta`, la postcondición «Oferta → Tipo se
conservaron» de `CO-221` no se puede ejercer.

**Qué habría que cambiar.**
Nada.

---

### B-17-009 · Desde la carga de un lote, el tipo nuevo es editorial y el formato nuevo se declara para el tipo elegido

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-TPA` A1, `CU-CFG-FMA` A1, `CO-141`, `CO-144`
**Estado:** Abierta

**Qué apareció.**
El alta al vuelo desde la carga de un lote no tiene lugar para el formulario completo: se resuelve
con el nombre y una pregunta de sí o no.

**Qué dice la especificación.**
> «El formato creado queda declarado para el tipo seleccionado en el formulario de carga, salvo
> que se indique que aplica a todos los tipos.» (`CU-CFG-FMA`, A1)

Sobre el rubro del tipo creado desde la carga: `Nada`.

**Qué se hizo.**
El tipo creado desde la carga de un lote toma el rubro editorial, que es el de la pantalla, y
pregunta sólo si se clasifica por formato. El formato pregunta si aplica a todos; si no, queda
declarado para el tipo elegido en la cabecera. Los dos pasan por el mismo formulario, la misma
normalización y la misma auditoría que su pantalla propia.

**Qué habría que cambiar.**
`CU-CFG-TPA`, A1: «El tipo creado desde la carga de un lote es del rubro editorial».

---

### B-17-010 · Los formatos y tipos dados de baja no se desvinculan al editar la lista del otro lado

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-145`, `CO-146`
**Estado:** Abierta

**Qué apareció.**
La declaración de formatos de un tipo sólo ofrece los formatos activos (`CO-146`, precondición), y
la de tipos de un formato sólo los tipos activos que se clasifican por formato (`CO-145`). Uno
dado de baja que ya estaba declarado no aparece en la lista, y guardarla lo habría desvinculado
sin que nadie lo eligiera.

**Qué dice la especificación.**
> «(b) Se formaron las asociaciones Formato ↔ Tipo de la lista declarada y se rompieron las que
> quedaron fuera.» (`CO-146`, Postcondiciones)
> «Las asociaciones ProductoEditorial → Formato, TablaPrecioReferencia → Formato y Formato ↔ Tipo
> se conservaron.» (`CO-148`, Postcondiciones)

**Qué se hizo.**
Lo dado de baja que ya estaba declarado se conserva al guardar la lista: «quedar fuera» se lee
sobre lo que se ofrecía. Coincide con `CO-148`, que conserva Formato ↔ Tipo en la baja.

**Qué habría que cambiar.**
`CO-145` y `CO-146`, Notas: «Las combinaciones con un tipo o un formato dados de baja no se ofrecen
y se conservan».

---

### B-17-011 · El logo no admite SVG: RNF-05 convierte toda imagen a WebP

**Tipo:** Corrección · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-VIS` paso 2, `CO-131`, RNF-05
**Estado:** Abierta — se aplicó la palabra del requisito (consulta C-08)

**Qué apareció.**
La guía de formato del logo recomienda PNG o SVG. RNF-05 pide convertir **toda** imagen que sube
el Administrador a WebP, y un SVG es un dibujo vectorial que no se puede convertir sin
rasterizarlo. Además, un SVG puede llevar guiones adentro y se mostraría en una pantalla pública.

**Qué dice la especificación.**
> «Logo de la tienda (carga de imagen, guía de formato: cuadrado o 2:1 horizontal, PNG o SVG
> recomendado)» (`CU-CFG-VIS`, paso 2)
> «El backend del sistema debe procesar automáticamente toda imagen que suba el Administrador
> —portadas, imágenes de producto, identidad visual y banners—, realizando […] conversión al
> formato WebP» (RNF-05)

**Qué se hizo.**
El logo, el fondo y los banners admiten JPG, PNG y WebP, y se guardan en WebP. Un SVG se rechaza
con el problema específico («El formato SVG no se admite»), como pide la E2 de la ficha.

**Qué habría que cambiar.**
`CU-CFG-VIS`, paso 2: «PNG recomendado» en lugar de «PNG o SVG recomendado».

---

### B-17-012 · Tamaños máximos, calidad de compresión y lado mayor del fondo

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** RNF-05, `CO-131`, `CO-132`, `CO-133`
**Estado:** Abierta — el valor fijo de la calidad estaba anunciado en el plan 17, ambigüedad 10

**Qué apareció.**
Las excepciones de las imágenes hablan de un «tamaño máximo admitido» que nadie fija. RNF-05 pide
una calidad «configurable» que `ConfiguracionSistema` no declara, y no dice qué lado mayor le
corresponde a una imagen de fondo.

**Qué dice la especificación.**
> «redimensionado a unas dimensiones máximas configurables manteniendo la proporción (por defecto
> 800 px en el lado mayor; para los banners, 1920 px) y compresión con nivel de calidad
> configurable» (RNF-05)

**Qué se hizo.**
Peso máximo de lo que se sube: 10 MB para los banners y 5 MB para el resto, el mismo que ya
tenían las portadas. Calidad WebP fija en 80. El logo se reduce a 800 px de lado mayor, y el fondo
a 1920 px como los banners: ocupa la pantalla entera y a 800 px se vería pixelado.

**Qué habría que cambiar.**
RNF-05: declarar el peso máximo por tipo de imagen y el lado mayor del fondo de la tienda. Si la
calidad tiene que ser configurable, `MODELO_DE_DOMINIO.md`, `ConfiguracionSistema`: agregar el
parámetro.

---

### B-17-013 · La portada y las preguntas frecuentes de la tienda

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-132`, `CO-135`, `CU-CFG-BNC`, `CU-CFG-FAQ`
**Estado:** Abierta — decisión del responsable el 2026-09-30 (consulta C-06)

**Qué apareció.**
Los contratos de los banners y de la FAQ dicen que el contenido «quedó publicado en la tienda», y
ningún caso de uso declara la portada ni la página de preguntas frecuentes.

**Qué dice la especificación.**
> «(c) b.imagen quedó con la imagen procesada y b.posición con el valor siguiente al último de la
> galería. El banner quedó publicado en la tienda.» (`CO-132`, Postcondiciones)

**Qué se hizo.**
La portada de la tienda muestra el carrusel, con el intervalo de los parámetros, cambio
instantáneo y los controles «Anterior», «Siguiente» y «Pausar». La página de preguntas frecuentes
muestra lo publicado y es pública: se lee sin iniciar sesión. La portada sigue siendo la de la
cuenta de cliente, como hasta ahora.

**Qué habría que cambiar.**
`CU-CFG-BNC` y `CU-CFG-FAQ`, Comentarios: nombrar las dos pantallas públicas, o asignarlas a
`CU-TDA-CAT`.

---

### B-17-014 · La vista previa de la FAQ es un envío que no guarda

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-FAQ` pasos 2 y 3, `CO-210`
**Estado:** Abierta

**Qué apareció.**
La ficha pide alternar entre edición y vista previa del renderizado. El sistema no carga
bibliotecas de terceros en el navegador, así que el Markdown no se puede renderizar ahí.

**Qué dice la especificación.**
> «El sistema presenta el editor Markdown con el contenido publicado y la alternancia entre modo
> de edición y vista previa del renderizado.» (`CU-CFG-FAQ`, paso 2)

**Qué se hizo.**
El editor tiene un botón «Vista previa» que envía el texto al servidor, lo renderiza con la misma
función que la tienda y lo muestra debajo, sin guardar ni auditar nada. «Descartar cambios» vuelve
a cargar lo publicado.

**Qué habría que cambiar.**
Nada.

---

### Nota de cierre · 2026-10-02

Las dos tandas del plan 17 quedaron construidas. Catálogos: editoriales, tipos y formatos con
pantalla propia, baja con informe y reparo en los borradores. Contenido: FAQ, banners con el
carrusel de la portada e identidad visual, con el procesamiento de imágenes de RNF-05. Queda:
`CU-CFG-PAR` (secciones de módulos no construidos y Seguridad), `CU-CFG-LLM` sin verificar, las
portadas de producto sin procesar (deuda del módulo 01) y las consultas C-20 y C-21.

---

### B-17-015 · Los textos de la portada y del pie se escriben desde la identidad visual

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CFG-VIS`, `CO-131`, `CO-208`
**Estado:** Abierta — pedido explícito del responsable el 2026-10-02

**Qué apareció.**
El título grande de la portada («Historietas de noche»), su antetítulo, la bajada, los mensajes del
ticker y la descripción del pie estaban escritos en la plantilla. El responsable pidió poder
cambiarlos desde la administración.

**Qué dice la especificación.**
> «Datos de la tienda: Nombre de la tienda (texto libre); Email de contacto público; Teléfono o
> WhatsApp de contacto (opcional); Enlace a Instagram, Facebook, TikTok, X/Twitter» (`CU-CFG-VIS`,
> paso 2)

Sobre los textos de la portada: `Nada`.

**Qué se hizo.**
La identidad visual suma una sección «Portada y pie» con el antetítulo, el título, la bajada, los
mensajes del ticker (uno por renglón) y la descripción del pie. Un texto que se deja vacío vuelve a
su valor inicial. Sin mensajes, el ticker anuncia los títulos de lo último que llegó. Los cambios
se auditan con la misma acción y el detalle anterior y nuevo.

**Qué habría que cambiar.**
`CU-CFG-VIS`, paso 2: agregar la sección «Portada y pie». `MODELO_DE_DOMINIO.md`,
`IdentidadVisual`: los cinco atributos.

---

### R-17-003 · Resolución de B-17-008

**Fecha:** 2026-10-03 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Con `Oferta` construida (plan 03, segunda parte), el informe de baja de un tipo cuenta las ofertas
que lo referencian, y la baja las conserva.

**Qué se hizo.**
El informe de `CO-220` presenta la cantidad real de ofertas Programadas o Activas cuyo alcance es
el tipo, según sus fechas: no cuentan las vencidas, las dadas de baja ni las de un producto suelto
de ese tipo. La baja de `CO-221` conserva la asociación Oferta → Tipo y no cambia el estado de la
oferta, que sigue descontando. B-17-008 queda resuelta.

---

### B-17-016 · Un doble clic en el alta de un catálogo terminaba en error 500

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** `CO-137`, `CO-141`, `CO-144`, `CO-038`, `CO-042` (altas de los cinco catálogos)
**Estado:** Resuelta — corregido el código el 2026-10-04, encontrado en el ensayo de la demostración (plan 00, D4-04)

**Qué apareció.**
Dos envíos del mismo nombre a la vez (un doble clic, o dos pestañas) pasaban los dos la validación
del formulario, porque todavía no existía ninguno. El segundo chocaba contra la restricción de
unicidad de la base y respondía **error 500**. El dato quedaba bien (un solo registro), pero el
sistema se rompía mal: en el ensayo, 6 de 10 dobles envíos.

**Qué dice la especificación.**
> E1 de cada alta: el nombre repetido se informa y no se registra.

La especificación es correcta; el código no cubría la carrera.

**Qué se hizo.**
La vista común de los catálogos atrapa el choque de unicidad y devuelve el formulario con el mismo
aviso de duplicado que daría la validación. La prueba (`test_concurrencia_catalogos.py`, editorial
y tipo, diez repeticiones cada uno) se escribió antes y fallaba con el 500.

**Qué habría que cambiar.**
Nada en el documento.

---

### B-17-017 · El alta de un catálogo podía volver sin decir por qué

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** `CO-137`, `CO-141`, `CO-144`, `CO-038`, `CO-042`
**Estado:** Resuelta — corregido el código el 2026-10-04, encontrado al repetir la prueba de B-17-016

**Qué apareció.**
Con el doble clic corregido, la prueba falló una de cada tres corridas por otro lado. Si el otro
envío se guardaba entre la consulta de duplicados del formulario y la validación del modelo, el
choque lo detectaba la restricción de unicidad del modelo, con un error general redactado con su
nombre técnico («No se cumple la restricción editorial_unica_por_nombre»). Y la pantalla de los
catálogos **no mostraba los errores generales**: el formulario volvía sin ninguna explicación.

**Qué dice la especificación.**
> E1 de cada alta: el nombre repetido se informa.

**Qué se hizo.**
- El formulario de los catálogos traduce ese caso al aviso de duplicado de siempre, con el enlace al
  registro existente.
- La pantalla de los catálogos muestra los errores generales, para que ningún otro rechazo vuelva
  sin texto.

**Qué habría que cambiar.**
Nada en el documento.

---

### B-17-018 · El diagnóstico del modelo no quedaba en el log, y la disponibilidad no era una acción propia

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-CFG-LLM` paso 6, A2 y E4, `CO-149`, `CO-150`, `CO-214`
**Estado:** Abierta

**Qué apareció.**
Al escribir las pruebas de contrato (V2 del plan 00): ni el diagnóstico ni la comprobación de
disponibilidad dejaban entrada en el log. La disponibilidad se consultaba sola en cada carga de la
pantalla, sin una acción que el Administrador ejecutara. Y cuando el modelo configurado no estaba
en el servidor, la pantalla lo decía pero no listaba los que sí estaban.

**Qué dice la especificación.**
> «Se creó una entrada en el registro de auditoría con el resultado del diagnóstico y la
> configuración vigente al momento de ejecutarlo (modalidad, dirección del servicio y modelo), sin
> incluir la credencial.» (`CO-149`) · «Se creó una entrada en el registro de auditoría con el
> resultado.» (`CO-150`) · Ninguno de los dos nombra la acción.

**Qué se hizo.**
- Dos acciones nuevas en el log: «Diagnóstico del modelo de lenguaje» y «Comprobación de
  disponibilidad del modelo de lenguaje». Las dos registran el resultado —en línea, rechazado con
  su código, sin respuesta, ininterpretable, o cuántos productos y cuántos con reparos— con la
  modalidad, la dirección y el modelo. La credencial no aparece, ni enmascarada.
- «Comprobar disponibilidad» es un botón del panel de estado (A2): no gasta inferencia y queda
  en el log. El estado que se ve al abrir la pantalla se sigue consultando solo y **no** se
  registra: es parte de presentar la configuración (`CO-214`), y registrarlo llenaría el log con
  una entrada por cada visita.
- E4: con el modelo configurado ausente, los que el servidor ofrece se listan plegados. Un
  proveedor remoto declara cientos y la lista abierta tapaba el resto de la pantalla.

**Qué habría que cambiar.**
`CO-149` y `CO-150`: nombrar las acciones del log. `CU-CFG-LLM` paso 2: anotar que la pantalla
muestra el estado del servicio al abrirse, sin registrarlo.

---

### B-17-019 · La identidad visual tiene un mapa de colores, y cada color trae su familia

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-CFG-VIS`, `CO-131`, `CO-208`
**Estado:** Abierta — pedido del responsable (plan 00 de interfaz, cuarta parte, A y B)

**Qué apareció.**
Cambiar el acento de la tienda a azul dejaba en naranja el hover, la selección, las sombras de las
tarjetas, la cinta del pie y los rótulos de pre-venta: esas variantes salían de la paleta fija y
no del color elegido. Y no había forma de saber qué partes de la tienda pintaba cada color.

**Qué dice la especificación.**
> «Paleta de colores: Color primario (HEX), Color secundario (HEX), Color de acento (HEX)»
> (`CU-CFG-VIS`, paso 2). Nada sobre qué pinta cada uno.

**Qué se hizo.**
- **Familias de color.** Cada color elegido trae sus variantes: más claro para el hover, más
  oscuro para lo presionado, tenue para lo seleccionado. El texto encima de cada color es noche o
  blanco, el que más contraste dé, y un color que no llega a 3:1 sobre el fondo no se usa como
  texto. El backoffice no cambia: su paleta sigue fija (P-07).
- **Mapa de colores.** Siete partes de la tienda, cada una con un selector entre los colores de la
  paleta: botón principal, botones secundarios y enlaces, precios, rótulos y carteles, títulos de
  sección, tarjetas e imágenes, encabezado y pie. Los precios, los títulos y las tarjetas admiten
  además «Neutro»; el encabezado y el pie, «Fondo». Las opciones las valida el servidor.
- **Los valores iniciales reproducen la tienda tal como se veía**, y no la «propuesta inicial» del
  plan: sin tocar el mapa, nada cambia de lugar.
- Con el encabezado y el pie en un color, su texto y sus acentos pasan al de contraste; el
  buscador conserva los suyos.

**Qué habría que cambiar.**
`CU-CFG-VIS` paso 2: agregar el mapa de colores a la sección Apariencia. `CO-131`: los siete roles
en la firma (`colores` pasa a incluir el mapa). `CO-208`: presentarlos.
