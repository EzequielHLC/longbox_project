> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `00` Documentación de pruebas

> Registro de lo que se decidió escribiendo el modelo de pruebas (plan
> `docs/planes/00-documentacion-de-pruebas.md`). **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.
>
> La numeración sigue la de las otras bitácoras del módulo `00`, que comparten el prefijo `B-00`.

---

## Entradas

### B-00-012 · Siete pruebas del módulo 13 verifican algo que ninguna ficha ni contrato declara

**Tipo:** Agregado · **Fecha:** 2026-10-07 · **Alcance:** `CU-USR-CON`, `CU-USR-MOD`
**Estado:** Abierta — consulta

**Qué apareció.**
Al escribir los casos de prueba del módulo 13, siete pruebas no encajaron en ningún escenario.
Verifican comportamientos que existen en el sistema y que la especificación no menciona:

| Prueba | Qué verifica |
| --- | --- |
| `test_listado_usuarios.py::test_un_filtro_con_un_valor_invalido_se_ignora` | Un filtro con un valor escrito a mano en la dirección no filtra de más ni rompe el padrón: se ignora |
| `test_listado_usuarios.py::test_se_informa_cuantos_resultados_hay` | El padrón dice cuántas cuentas muestra |
| `test_listado_usuarios.py::test_la_fila_del_propio_usuario_esta_marcada` | El Administrador ve marcada su propia cuenta en el padrón |
| `test_listado_usuarios.py::test_los_filtros_siguen_siendo_selects_de_verdad` | Los filtros son controles nativos del navegador, que funcionan sin JavaScript |
| `test_listado_usuarios.py::test_el_pedido_parcial_devuelve_solo_la_tabla` | El buscador en vivo recibe sólo la tabla, no la pantalla entera |
| `test_modificacion_usuario.py::test_guardar_sin_cambios_no_ensucia_la_auditoria` | Confirmar la edición sin cambiar nada no crea una entrada de auditoría |
| `test_pantallas_backoffice.py::test_ninguna_pantalla_filtra_comentarios_del_template` | Ninguna pantalla muestra restos sin interpretar de su plantilla |

**Qué dice la especificación.**
`Nada.` La ficha de `CU-USR-CON` no menciona el conteo, la marca propia, el tratamiento de un
filtro inválido ni la actualización parcial. `CO-121` dice que la modificación «queda registrada
en el log de auditoría con valores anteriores y nuevos de cada campo modificado», y no dice qué
pasa cuando no se modificó ningún campo.

**Qué se hizo.**
No se les escribió un caso de prueba: el plan prohíbe inventar escenarios. Siguen siendo
componentes de prueba sin caso.

**Qué habría que cambiar.**
Lo decide el responsable, caso por caso. Mi recomendación:

- **`CO-121`: aclarar si confirmar sin cambios es una operación.** Es el único de los siete que
  toca una regla del dominio, porque `RNF-09` exige auditar toda escritura. Si la ficha lo
  incorpora, recibe un caso en `CU-USR-MOD`.
- **El conteo, la marca propia y el filtro inválido:** agregarlos a la ficha de `CU-USR-CON` si
  se quiere que sean parte de lo que el caso de uso promete; si no, `Nada`.
- **Los controles nativos, la actualización parcial y los comentarios:** `Nada`. Son detalles de
  construcción, no comportamiento del caso de uso.

---

### B-00-013 · `RNF-11` y `RNF-12` llevan el título de `RNF-01`

**Tipo:** Corrección · **Fecha:** 2026-10-07 · **Alcance:** `RNF-11`, `RNF-12`
**Estado:** Abierta

**Qué apareció.**
El plan de prueba incorpora `RNF-11` y `RNF-12` a los casos transversales. Sus títulos no
corresponden a lo que describen.

**Qué dice la especificación.**
> `| RNF-11 | Diseño Web Responsivo |` — «Ninguna salida producida por un modelo de lenguaje debe
> modificar el estado del sistema sin confirmación humana explícita…»
>
> `| RNF-12 | Diseño Web Responsivo |` — «El sistema debe generar respaldos automatizados de la
> base de datos…»

`RNF-01` también se titula «Diseño Web Responsivo», y ése sí es su tema.

**Qué se hizo.**
Los casos de prueba citan los dos requisitos por su código y por su descripción, no por el título.

**Qué habría que cambiar.**
Requisitos no funcionales, filas `RNF-11` y `RNF-12`: corregir el título. Una propuesta:
«Confirmación humana de las salidas del modelo de lenguaje» y «Respaldo verificado de la base de
datos».

---

### B-00-014 · El modelo de dominio cuenta 14 máquinas de estados y el documento tiene 18

**Tipo:** Corrección · **Fecha:** 2026-10-07 · **Alcance:** DME-01 a DME-18, patrón P-04
**Estado:** Abierta

**Qué apareció.**
Los casos de prueba citan DME-18 (`EnlaceActivacion`). El patrón que justifica las máquinas de
estados dice que son catorce.

**Qué dice la especificación.**
> «P-04 · Estado como atributo + Máquina de Estados … **Aplicado a:** 14 conceptos con ciclo de
> vida (DME-01 a DME-14)» — `MODELO_DE_DOMINIO.md`, Patrones de Análisis.

La lista de diagramas tiene dieciocho figuras, de DME-01 (`Usuario`) a DME-18
(`EnlaceActivacion`), y suma `CasoDevolucion`, `CambioProducto`, `Proveedor` y
`EnlaceActivacion`.

**Qué se hizo.**
Los casos citan la DME que corresponde, aunque esté fuera del rango que declara P-04.

**Qué habría que cambiar.**
Patrones de Análisis, P-04, campo «Aplicado a», y la fila de P-04 en la tabla de patrones: «18
conceptos con ciclo de vida (DME-01 a DME-18)».

---

### B-00-015 · Los casos de prueba se eligen por riesgo, y no por escenario de cada caso de uso

**Tipo:** Agregado · **Fecha:** 2026-10-07 · **Alcance:** `docs/pruebas/`
**Estado:** Resuelta — decidida por el responsable el 2026-10-07

**Qué apareció.**
El primer enfoque derivaba un caso de prueba por escenario de cada caso de uso construido. El
piloto dio 29 casos para un solo módulo, de riesgo medio, con una ficha de doce campos.

**Qué dice la especificación.**
`Nada.` El documento de análisis no tiene apartado de casos de prueba. Su Tabla de Riesgos
(apartado 5.3) calcula la exposición de cada riesgo.

**Qué se hizo.**
Los casos de prueba salen de los riesgos con exposición de 1,80 o más, o con impacto Crítico, más
R-13 y la carga. Son 28, en `docs/pruebas/CASOS_DE_PRUEBA.md`, con seis campos. Se borraron:
- el índice, el plan de prueba y los casos por módulo;
- `DEMO.md`, cuyos escenarios pasaron a ser casos;
- `DEMO-ENSAYO.md`, cuyos hallazgos ya estaban en las bitácoras.

`CATALOGO.md` pasó a generarse con `scripts/generar_catalogo.py`, desde una corrida real de la
suite.

B-00-012 sigue abierta: las siete pruebas sin escenario declarado no dependen del enfoque.

**Qué habría que cambiar.**
Si el documento de análisis incorpora un apartado de casos de prueba, conviene que declare el
criterio de selección por riesgo y que remita a la Tabla de Riesgos.

---

### B-00-016 · Cada caso de prueba dice con qué se ejecuta

**Tipo:** Agregado · **Fecha:** 2026-10-07 · **Alcance:** `docs/pruebas/CASOS_DE_PRUEBA.md`, `CATALOGO.md`
**Estado:** Resuelta — pedido del responsable el 2026-10-07

**Qué apareció.**
Los casos citaban el escenario de la demostración (D3-02, D4-06…) pero no qué lo ejecuta. Al
borrar `DEMO.md`, lo que hace cada script de `scripts/demo/` quedó documentado sólo en su propio
docstring.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Cada caso suma un séptimo campo, «Se ejecuta con», que nombra la prueba de la suite, el script de
`scripts/demo/` o los dos. `scripts/generar_catalogo.py` lo lee:
- lista cada script con lo que hace y los casos que ejecuta;
- en cada archivo de la suite, indica los casos que ejecuta;
- avisa si un caso cita un archivo que no existe.

**Qué habría que cambiar.**
`Nada`.
