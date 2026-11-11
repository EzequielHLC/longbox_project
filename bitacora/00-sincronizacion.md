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

### Nota · 2026-11-08 · Segunda pasada: decisiones del responsable y códigos nuevos

**Documento comparado.** El mismo de la nota anterior: versión 13 de la Lista de Cambios, archivo del
2026-09-30. La pasada completa el inventario del 2026-10-30 con las 13 entradas del 2026-11-07 y
verifica las decisiones abiertas de ciclos anteriores contra lo construido.

**Regla nueva del ciclo.** Lo construido es final: el documento de análisis se corrige para describirlo.

**Decisiones del responsable.**

- **Códigos de caso de uso**, asignados por Claude por delegación del responsable, con la forma
  `CU-###-!!!`: `CU-RST-RSP` (respuesta del proveedor), `CU-CFG-FIL` (filas de la portada),
  `CU-CAJ-HIS` (cierres de caja anteriores), `CU-TDA-POR` (portada pública), `CU-TDA-PFR` (preguntas
  frecuentes públicas), `CU-CLI-POL` (política de privacidad) y `CU-REP-PAN` (panel del Administrador,
  con `CO-219`). Se conservan `CU-RST-PRC`, `CU-RST-PDA`, `CU-RST-LLE` (C-23) y los once `CU-AVI-*`
  (B-19-001). «Volver a anunciar» queda como flujo alternativo del alta, sin código.
- **Se retiran**, y sus códigos no se reutilizan: `CU-RST-ING` (lo cubre `CU-RST-LLE`), `CU-DEV-PRU`,
  `CO-222`, `CO-223`, `CO-224`, `CO-225` y `CO-226`; el estado «Pendiente de verificación» de
  `TransaccionPago` y `CU-CAJ-CIE` A1, que ningún flujo usa; DME-16.
- **Reservados sin construir:** `CO-230` y `CO-231` (ingreso con Google).
- **RNF-09** declara la excepción: suscribirse a un aviso de reposición, cancelarlo, canjear puntos y
  anular el canje no se auditan (`CO-075`, `CO-076`, `CO-103`, `CO-104`), como ya hace el sistema.
- **Lo construido sin registro entra al documento**: los cierres de caja anteriores y la política de
  privacidad, con caso de uso, DSS y contratos; los datos que el modelo no declaraba, al modelo; el
  despliegue en la VM, al alcance.
- **Casos de prueba:** `CP-MOD-AAA-NN`.
- Las decisiones de ciclos anteriores (M6, N3, N7, `CO-155` en PA-04, la sección 5) se resuelven como
  lo construido.

**Pendiente de confirmar:** la numeración de los contratos nuevos desde `CO-233`, y la de requisitos,
invariantes y máquinas de estado a continuación de las vigentes.

**Para quien programe.** Ningún código cambia por esta pasada. Los códigos nuevos todavía no están en
`.contexto-ia/`: llegan cuando el responsable aplique las correcciones y se regenere el contexto.

### Nota · 2026-11-08 · Confirmación de la numeración

El responsable confirmó lo que la nota anterior dejaba pendiente: los contratos nuevos se numeran desde
`CO-233`, sin reutilizar huecos; siguen `RF-28` a `RF-30`, `RNF-13`, `I-24` a `I-26`, `DME-19` y
`DME-20`. Confirmó también que la relación entre cada caso de prueba y sus pruebas vive en la ficha del
caso, que `CO-228` es un paso de `CU-ALT-NOV` E2, que los contracargos de MercadoPago son un límite
declarado y que `CU-TDA-POR`, `CU-TDA-PFR` y `CU-REP-PAN` son casos de uso.
