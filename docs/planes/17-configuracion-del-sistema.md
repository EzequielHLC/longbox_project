> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `17` Configuración del Sistema

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Dos tandas del mismo módulo, en momentos distintos de la etapa A:

- **Tanda 1: catálogos de clasificación.** Editoriales, tipos de material y formatos. Va
  inmediatamente después del estilo preliminar.
- **Tanda 2: contenido de la tienda.** FAQ, identidad visual y banners. Va al final de la
  etapa A.

`CU-CFG-PAR` y `CU-CFG-LLM` no se cierran en esta sesión. De `CU-CFG-PAR` sólo entra el parámetro
del intervalo del carrusel, que los banners necesitan.

---

## 1. Qué cubre

### Tanda 1

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CFG-EDC` | `CO-211` | 0 | 1 |
| `CU-CFG-EDA` | `CO-137`, `CO-211` | 1 | 1 |
| `CU-CFG-EDM` | `CO-138`, `CO-211` | 1 | 1 |
| `CU-CFG-EDB` | `CO-139`, `CO-140`, `CO-156`, `CO-211` | 1 | 3 |
| `CU-CFG-TPC` | `CO-212` | 0 | 1 |
| `CU-CFG-TPA` | `CO-141`, `CO-146`, `CO-212` | 2 | 1 |
| `CU-CFG-TPM` | `CO-142`, `CO-146`, `CO-212` | 2 | 1 |
| `CU-CFG-TPB` | `CO-220`, `CO-221`, `CO-156`, `CO-212` | 1 | 3 |
| `CU-CFG-FMC` | `CO-213` | 0 | 1 |
| `CU-CFG-FMA` | `CO-144`, `CO-213` | 1 | 1 |
| `CU-CFG-FMM` | `CO-145`, `CO-213` | 1 | 1 |
| `CU-CFG-FMB` | `CO-147`, `CO-148`, `CO-156`, `CO-213` | 1 | 3 |

**Tanda 1: 18 contratos distintos.** `CO-139`, `CO-147` y `CO-220` son solicitudes: devuelven el
informe y no cambian nada, así que se cuentan como consulta.

Las altas `CO-137`, `CO-141` y `CO-144` también se invocan desde el alta de lotes y desde el alta
de proveedor (A1 de `EDA`, `TPA` y `FMA`). Hoy sólo la editorial tiene alta al vuelo; se agregan
tipo y formato con el mismo parcial `_catalogo_rapido.html`.

**Cambio de comportamiento visible.** La casilla `activo` sale de los formularios de alta y de
modificación. El alta nace activa. La modificación sólo reactiva. La baja pasa a una pantalla
propia con el informe y la confirmación. Los tres listados salen de la pantalla de parámetros a
una pantalla propia cada uno, con filtro por estado, y la pantalla de parámetros los enlaza.

**Lo que la baja cambia en otros módulos.** Los contratos `CO-140`, `CO-148` y `CO-221` dicen que,
desde la baja, la entrada no se asigna «por ninguna vía». Un borrador que la hereda de su
proveedor registra un reparo y no se puede confirmar. Hoy los borradores no miran el estado de
la editorial ni del tipo que heredan. Se agrega en `catalog/borradores.py` y en
`catalog/revisiones.py`, con prueba.

### Tanda 2

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CFG-FAQ` | `CO-135`, `CO-136`, `CO-210` | 2 | 1 |
| `CU-CFG-VIS` | `CO-131`, `CO-208` | 1 | 1 |
| `CU-CFG-BNC` | `CO-209` | 0 | 1 |
| `CU-CFG-BNA` | `CO-132`, `CO-209` | 1 | 1 |
| `CU-CFG-BNM` | `CO-133`, `CO-209` | 1 | 1 |
| `CU-CFG-BNB` | `CO-134`, `CO-209` | 1 | 1 |

**Tanda 2: 10 contratos distintos.** Se suma el atributo del intervalo del carrusel en
`ConfiguracionSistema`, editable desde `ParametrosView` (sección Tienda de `CU-CFG-PAR`).

`CU-CFG-BNB` pide confirmación, pero su ficha no declara `cancelarOperacion` y `CO-156` no lo
referencia. El abandono se prueba igual, como parte de `CO-134`: sin confirmación no hay
eliminación.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Editorial` | Sí | Lo modifica: la baja pasa a un par con informe |
| `Tipo` | Sí | Lo modifica: el rubro entra al formulario; se declaran formatos desde el tipo |
| `Formato` | Sí | Lo modifica: «aplica a todos los tipos» (ver ambigüedad 1) |
| `BorradorProducto` | Sí | Lo modifica: reparo por entrada inactiva heredada |
| `ContenidoFAQ` | **No** | Lo crea. Instancia única (I-14) |
| `IdentidadVisual` | **No** | Lo crea. Instancia única. Su alcance depende de la ambigüedad 6 |
| `Banner` | **No** | Lo crea |
| `ConfiguracionSistema` | Sí | Lo modifica: intervalo del carrusel, **que el modelo de dominio todavía no declara** |
| `RegistroAuditoria` | Sí | Lo lee y escribe. Ver ambigüedad 4 |

La tanda 2 necesita además el procesamiento de imágenes de RNF-05: conversión a WebP, lado mayor
de 1920 px para banners y sin conservar el original. **No existe en ninguna parte del sistema**,
tampoco para las portadas. Se construye como una función única que usan los banners y el logo.
Las portadas quedan como deuda del módulo 01 y no se tocan en este plan.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-144`, `CO-145`, `CO-146`, `CO-049` y las fichas `FMA`/`FMC`/`FMM`/`TPA`: «f.aplica a todos los tipos» | Los contratos lo declaran como **atributo** que se fija y cambia. `MODELO_DE_DOMINIO.md` no lo declara en `Formato`. El código lo **deduce** de la lista vacía de tipos. **(a)** Atributo propio, con una migración que marca como «aplica a todos» los formatos que hoy tienen la lista vacía. **(b)** Deducido. Con (b), `CO-146` se contradice: declarar un formato universal desde un tipo lo convierte en particular sin que nadie lo decida. **Recomiendo (a)** | Decisión del responsable y enmienda del modelo de dominio. **Bloquea `FMA`, `FMM` y la declaración de formatos de `TPA`/`TPM`**. El resto de la tanda avanza |
| 2 | `CO-220` y `CU-CFG-TPB` paso 2: «cuántas ofertas Programadas o Activas» | `Oferta` no existe. **(a)** Informar «No disponible», como pide `CO-163` para los indicadores que dependen de módulos no construidos. **(b)** Informar 0. **Recomiendo (a)**: un cero diría que se verificó que no hay ofertas | Confirmación. Hasta que exista `Oferta`, la postcondición «Oferta → Tipo se conservaron» no se puede ejercer y `CO-221` queda parcial |
| 3 | `CU-CFG-EDC`, `TPC`, `FMC`: «cantidad de productos vinculados» | ¿Cuenta todos los estados, o sólo los no terminales? Los informes de baja dicen «todas las referencias que la baja conserva» (R2). **Recomiendo contar todos**, igual que los informes | Confirmación |
| 4 | Todas las escrituras: «Se creó una entrada en el registro de auditoría de la operación» | Hoy los catálogos se auditan con la acción «Modificación de parámetros globales». `CO-130` dice que un catálogo **no** es un parámetro. El enumerado es cerrado y sólo se amplía declarándolo en el modelo. **(a)** Se conserva la acción actual. **(b)** El responsable declara acciones propias: alta, modificación y baja de catálogo, más FAQ, identidad visual y banner, que hoy no tienen ninguna | Decisión del responsable. Para los catálogos no bloquea, porque ningún contrato nombra la acción. **Para FAQ, identidad visual y banners no hay ninguna acción aplicable**: bloquea su cierre |
| 5 | `CU-CFG-PAR` sección Tienda: intervalo del carrusel | Construirlo es una decisión ya tomada. **Su valor inicial no está en ninguna parte** | **El valor inicial, del responsable.** Bloquea la migración de `ConfiguracionSistema` |
| 6 | `CO-131`, `CU-CFG-VIS`, modelo `IdentidadVisual`: «fondo: {Color sólido, Imagen}» | `TOKENS_VISUALES.md` prohíbe los fondos con imagen y declara `--tienda-fondo` como color. La ficha y el modelo admiten imagen. Además `CO-131` sigue diciendo que P-07 está abierta. **(a)** Mientras rija el estilo preliminar, el fondo es sólo color, y se guardan los tres colores más el fondo, que son las cuatro `--tienda-*`. **(b)** Se construye la opción de imagen igual. **Recomiendo (a)** | Decisión del responsable: si P-07 quedó cerrada con las cuatro variables, y qué pasa con el fondo imagen. **Bloquea `CU-CFG-VIS`** |
| 7 | `CO-133` precondición: «la posición está dentro del rango de la galería» | ¿La posición es 0, 1, 2… o 1, 2, 3…? El modelo dice «entero ≥ 0» y la ficha habla de «posición numerada». Se guarda desde 0 y se muestra desde 1 | Nada, salvo objeción |
| 8 | `CO-135`: «El contenido quedó publicado en la tienda». `CO-132`: «El banner quedó publicado en la tienda» | Ningún caso de uso declara la **portada** ni la **página de preguntas frecuentes** públicas. `CU-TDA-CAT` es el catálogo y no las menciona. **(a)** Se construyen las dos pantallas públicas como parte de estos casos de uso, porque sin ellas la postcondición no se puede verificar. **(b)** Se espera a que el documento las asigne | Confirmación. Con (b), los seis casos de uso de la tanda 2 quedan parciales |
| 9 | `CO-135`: Markdown «se publica tal cual» | Renderizar Markdown escrito por el Administrador en una pantalla pública abre una vía de inyección de guiones. **(a)** Se renderiza con HTML crudo deshabilitado. **(b)** Tal cual, con HTML. **Recomiendo (a)**. No cambia lo que el Administrador puede escribir en Markdown | Confirmación |
| 10 | RNF-05: «compresión con nivel de calidad configurable» | `ConfiguracionSistema` no declara ese parámetro. Se usa un valor fijo en el código y se anota como agregado | Nada, salvo objeción |

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CU-CFG-EDC`, `EDA`, `EDM`, `EDB` | Estilo preliminar | Sin ambigüedades bloqueantes. Fija el patrón de listado, alta, modificación y baja con informe que siguen los otros dos catálogos |
| 2 | `CU-CFG-TPC`, `TPB` y la parte de `TPA`/`TPM` sin formatos | 1 | El rubro entra al formulario. `TPB` necesita la ambigüedad 2 |
| 3 | `CU-CFG-FMC`, `FMB` | 1 | Sin bloqueo |
| 4 | `CU-CFG-FMA`, `FMM` y `CO-146` desde el tipo | 2, 3, **ambigüedad 1** | Si sigue abierta, estos quedan `Bloqueado` y se sigue con el módulo 02 |
| 5 | Reparo del borrador por entrada inactiva | 1, 2, 3 | Toca el módulo 01; se prueba contra `CO-140`, `CO-148` y `CO-221` |
| 6 | `CU-CFG-FAQ` | Estilo, **ambigüedades 4, 8 y 9** | Instancia única, sin imágenes: el más chico de la tanda 2 |
| 7 | Procesamiento de imágenes de RNF-05 | — | Lo necesitan 8 y 9 |
| 8 | `CU-CFG-BNC`, `BNA`, `BNM`, `BNB` y el carrusel | 7, **ambigüedades 4, 5 y 8** | El carrusel cambia de imagen al instante, con «Anterior», «Siguiente» y «Pausar» como `.boton-texto` |
| 9 | `CU-CFG-VIS` | 7, **ambigüedades 4 y 6** | Último: cambia cómo se ve toda la parte pública |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Dos administradores modificando el mismo catálogo | Baja y modificación del mismo registro | La confirmación relee el estado dentro de la transacción. Si ya no está activo, informa y no hace nada |
| Reordenar banners deja posiciones repetidas o con huecos | `CO-133`, `CO-134` | Reajuste en una sola transacción con bloqueo sobre la galería. La prueba afirma posiciones consecutivas después de cada operación |
| Una imagen inválida deja el banner a medias | `CO-133` E1: «no se registra ningún cambio, tampoco el de posición» | Se procesa la imagen antes de tocar nada. Prueba de la postcondición negativa |
| Colores de `IdentidadVisual` que dejan la tienda ilegible | `CU-CFG-VIS` | No hay regla declarada. El foco se sigue marcando en `--tinta` y la vista previa muestra el resultado. Validar el contraste sería un agregado y se consulta antes |
| La red en las pruebas | Ninguna integración nueva | — |

---

## 6. Fuera de alcance

- `CU-CFG-PAR` completo. Las secciones de los módulos no construidos y la de Seguridad
  (B-12-001) siguen pendientes.
- El procesamiento RNF-05 de las portadas de producto.
- El filtro por estado de las etiquetas en el catálogo público: vive en el módulo 02 y en
  `CU-TDA-CAT`.
