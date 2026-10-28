> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Cierre de la deuda de código

**Estado del plan:** Aprobado el 2026-10-23, con las cuatro recomendaciones de la sección 3 · **Fecha:** 2026-10-23

Los 103 casos de uso están verificados y las siete puertas en verde (medición del 2026-10-23 en
[`ESTADO.md`](../ESTADO.md)). Lo que queda en [`DEUDA.md`](../DEUDA.md) se divide en dos: lo que
espera una decisión o una enmienda del responsable, que este plan **no toca**, y cuatro deudas de
código que la especificación ya resuelve y el código todavía no cumple. Este plan es sobre las
cuatro.

Ninguna agrega un caso de uso, un contrato ni un concepto. Cada una hace que una operación que ya
existe cumpla lo que su contrato, una invariante o un requisito no funcional ya dicen.

---

## 1. Qué cubre

| # | Deuda | Qué dice la especificación | Casos de uso | Contratos |
| --- | --- | --- | --- | --- |
| D1 | **Carreras de unicidad no ensayadas.** Un doble envío del alta puede terminar en 500 en vez de en el aviso de duplicado | Los contratos declaran la colisión como excepción con aviso, no como fallo | `CU-ALT-NAC`, `CU-ALT-IMP`, `CU-ALT-REV`, `CU-CAT-ALT`, `CU-CAT-EDI`, `CU-CLI-ALT`, `CU-USR-ALT` | `CO-003`, `CO-009`, `CO-022`, `CO-028` E3, `CO-030` E2, `CO-107` E1, `CO-120` E2 |
| D2 | **RNF-05 en las portadas de producto.** Hoy se guardan tal como llegan | RNF-05: «toda imagen que suba el Administrador —portadas, imágenes de producto…— […] conversión al formato WebP, redimensionado […] 800 px en el lado mayor […] El archivo original […] no debe conservarse» | `CU-ALT-NAC`, `CU-ALT-IMP`, `CU-ALT-REV`, `CU-CAT-ALT`, `CU-CAT-EDI` | `CO-003`, `CO-009`, `CO-022`, `CO-028`, `CO-030` |
| D3 | **Invariantes sin garantía en la base**: I-05, I-06, I-09 en `Producto.precio` e I-12 | Modelo de dominio, § 6: «son verdaderas antes y después de todas [las operaciones]» | Todos los que escriben productos o cuentas de personal | — (invariantes, no contratos) |
| D4 | **Supresiones de `bandit` sin justificación** | La puerta: «sin hallazgos sin justificación registrada» | — | — |

### D1 · Qué se ensaya

Por cada operación, una prueba que **gana la carrera**: el formulario valida, otra transacción
inserta el valor único antes de que se guarde, y se comprueba que la respuesta es el aviso que
declara el contrato, con la ficha en conflicto cuando el contrato la pide, y que no se creó nada
ni quedó auditoría. Donde la prueba dé 500, se corrige como ya se hizo en catálogos y proveedores
(B-17-016, B-04-006): el `IntegrityError` se vuelve a verificar y, **sólo si de verdad hay un
duplicado**, se informa como la excepción del contrato. Si no lo hay, el error sigue subiendo
(la lección de `catalog/services.py`, donde tratar todo `IntegrityError` como colisión escondió
un defecto).

| Operación | Valor único | Respuesta que exige el contrato |
| --- | --- | --- |
| `CO-003`, `CO-009` (ítem del lote) | ISBN, clave de edición | El ítem se excluye como duplicado y el lote sigue (E1 del caso de uso) |
| `CO-022` (confirmar borrador) | ISBN, clave de edición | La colisión con su criterio (`CO-022` E7) |
| `CO-028` | Código interno, código de barras | E3: se bloquea, con enlace a la ficha en conflicto |
| `CO-030` | Código de barras, ISBN, clave de edición | E2: duplicidad con enlace y criterio; no se actualiza |
| `CO-107` | Correo | E1: «Este correo ya tiene una cuenta asociada», con enlace a recuperar |
| `CO-120` | Correo | E2: se informa el conflicto y no se crea la cuenta |

Los nombres llevan el contrato: `test_CO107_doble_envio_del_registro_informa_E1`.

### D2 · Qué cambia

La portada pasa por `core.imagenes.procesar`, igual que las imágenes adicionales, en las cinco
entradas: el ítem del lote nacional e importado, el alta no editorial, la edición y la portada
que trae el correo del proveedor. Una portada que no es JPG, PNG o WebP, o que está dañada, deja
de aceptarse con el mensaje del problema específico; hoy el campo acepta cualquier formato que
lea la biblioteca de imágenes. Las pruebas siguen la condición de verificación de RNF-05: una PNG
de más de 800 px queda guardada sólo en WebP, con 800 px en el lado mayor, **sin el original**, y
por debajo de 150 KB.

### D3 · Qué cambia

| Invariante | Cómo queda en la base | Por qué así |
| --- | --- | --- |
| I-09 · `Producto.precio` mayor que cero | `CheckConstraint`, como las de la compra | La propagación de precios escribe con `update()` y no pasa por los validadores |
| I-09 · `TablaPrecioReferencia.pvp` mayor que cero; `precio_base` y `costo_origen` no negativos | `CheckConstraint` | Mismo motivo |
| I-05 · el tipo es del rubro del producto | Disparador de restricción **diferido al cierre de la transacción** | El tipo vive en la tabla del padre y el rubro lo da la tabla hija, que se inserta después: un control inmediato vería un producto sin rubro |
| I-06 · el no editorial no está en Pre-venta ni Cancelado | Disparador de restricción diferido | El estado vive en la tabla del padre |
| I-12 · siempre un Administrador activo | Disparador que bloquea las filas de los Administradores activos y vuelve a contar | El servicio ya lo cumple con un bloqueo ordenado (B-13-006); el disparador alcanza cualquier escritura, como I-13 (B-16-004) |

La base de desarrollo no tiene ninguna fila que viole estas invariantes (consultado el
2026-10-23 sobre 3683 productos), así que las migraciones aplican sin tocar datos.

### D4 · Qué cambia

Sólo comentarios: cada `# nosec` dice la regla y el motivo en su línea, y el `# nosec` sin código
de `scripts/demo/mutacion.py` pasa a nombrar la regla que suprime.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Producto`, `ProductoEditorial`, `ProductoNoEditorial` | Sí | Restricciones y disparadores nuevos; la portada se procesa |
| `TablaPrecioReferencia` | Sí | Restricción nueva |
| `BorradorProducto` | Sí | La portada del correo se procesa al adjuntarla |
| `Usuario` | Sí | Disparador de I-12; las altas manejan la carrera |
| `Tipo` | Sí | Sólo lo lee el disparador de I-05 |

Ningún concepto nuevo.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | RNF-05 y la portada del correo del proveedor (`CU-ALT-NOV`, `CU-ALT-REV`) | RNF-05 habla de «toda imagen que suba el Administrador», y la del correo no la sube nadie / la portada del borrador termina en el catálogo igual que una subida | **Procesarla al adjuntarla al borrador**: la revisión ve la misma imagen que se va a guardar, y el original del adjunto no queda en el almacenamiento. La lectura literal dejaría en el catálogo imágenes de cualquier tamaño |
| 2 | Las portadas que ya están guardadas | RNF-05 rige para lo que se sube de ahora en más / también para lo ya guardado | **Sólo de ahora en más.** Reprocesar lo guardado es irreversible sobre archivos y no lo pide la condición de verificación, que habla de «una imagen subida». Se registra en la bitácora |
| 3 | Un formato de portada que hoy se acepta (GIF, BMP) | Se sigue aceptando y se convierte / se rechaza como en banners | **Se rechaza**, con el mensaje de `core.imagenes`. Es el criterio que ya rige para las imágenes adicionales del mismo producto, y la condición de verificación de RNF-05 nombra PNG y JPG |
| 4 | I-12 en la base | Alcanza con el servicio (hoy) / la invariante «es verdadera antes y después de todas» | **Llevarla a la base**, por la regla de `CLAUDE.md`: «la restricción vive en el servidor, no en el formulario». Si preferís que quede como está, D3 se hace sin I-12 |

Ninguna bloquea el resto del plan.

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | D4 | — | Sólo comentarios; deja la puerta de seguridad limpia desde el principio |
| 2 | D1 | — | Las pruebas primero: dicen qué operación da 500 de verdad antes de tocar nada |
| 3 | D2 | — | Toca los mismos formularios de alta que D1, ya con las pruebas puestas |
| 4 | D3 | D1 | Las restricciones nuevas pueden convertir un camino que hoy pasa en un `IntegrityError`; D1 ya deja el manejo en su lugar |
| 5 | Cierre | Todo | Las siete puertas, las dos verificaciones a mano (las migraciones aplican y las restricciones y disparadores están en la base), `ESTADO.md`, `DEUDA.md` y `COBERTURA.md` |

Cada deuda se cierra con su anotación en la bitácora del módulo que corresponda, cuando aparece
la decisión: `01` para el lote y el borrador, `02` para el catálogo e I-05, I-06 e I-09, `11` para
el registro, `13` para el alta de personal e I-12.

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Un disparador diferido rechaza algo al confirmar y la vista responde 500 | I-05, I-06 | Ninguna operación construida debería violarlas: las pruebas existentes lo confirman. Pruebas nuevas que escriben por fuera del modelo (con `update()` y SQL) y esperan el rechazo |
| Las pruebas que arman productos con un tipo de otro rubro o un precio cero para otro fin | Fábricas y pruebas viejas | La suite completa después de cada migración; se corrige la fábrica, no la restricción |
| El disparador de I-12 se cruza con el bloqueo ordenado del servicio | `accounts` | La prueba de concurrencia existente (B-13-006), corrida tres veces seguidas |
| La portada procesada pesa más de 150 KB | D2 | Prueba con una imagen fotográfica de 2000 px, no con un color plano |
| Las pantallas del error de imagen y del duplicado por carrera | Formularios de alta | Capturas con Chrome sin interfaz, en escritorio y en 390 px |

---

## 6. Fuera de alcance

Lo que sigue en `DEUDA.md` y **no** es de este plan, porque espera al responsable:

- C-19 (margen sin importados) y C-21 (el logo en SVG).
- `CO-219` y el tablero del Administrador; el contrato de la política de privacidad; la
  degradación de `integraciones.py` fuera de las cotizaciones.
- El código del caso de uso de las filas de la portada y la ficha de `CU-PVP-VEN`.
- Los apartados del DSS de C-17, `04_RESUMEN.md` y todas las enmiendas al documento.
- La calidad y las dimensiones de RNF-05 como parámetros (B-17-012): `ConfiguracionSistema` no
  los declara.
- MercadoPago contra la API real, el envío por peso, el bot de Telegram y el calendario público
  de lanzamientos.

Tampoco entra cifrar la credencial del modelo de lenguaje en la base: `CO-130` dice que «se
almacena y no se devuelve nunca al formulario», y eso ya se cumple.
