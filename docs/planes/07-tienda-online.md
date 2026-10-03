> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `07` Tienda Online

**Estado del plan:** Aprobado el 2026-10-02 por pedido explícito del responsable («crea un mini
apartado de tienda para la vista del cliente»), con las recomendaciones de la sección 3 aplicadas
· **Fecha:** 2026-10-02

Primer plan del módulo. Cubre sólo el catálogo público. El carrito, la compra y la consulta de
pedidos dependen de `Carrito`, `Pedido` y `TransaccionPago`, que no existen.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | `CO-176`, `CO-177` | 0 | 2 |

Las acciones de la ficha («Agregar al carrito», «Avisarme cuando haya stock», «Reservar») inician
`CU-TDA-CRA` y `CU-RST-SUS`, que no están construidos.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Producto` y sus dos especializaciones | Sí | Sólo los lee |
| `Etiqueta`, `GrupoEtiqueta` | Sí | Sólo los lee: el filtro de franquicia es el filtro por etiqueta |
| `Banner`, `ContenidoFAQ`, `IdentidadVisual` | Sí | La portada los muestra |
| `Oferta` | **No** | Sin ofertas, ningún precio sale tachado |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se aplicó |
| --- | --- | --- | --- |
| 1 | Precondición de `CU-TDA-CAT` y `CO-176`: «el acceso es público» frente a la portada, que hoy es sólo de la cuenta de cliente (C-20) | **(a)** Catálogo y ficha públicos; la portada sigue esperando C-20. **(b)** Todo detrás del inicio de sesión | **(a)**: la precondición del contrato es explícita |
| 2 | `solo_adultos` | Ningún caso de uso dice qué ve el catálogo público de un producto para adultos, y no hay verificación de edad | Se excluye del catálogo público, para todos. Es lo que el campo declara hacer en el código |
| 3 | Las acciones de la ficha | Inician casos de uso no construidos | Se muestran deshabilitadas, con la línea «Disponible próximamente» |
| 4 | Estado «Agotado» | Un producto Activo con stock 0 y uno en estado Agotado | Los dos se presentan como «Sin stock» y caen en el filtro «Agotado» |
| 5 | Filtro «franquicia» | Es una faceta de etiquetas (`CO-042`), no un campo | Filtro por etiqueta activa, agrupado por faceta |
| 6 | «paginados» | Sin tamaño | 24 por página: múltiplo de las columnas de la estantería |

---

## 4. Orden de construcción

| # | Qué | Depende de |
| --- | --- | --- |
| 1 | `CO-176`: consulta con filtros, orden y paginación | — |
| 2 | `CO-177`: ficha pública con su acción según estado | 1 |
| 3 | Portada: carrusel, ticker y recién llegados | 1 |

---

## 5. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Un Descatalogado o Cancelado visible por algún filtro | Prueba con los cinco estados contra cada valor del filtro de estado |
| Un producto para adultos visible | Prueba explícita |
| La ficha de un producto no visible se abre por la dirección | Responde 404 |

---

## 6. Fuera de alcance

- `CU-TDA-CRC`, `CRA`, `CRM`, `CRB`, `CMP`, `INV`: etapa B.
- El precio tachado por oferta: cuando exista `Oferta`.
