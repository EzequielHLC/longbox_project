> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de construir y **no se reescribe** después: lo que cambie va a
> `bitacora/00-documentacion-de-pruebas.md`.

# Plan — `00` Documentación de pruebas

**Estado del plan:** Aprobado el 2026-10-07 · **Fecha:** 2026-10-07

Reemplaza la versión de la mañana del mismo día, que armaba el modelo de pruebas completo del
Proceso Unificado (índice, plan de prueba, procedimientos y casos por escenario de cada caso de
uso). El responsable lo descartó por excesivo (B-00-015).

---

## 1. Qué queda en `docs/pruebas/`

| Archivo | Responde | Tipo | Cómo se mantiene |
| --- | --- | --- | --- |
| `CATALOGO.md` | Qué pruebas hay, qué hace cada una y si pasa | Fotografía | `scripts/generar_catalogo.py`, que corre la suite |
| `ESPECIFICACION.md` | Cómo se construye una prueba | Normativo | A mano, con aprobación |
| `COBERTURA.md` | Cuántos contratos tienen prueba | Fotografía | `scripts/generar_cobertura.py` |
| `CASOS_DE_PRUEBA.md` | Qué casos de prueba hay, elegidos por riesgo | Normativo | A mano, con aprobación |

**Se borran:** `DEMO.md` (sus escenarios pasan a ser casos), `DEMO-ENSAYO.md` (sus hallazgos ya
están en las bitácoras de cada módulo), y el índice, el plan de prueba y los casos por módulo que
se habían escrito en la mañana.

---

## 2. Los casos de prueba

**Criterio de selección** (decisiones 1 a 3 del responsable):

- los riesgos de la Tabla de Riesgos del documento (apartado 5.3) con exposición de 1,80 o más, o
  con impacto Crítico, que se puedan verificar sobre lo construido: R-01, R-14, R-15, R-07 y R-08;
- R-13, que está por debajo del corte, porque es la regla 4 del dominio;
- la carga y el volumen (`RNF-02`, `RNF-07`).

Quedan afuera R-03 y R-06, porque ventas y pagos no están construidos, y R-04 y los riesgos de
proyecto, porque ninguna prueba los mitiga.

**Fuente de los escenarios:** los de la demostración de resistencia (`scripts/demo/`) y las
pruebas de la suite que los respaldan.

**Campos de cada caso:**

1. identificador y objetivo;
2. trazabilidad;
3. precondiciones;
4. datos de entrada;
5. pasos;
6. resultado esperado y postcondiciones.

**Identificador:** `CP-NN`, correlativo. El riesgo va en la trazabilidad (decisión 5).

---

## 3. Referencias que hay que corregir

| Dónde | Qué |
| --- | --- |
| `docs/planes/00-demostracion.md` | Remite a `DEMO-ENSAYO.md` y a `docs/pruebas/demo/` |
| `scripts/demo/ensayo.py` | Su docstring remite a `DEMO-ENSAYO.md` |
| `scripts/demo/escalones.py` | Guarda el gráfico en `docs/pruebas/demo/`, una carpeta que no existe; pasa a `scripts/demo/salida/` |

---

## 4. Fuera de alcance

- Las pruebas: no se escribe, renombra ni marca ninguna.
- El documento de análisis y `.contexto-ia/`.
