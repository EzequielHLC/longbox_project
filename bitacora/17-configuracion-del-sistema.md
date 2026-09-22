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
