> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `00` Sincronización con el documento de análisis

> Registro de las pasadas que comparan el sistema construido con el documento de análisis.
> **Se anexa, no se reescribe.** Una entrada resuelta se marca; no se borra.
>
> El inventario de cada pasada es una fotografía y vive en
> [`docs/sincronizacion/INVENTARIO.md`](../docs/sincronizacion/INVENTARIO.md); esta bitácora registra
> que la pasada ocurrió, contra qué se comparó y qué encontró que no tiene otro lugar.

---

## Entradas

### Nota · 2026-10-30 · Primer inventario de cambios para el documento

**Documento comparado.** `docs/Longbox - Comic Store Manager.docx`, modificado el 2026-09-30 09:03
(revisión interna 56). La última versión de su Lista de Cambios es la **13, del 05/09/2026**; el
responsable confirmó que el archivo es el vigente y que su contenido es del 30/09. El historial de git
se leyó desde esa fecha: 14 commits (`62b72d8` a `b6dd342`) y el árbol de trabajo sin commitear.

**Base.** `scripts/generar_contexto.py` corrido hoy: 18 módulos, 103 casos de uso, 219 contratos;
`.contexto-ia/` no cambió y los 11 archivos protegidos siguen iguales. Informe completo en
[`docs/sincronizacion/generador.txt`](../docs/sincronizacion/generador.txt).

**Cifras.**

| | |
| --- | ---: |
| Filas del inventario | 209 |
| Por tipo | 145 agregados, 49 correcciones, 8 desvíos, 2 mixtas, **5 sin registro** |
| Por estado en el documento | 81 no reflejadas, 119 parciales, 5 no determinables, 4 reflejadas |
| Requieren asignar un código | 23 |
| Requieren una decisión | 23 |
| Entradas `B-` de la bitácora | 267: 219 citadas en alguna fila y 48 excluidas con su motivo |
| Rótulos provisorios | 1 módulo, 19 casos de uso, 25 contratos, 16 DSS, 4 requisitos, 3 invariantes, 6 estados |
| Flujos que conviene reescribir | `CU-DEV-SOL`, `CU-DEV-RES`, `CU-ALT-TRA`, `CU-RST-APR`, `CU-CLI-HIS` |

**Lo que el responsable tiene que ver primero.** Dos cambios **sin registro** alteran lo que el
usuario puede hacer: la consulta de los **cierres de caja anteriores** (Cajero y Administrador,
`caja/cierres/`) y la **página pública de la política de privacidad**. Están en el inventario como
filas «Sin registro», con la decisión que piden.

**Citas de la bitácora que no cierran.** No se corrigen acá, porque las entradas no se reescriben:

- B-17-011 cita la consulta C-08; la del logo, en `docs/DEUDA.md`, es **C-21**.
- B-17-007 nombra `CU-PRV-MOD`, que no existe; el caso de uso es `CU-PRV-EDI`.
- B-05-016 dice «Nada» para el documento y `docs/DEUDA.md` pide enmendar `CU-RST-APR` paso 2; el
  inventario lo registra por `DEUDA.md`.
- B-00-001 dice «Nada» para el documento, pero el «Estudio de Factibilidad» nombra Tailwind en cuatro
  lugares.

**Una interpretación de la consigna.** El índice del documento numera dos capítulos «3». Las
«Secciones 4 y 5» se tomaron por orden real: «Alcance y Limitaciones» y «Estudio de Factibilidad».

**Contradicciones.** No hay contradicciones entre entradas sin resolver: en todos los casos la
posterior dice qué reemplaza. La más grande: B-09-008 retira `DevolucionFisica`, que R-09-001 había
decidido conservar.
