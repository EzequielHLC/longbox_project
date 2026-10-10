> **Tipo: Normativo.** Los casos de prueba del sistema, elegidos por riesgo. Lo que cada prueba
> automatizada hace y si pasa está en [`CATALOGO.md`](CATALOGO.md); cómo se escribe, en
> [`ESPECIFICACION.md`](ESPECIFICACION.md); qué contratos tienen prueba, en
> [`COBERTURA.md`](COBERTURA.md).

# Casos de prueba

**Criterio.** Entran los riesgos de la Tabla de Riesgos del documento de análisis (apartado 5.3)
con exposición de 1,80 o más, o con impacto Crítico, que se pueden verificar sobre lo construido.
Se suman R-13, porque es la regla 4 del dominio («el modelo propone, nunca aplica»), y la carga
(`RNF-02`, `RNF-07`). Quedan afuera R-03 y R-06, porque ventas y pagos no están construidos, y
R-04 y los riesgos de proyecto, porque ninguna prueba los mitiga.

**Datos.** Los casos de resistencia corren sobre la base de la demostración (`longbox_demo`,
poblada por `scripts/demo/poblar.py`), cuyas cuentas son `admin1@longbox.demo`,
`cajero1@longbox.demo` y `cliente001@longbox.demo`, todas con la contraseña `Demo-2026!`.

**Cómo se ejecutan.** Cada caso dice con qué se ejecuta: una prueba de la suite, un script de
`scripts/demo/` o los dos. Qué hace cada script, y qué casos ejecuta, está en
[`CATALOGO.md`](CATALOGO.md#scripts-de-scriptsdemo). Los scripts corren sobre la base de la
demostración, en el contenedor `longbox-demo-db`, y se niegan a tocar la de desarrollo.
`poblar.py` la llena una vez, y `restaurar.py` la vuelve al punto de partida después de un script
que escribe datos. Sólo `linea_base.py`, `caida_base.py` y la carga con `locustfile.py` necesitan
el servidor levantado (`manejar.py servir` y Caddy con `Caddyfile.demo`). `ensayo.py` corre todos
los scripts en orden y guarda la salida de cada uno.

| Riesgo | Exposición | Casos |
| --- | --- | --- |
| R-01 · Precios de importación desactualizados | 2,40 | CP-01 a CP-06 |
| R-14 · El modelo de lenguaje no está disponible | 1,80 | CP-07, CP-08 |
| R-13 · El modelo de lenguaje responde mal | 0,80 | CP-09, CP-10 |
| R-15 · Procesos periódicos | 1,80 | CP-11 |
| R-07 · Acceso no autorizado | Crítico | CP-12 a CP-22 |
| R-08 · Pérdida de datos | Crítico | CP-23 a CP-25 |
| Carga y volumen | `RNF-02`, `RNF-07` | CP-26 a CP-28 |

---

## R-01 · Precios de importación desactualizados

### CP-01 · El precio de un importado conserva todos los decimales del coeficiente de envío

- **Trazabilidad:** R-01 · `CU-ALT-IMP`, flujo principal · `RF-10` · Sabotaje «dinero» (D1-02).
- **Precondiciones:** Sesión de Administrador. Margen global de 40 %.
- **Datos de entrada:** Lote importado con envío total de $1.234,56 y compra total de
  $9.876,54. Un tomo con costo de $8.000.
- **Pasos:** 1. El Administrador carga el lote con su calculadora de envío. 2. Confirma el alta.
- **Resultado esperado:** El coeficiente se guarda como 0,124999, y el precio final del tomo es
  **$12.600**. Si el coeficiente se recortara a dos decimales antes de aplicarlo, daría $12.544.
- **Postcondiciones:** El producto existe con precio base de $8.999,99 y precio final de
  $12.600,00. Todo el cálculo es decimal exacto, sin punto flotante.
- **Se ejecuta con:** `apps/catalog/tests/test_casos_borde.py` (`test_D2_03_el_cre_conserva_sus_decimales_hasta_el_precio_final`) y `apps/catalog/tests/test_precios.py`. `scripts/demo/sabotaje.py dinero` comprueba que la suite lo detecta si se rompe, y `scripts/demo/mutacion.py precios` que ningún cambio al cálculo pasa inadvertido.

### CP-02 · Cambiar el margen global recalcula los importados vinculados y respeta los fijados a mano

- **Trazabilidad:** R-01 · `CU-PVP-MAR`, pasos 3 y 4 · `CO-052`, `CO-053` · `RF-10`.
- **Precondiciones:** Sesión de Administrador. Margen de 40 %. Hay un importado vinculado con
  precio base de $9.000 y precio de $12.600, que está en el carrito de `cliente001`. Hay otro
  importado con el precio fijado a mano en $15.000.
- **Datos de entrada:** Margen nuevo: 45 %.
- **Pasos:** 1. El Administrador simula el cambio y ve el impacto. 2. Confirma.
- **Resultado esperado:** La simulación informa cuántos productos se recalculan. Al confirmar, el
  primer importado vale $13.050, y el carrito del cliente lo muestra con el aviso de cambio de
  precio.
- **Postcondiciones:** El margen pasó de 40 % a 45 %. El precio base del vinculado no cambió. El
  fijado a mano sigue en $15.000. Hay una entrada de auditoría con el valor anterior, el nuevo y
  la cantidad de productos recalculados.
- **Se ejecuta con:** `apps/catalog/tests/test_contratos_03_pricing.py` y `apps/tienda/tests/test_contratos_07_carrito.py`, con `-k "CO052 or CO053"`.

### CP-03 · Cambiar un precio de la tabla de referencia lo propaga a los vinculados, salvo los cancelados

- **Trazabilidad:** R-01 · `CU-PVP-TBM`, pasos 5 a 7 · `CO-047`, `CO-048` · `RF-11`.
- **Precondiciones:** Sesión de Administrador. La combinación Ivrea · Tankōbon vale $9.500. Tiene
  vinculados un tomo Activo, que está en un carrito, y un tomo Cancelado por editorial.
- **Datos de entrada:** Nuevo precio de la combinación: $10.500.
- **Pasos:** 1. El Administrador edita la combinación y ve el informe de alcance. 2. Confirma.
- **Resultado esperado:** El informe lista los vinculados alcanzados. El tomo Activo vale $10.500,
  y su línea de carrito muestra el aviso de cambio.
- **Postcondiciones:** El tomo Cancelado sigue en $9.500. Hay una entrada de auditoría con la
  combinación, el valor anterior y el nuevo.
- **Se ejecuta con:** `apps/catalog/tests/test_contratos_03_pricing.py` y `apps/tienda/tests/test_contratos_07_carrito.py`, con `-k "CO047 or CO048"`.

### CP-04 · Si el servicio de cotizaciones no responde, se usa la última cotización guardada

- **Trazabilidad:** R-01 · `CO-155` · Cotizaciones caídas (D6-03).
- **Precondiciones:** Hay una cotización de USD guardada de $1.250,00, obtenida el día anterior
  y ya vencida. El servicio de cotizaciones no responde.
- **Datos de entrada:** La moneda USD.
- **Pasos:** 1. El sistema intenta sincronizar las cotizaciones. 2. El Administrador abre la
  calculadora de un lote importado en dólares.
- **Resultado esperado:** La calculadora usa $1.250,00, muestra la fecha en que se obtuvo y la
  marca como desactualizada.
- **Postcondiciones:** La cotización y su fecha no cambiaron. El fallo quedó registrado.
- **Se ejecuta con:** `apps/core/tests/test_cotizaciones.py`.

### CP-05 · Dos ofertas solapadas registradas al mismo tiempo: queda una sola

- **Trazabilidad:** R-01 · `CU-PVP-ALT`, excepción E2 · `CO-054` · `I-20` · `RNF-06` · Carrera
  D4-06.
- **Precondiciones:** Dos sesiones de Administrador. El tomo 1 de *Chainsaw Man* no tiene
  ofertas.
- **Datos de entrada:** Oferta «Semana del manga», 10 %, del día 10 al 20. Oferta «Promo
  Ivrea», 15 %, del día 15 al 25. Las dos sobre el mismo tomo.
- **Pasos:** 1. Los dos Administradores confirman su oferta en el mismo instante. 2. Se repite
  20 veces.
- **Resultado esperado:** Una se registra. La otra informa el conflicto, con el nombre de la
  oferta registrada y el período solapado. Ninguna respuesta es un error 500.
- **Postcondiciones:** Existe exactamente una oferta sobre el tomo.
- **Se ejecuta con:** `scripts/demo/carreras.py D4-06` y `apps/catalog/tests/test_concurrencia_ofertas.py`.

### CP-06 · Un importe imposible se rechaza sin registrar nada

- **Trazabilidad:** R-01 · `I-09` · `CU-CAT-ALT`, campo precio · Casos borde de dinero (Acto 2).
- **Precondiciones:** Sesión de Administrador.
- **Datos de entrada:** Precio de un producto no editorial: `0`, `-100`, `100,555`, `abc`,
  `99999999,99` y `10000000,00`. Después, el máximo exacto: `9999999,99`.
- **Pasos:** 1. El Administrador da de alta el producto con cada valor.
- **Resultado esperado:** Los seis primeros se rechazan con su motivo; el que pasa por un
  centavo el máximo informa «El máximo es $9999999.99». El máximo exacto entra.
- **Postcondiciones:** Sólo existe el producto con precio $9.999.999,99.

---

## R-14 · El modelo de lenguaje no está disponible
- **Se ejecuta con:** `apps/catalog/tests/test_casos_borde.py`, con `-k D2_03`.

### CP-07 · Con el modelo caído, el correo queda marcado con su motivo y se puede reprocesar

- **Trazabilidad:** R-14 · `CU-CFG-LLM` · `CU-PRV-COL` · `CO-017`, `CO-019` · Modelo caído (D6-01).
- **Precondiciones:** LM Studio apagado. Hay un correo de novedades de Ivrea en la cola,
  pendiente de aprobación. El catálogo tiene 20 000 productos.
- **Datos de entrada:** El correo de Ivrea.
- **Pasos:** 1. El Administrador corre el diagnóstico del modelo. 2. Aprueba el correo.
  3. Levanta LM Studio y reprocesa el correo.
- **Resultado esperado:** El diagnóstico dice «El servicio no respondió». El correo queda en
  «Falló el procesamiento», con su motivo. Al reprocesar, genera sus borradores.
- **Postcondiciones:** Mientras el modelo estuvo caído no se creó ningún borrador ni ningún
  producto. El catálogo sigue con 20 000 productos.
- **Se ejecuta con:** `scripts/demo/modelo_caido.py` (situación 1) y `apps/suppliers/tests/test_diagnostico_llm.py`.

### CP-08 · El mismo correo aprobado o ingerido dos veces no se procesa dos veces

- **Trazabilidad:** R-14 · `CO-017`, `CO-019` · `I-16` · `RNF-06` · Carreras D4-02 y D4-03.
- **Precondiciones:** Dos sesiones de Administrador. Hay un correo de Ivrea pendiente en la cola.
- **Datos de entrada:** El mismo correo, con su identificador de mensaje.
- **Pasos:** 1. Los dos Administradores aprueban el correo en el mismo instante. 2. Se ingiere
  otra vez el mismo archivo `.eml`. 3. Se reprocesa el correo ya procesado.
- **Resultado esperado:** Una aprobación procesa y la otra informa el estado del correo. La
  segunda ingesta no agrega nada. Ninguna respuesta es un error 500.
- **Postcondiciones:** Hay una sola fila del correo en la cola. El reproceso termina en Procesado
  o en Falló, y no toca los borradores ya confirmados.

---

## R-13 · El modelo de lenguaje responde mal
- **Se ejecuta con:** `scripts/demo/carreras.py D4-02 D4-03` y `apps/suppliers/tests/test_concurrencia_correos.py`.

### CP-09 · Una respuesta que no se puede interpretar no genera borradores

- **Trazabilidad:** R-13 · `RNF-11` · JSON roto (D6-02).
- **Precondiciones:** El modelo configurado es el falso (`scripts/demo/llm_falso.py roto`).
  Hay un correo de Ivrea pendiente en la cola.
- **Datos de entrada:** El correo de Ivrea. El modelo responde con un JSON roto.
- **Pasos:** 1. El Administrador aprueba el correo.
- **Resultado esperado:** El correo queda en «Falló el procesamiento», con el motivo «El modelo
  respondió algo que no se pudo interpretar».
- **Postcondiciones:** No se creó ningún borrador ni ningún producto.
- **Se ejecuta con:** `scripts/demo/modelo_caido.py` (situación 2), que levanta `scripts/demo/llm_falso.py roto`.

### CP-10 · Los datos inventados se descartan con su reparo, y nada llega al catálogo sin confirmar

- **Trazabilidad:** R-13 · `RNF-11` · `CU-ALT-REV` · Datos inventados (D6-02).
- **Precondiciones:** El modelo configurado es el falso (`llm_falso.py inventado`). El catálogo
  tiene 20 000 productos.
- **Datos de entrada:** El modelo responde con la forma correcta, pero con un ISBN de dígito
  verificador inválido, un precio negativo y una fecha imposible.
- **Pasos:** 1. El Administrador aprueba el correo. 2. Abre el borrador.
- **Resultado esperado:** El borrador queda en «Extracción incompleta». El ISBN, el precio y la
  fecha están descartados, cada uno con su reparo. El título queda para que lo confirme una
  persona.
- **Postcondiciones:** El catálogo sigue con 20 000 productos.

---

## R-15 · Procesos periódicos
- **Se ejecuta con:** `scripts/demo/modelo_caido.py` (situación 3), que levanta `scripts/demo/llm_falso.py inventado`.

### CP-11 · El temporizador activa y vence las ofertas en la fecha, en hora argentina

- **Trazabilidad:** R-15 · `CO-059` · `CU-PVP-ALT`, `CU-PVP-CON` · Plazos (Acto 2).
- **Precondiciones:** El tomo 1 de *Chainsaw Man* vale $10.000 y el tomo 2, $10.000. Hay una
  oferta Programada de 10 % sobre el tomo 1, que empieza hoy. Hay una oferta Activa de 15 % sobre
  el tomo 2, que vence hoy.
- **Datos de entrada:** `manage.py ejecutar_temporizador`, corrido hoy a las 23:59 y mañana a las
  00:01, hora argentina.
- **Pasos:** 1. Se corre el temporizador a las 23:59. 2. Se corre a las 00:01 del día siguiente.
- **Resultado esperado:** A las 23:59, el tomo 1 se ve a $9.000 y el tomo 2 todavía a $8.500. A
  las 00:01, el tomo 2 vuelve a $10.000.
- **Postcondiciones:** La primera oferta pasó a Activa y la segunda a Vencida. Hay una entrada
  «Vencimiento automático de oferta» con el Temporizador como actor.

---

## R-07 · Acceso no autorizado
- **Se ejecuta con:** `apps/catalog/tests/test_casos_borde.py` (`test_D2_04_la_oferta_descuenta_hasta_las_23_59_y_no_a_las_00_00`) y `apps/catalog/tests/test_contratos_03_ofertas.py`, con `-k CO059`.

### CP-12 · Toda ruta protegida rechaza al rol equivocado, sin devolver datos

- **Trazabilidad:** R-07 · `RNF-03` · Rutas protegidas (D3-01).
- **Precondiciones:** El servidor corre con la configuración de producción.
- **Datos de entrada:** Todas las rutas del sistema, cada una pedida por tres visitantes: sin
  sesión, `cliente001@longbox.demo` y `cajero1@longbox.demo`.
- **Pasos:** 1. Cada visitante pide cada ruta que su rol no puede usar.
- **Resultado esperado:** Sin sesión, la ruta lleva al inicio de sesión. Con un rol equivocado,
  responde 403, y el cuerpo no trae ningún correo ni código de producto.
- **Postcondiciones:** Nada cambió en la base.
- **Se ejecuta con:** `scripts/demo/rutas_protegidas.py`.

### CP-13 · Cinco intentos fallidos bloquean la cuenta, incluso para la contraseña correcta

- **Trazabilidad:** R-07 · `CU-AUT-INI`, excepción E1 · `CO-114` · `RNF-03` · Ataque D3-02.
- **Precondiciones:** La cuenta `cajero1@longbox.demo` está Activa y sin bloqueo. El límite es de
  5 intentos y el bloqueo dura 15 minutos.
- **Datos de entrada:** 20 intentos con la contraseña `la-que-no-es`; después, `Demo-2026!`.
- **Pasos:** 1. Se intenta iniciar sesión 20 veces seguidas con la contraseña equivocada.
  2. Se intenta con la correcta.
- **Resultado esperado:** Cada intento responde «Correo o contraseña incorrectos», sin decir qué
  falló. Desde el quinto, el acceso está bloqueado, y la contraseña correcta tampoco entra.
- **Postcondiciones:** Los intentos y el bloqueo quedaron en el registro de auditoría. Salió un
  aviso de bloqueo al correo de la cuenta.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-02` y `apps/accounts/tests/test_bloqueo_intentos.py`.

### CP-14 · Recuperar la contraseña no revela si la cuenta existe

- **Trazabilidad:** R-07 · `CU-AUT-REC`, paso 5 · `CO-117` · Ataque D3-03.
- **Precondiciones:** Existe `cliente001@longbox.demo`. No existe `nadie@longbox.demo`.
- **Datos de entrada:** Los dos correos.
- **Pasos:** 1. Se pide recuperar la contraseña con cada correo.
- **Resultado esperado:** Las dos respuestas son idénticas byte a byte, salvo el token CSRF.
- **Postcondiciones:** Sólo para `cliente001` se creó un token de 30 minutos y salió un correo.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-03`.

### CP-15 · Una inyección SQL o un script en un campo de texto no se ejecutan

- **Trazabilidad:** R-07 · `CU-CAT-INV`, `CU-TDA-CAT`, `CU-CFG-EDA` · Ataque D3-04.
- **Precondiciones:** Sesión de Administrador.
- **Datos de entrada:** La búsqueda `%'; DROP TABLE catalog_producto; --`, en el inventario y en
  la tienda. La editorial `Editorial <script>alert('longbox')</script>`.
- **Pasos:** 1. Se busca con la cadena en los dos buscadores. 2. Se da de alta la editorial y se
  abre el listado.
- **Resultado esperado:** Las búsquedas responden 200, sin resultados. El nombre de la editorial
  se ve como texto y el script no se ejecuta.
- **Postcondiciones:** La tabla de productos está intacta. La editorial se guardó con el nombre
  literal.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-04`.

### CP-16 · Un envío sin token CSRF se rechaza

- **Trazabilidad:** R-07 · `RNF-03` · Ataque D3-05.
- **Precondiciones:** Sesión de Administrador.
- **Datos de entrada:** El alta de la editorial «Forjada», enviada sin el token CSRF.
- **Pasos:** 1. Se envía el formulario forjado.
- **Resultado esperado:** Responde 403.
- **Postcondiciones:** No existe la editorial «Forjada».
- **Se ejecuta con:** `scripts/demo/ataques.py D3-05`.

### CP-17 · Un cliente no puede tocar el carrito de otro

- **Trazabilidad:** R-07 · `CU-TDA-CRM`, `CU-TDA-CRB` · Ataque D3-06.
- **Precondiciones:** `cliente001` tiene una línea con 2 unidades de un tomo en su carrito. Hay
  una sesión de `cliente002`.
- **Datos de entrada:** La línea de `cliente001`: cambiar la cantidad a 9, y quitarla.
- **Pasos:** 1. `cliente002` envía los dos pedidos sobre la línea ajena.
- **Resultado esperado:** Los dos responden 404.
- **Postcondiciones:** La línea de `cliente001` sigue con 2 unidades.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-06`.

### CP-18 · Un archivo hostil se rechaza, y uno válido se guarda procesado y con nombre propio

- **Trazabilidad:** R-07 · `RNF-05` · `CU-CFG-BNA` · Ataque D3-07.
- **Precondiciones:** Sesión de Administrador.
- **Datos de entrada:** Como imagen de un banner:
  - a) un ejecutable renombrado a `.jpg`;
  - b) un JPEG de 21 MB;
  - c) un SVG con `<script>`;
  - d) un JPEG válido llamado `../../../../config/settings/evil.jpg`.
- **Pasos:** 1. Se sube cada archivo.
- **Resultado esperado:** a), b) y c) se rechazan, cada uno con su mensaje. d) se acepta.
- **Postcondiciones:** d) quedó guardado en WebP, con un nombre generado por el sistema y dentro
  de la carpeta de archivos subidos. No se escribió nada fuera de ella.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-07`.

### CP-19 · Dos cuentas con la misma contraseña no comparten el hash

- **Trazabilidad:** R-07 · `RNF-04` · Ataque D3-08.
- **Precondiciones:** Ninguna.
- **Datos de entrada:** Las cuentas `ana@longbox.demo` y `bruno@longbox.demo`, las dos con la
  contraseña `ClaveSegura123`.
- **Pasos:** 1. Se crean las dos cuentas. 2. Se leen sus credenciales en la base.
- **Resultado esperado:** Los dos hashes PBKDF2 son distintos.
- **Postcondiciones:** La contraseña no aparece en claro en ninguna tabla.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-08`.

### CP-20 · Cambiar el rol de una cuenta, o darla de baja, le corta la sesión abierta

- **Trazabilidad:** R-07 · `CU-USR-MOD`, paso 5 · `CU-USR-BAJ`, paso 4 · `CO-121`, `CO-123` ·
  Ataque D3-09.
- **Precondiciones:** `cajero1` y `cajero2` tienen sesión abierta. Hay una sesión de
  `admin1`.
- **Datos de entrada:** `cajero1`: el rol pasa de Cajero a Administrador. `cajero2`: se da de baja.
- **Pasos:** 1. `admin1` cambia el rol de `cajero1` y da de baja a `cajero2`. 2. Los dos cajeros
  siguen navegando.
- **Resultado esperado:** El siguiente pedido de cada cajero lo lleva al inicio de sesión.
  `cajero2` ya no puede volver a entrar.
- **Postcondiciones:** `cajero1` es Administrador y `cajero2` está Inactivo. Las sesiones de los
  demás usuarios siguen abiertas.
- **Se ejecuta con:** `scripts/demo/ataques.py D3-09`.

### CP-21 · Siempre queda al menos un Administrador activo, aunque dos operen a la vez

- **Trazabilidad:** R-07 · `CU-USR-BAJ` E1 · `CU-USR-MOD` E1 · `CO-121`, `CO-123` · `I-12` ·
  `RNF-06` · Carrera D4-01.
- **Precondiciones:** `admin1` y `admin2` son los únicos Administradores activos, y cada uno
  tiene su sesión.
- **Datos de entrada:**
  - a) cada uno da de baja al otro en el mismo instante;
  - b) cada uno le quita el rol al otro en el mismo instante;
  - c) uno da de baja y el otro quita el rol.
- **Pasos:** 1. Se lanza cada carrera 20 veces.
- **Resultado esperado:** En cada carrera, una operación procede y la otra informa «Debe existir
  al menos un Administrador activo en el sistema.». Ninguna respuesta es un error 500.
- **Postcondiciones:** Queda exactamente un Administrador activo.
- **Se ejecuta con:** `apps/accounts/tests/test_concurrencia_ultimo_administrador.py`.

### CP-22 · El registro de auditoría no se puede alterar, ni siquiera desde la base

- **Trazabilidad:** R-07, R-08 · `CU-AUD-CON` · `I-13` · `RNF-09` · Inmutabilidad (D3-10).
- **Precondiciones:** Existe una entrada de auditoría.
- **Datos de entrada:** Sobre esa entrada:
  - a) modificarla desde la aplicación;
  - b) modificarla con un `UPDATE` sobre la base;
  - c) borrarla con un `DELETE` sobre la base.
- **Pasos:** 1. Se ejecuta cada intento.
- **Resultado esperado:** Los tres se rechazan con «El log de auditoría es inmutable».
- **Postcondiciones:** La entrada sigue idéntica. Las entradas nuevas se siguen registrando.

---

## R-08 · Pérdida de datos
- **Se ejecuta con:** `apps/core/tests/test_inmutabilidad_auditoria_en_la_base.py`.

### CP-23 · Un respaldo se restaura completo

- **Trazabilidad:** R-08 · `RNF-12` · Respaldo y restauración (D6-06).
- **Precondiciones:** La base de la demostración está poblada.
- **Datos de entrada:** `manage.py respaldar_base`. Una base vacía, `longbox_restaurada`.
- **Pasos:** 1. Se genera el respaldo. 2. Se restaura en la base vacía. 3. Se comparan las dos
  bases, tabla por tabla.
- **Resultado esperado:** El respaldo se verifica antes de darse por bueno. Las dos bases tienen el
  mismo número de filas en cada tabla.
- **Postcondiciones:** La base restaurada conserva sus restricciones, incluidas las que existen
  como índice.
- **Se ejecuta con:** `scripts/demo/respaldo.py`.

### CP-24 · Si la base se cae, el sistema no expone nada y se recupera solo

- **Trazabilidad:** R-08 · Base caída (D6-04).
- **Precondiciones:** El servidor corre con la configuración de producción y el catálogo responde
  200.
- **Datos de entrada:** El contenedor de la base, detenido y vuelto a levantar.
- **Pasos:** 1. Se detiene la base y se pide el catálogo. 2. Se levanta la base y se pide otra
  vez, sin reiniciar la aplicación.
- **Resultado esperado:** Con la base caída, el catálogo responde 500 con la página genérica, sin
  traza ni configuración. Al volver la base, responde 200 en menos de un segundo.
- **Postcondiciones:** Ningún dato se perdió.
- **Se ejecuta con:** `scripts/demo/caida_base.py`, con el servidor levantado.

### CP-25 · Una falla técnica a mitad del alta de un lote no deja productos a medias

- **Trazabilidad:** R-08 · `CU-ALT-NAC`, paso 7 · `RNF-06` · Atomicidad (D6-05).
- **Precondiciones:** Sesión de Administrador.
- **Datos de entrada:** Un lote nacional con los tomos 1 y 2 de *Akira*, con una falla técnica
  forzada después de crear los productos, al registrar la auditoría.
- **Pasos:** 1. El Administrador confirma el alta del lote.
- **Resultado esperado:** El alta no se completa.
- **Postcondiciones:** No existe ningún producto del lote ni el lote mismo: la transacción se
  deshizo entera.

---

## Carga y volumen
- **Se ejecuta con:** `apps/catalog/tests/test_alta_lote_nacional.py`, con `-k fallo_tecnico`.

### CP-26 · Con un solo usuario, toda operación interactiva responde en menos de 2 segundos

- **Trazabilidad:** `RNF-02` · Línea base (D5-01).
- **Precondiciones:** La base de la demostración está poblada: 20 000 productos y 500 clientes.
- **Datos de entrada:** Cinco operaciones, 20 veces cada una:
  - la búsqueda `one` en el inventario;
  - la ficha de un producto;
  - la cola de correos;
  - el padrón de clientes;
  - la página 50 de la auditoría.
- **Pasos:** 1. `admin1` ejecuta cada operación 20 veces seguidas.
- **Resultado esperado:** El percentil 95 de cada operación está por debajo de 2 segundos.
- **Postcondiciones:** Queda la medición, que es la referencia de CP-27.
- **Se ejecuta con:** `scripts/demo/linea_base.py`, con el servidor levantado.

### CP-27 · Con 50 sesiones simultáneas, los tiempos no se degradan más de un 20 %

- **Trazabilidad:** `RNF-07` · `RNF-02` · Carga (D5-02).
- **Precondiciones:** La medición de CP-26.
- **Datos de entrada:** 50 usuarios virtuales durante 10 minutos, cada uno con su cuenta:
  - 60 % clientes: catálogo, búsqueda, ficha y carrito;
  - 25 % cajeros: inventario y ficha;
  - 15 % administradores: inventario, cola de correos y auditoría.
- **Pasos:** 1. Se corre `scripts/demo/locustfile.py` con 50 usuarios.
- **Resultado esperado:** Ningún pedido falla. El percentil 95 no supera en más de un 20 % al de
  CP-26, y ninguno pasa de 2 segundos.
- **Postcondiciones:** Ninguna sobre los datos.
- **Se ejecuta con:** `locust -f scripts/demo/locustfile.py --headless -u 50 -r 5 -t 10m --host https://127.0.0.1:8443`, con el servidor levantado.

### CP-28 · Un listado paginado hace las mismas consultas con 10 registros que con 20 000

- **Trazabilidad:** `RNF-02` · Volumen (D5-04).
- **Precondiciones:** Una base con 10 productos y 10 entradas de auditoría, y otra con 20 000
  productos y 100 000 entradas.
- **Datos de entrada:** El inventario, el catálogo público y la auditoría, en su primera página.
- **Pasos:** 1. Se pide cada listado en las dos bases y se cuentan las consultas a la base.
- **Resultado esperado:** Cada listado hace el mismo número de consultas en las dos bases.
- **Postcondiciones:** Ninguna.
- **Se ejecuta con:** `apps/core/tests/test_volumen_consultas.py`.

