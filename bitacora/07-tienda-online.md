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
