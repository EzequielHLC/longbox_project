> **Tipo: Normativo.** El guion de la demostración de resistencia (plan 00). Cada número que se
> dice en voz alta sale del ensayo registrado en [DEMO-ENSAYO.md](DEMO-ENSAYO.md), no de memoria.

# Demostración de resistencia — guion

**La idea, para abrir:** no se trata de que el sistema no se rompa nunca, sino de que se rompa
**bien**. Ante una entrada absurda, un ataque o una dependencia caída tiene que rechazar con un
mensaje claro, no dejar datos a medias, no exponer información y recuperarse solo. Y la suite de
pruebas tiene que darse cuenta cuando algo se rompe de verdad.

**Duración total en vivo: unos 60 minutos**, más la suite corriendo de fondo desde el principio.

Todos los comandos se corren desde la raíz del repositorio, con el entorno virtual activado.
**Cliente y servidor comparten la máquina:** los números de carga miden el sistema más la
herramienta que genera la carga.

---

## Antes de empezar (a la mañana, 15 minutos)

1. **Servicios.**
   - Docker Desktop abierto. `docker start longbox-demo-db`.
   - PostgreSQL de desarrollo arriba (lo usa la suite): `Get-Service postgresql-x64-18` dice
     `Running`. Si no, en PowerShell como administrador: `Start-Service postgresql-x64-18`.
   - LM Studio **apagado** (el Acto 6 lo necesita caído).
2. **Base en el punto de partida:** `python scripts/demo/restaurar.py` (1 segundo).
3. **Servidor como el de producción**, en dos terminales:
   - Terminal 1: `python scripts/demo/manejar.py servir` (waitress, `DEBUG=False`).
   - Terminal 2: `caddy run --config scripts/demo/Caddyfile.demo` (HTTPS en `https://127.0.0.1:8443`).
4. **Navegadores**, uno por rol, en perfiles separados o ventanas de incógnito. Todas las cuentas
   tienen la contraseña `Demo-2026!`:
   - Administrador: `admin1@longbox.demo`
   - Cajero: `cajero1@longbox.demo`
   - Cliente: `cliente001@longbox.demo`
   El navegador va a advertir que el certificado es local: se acepta una vez.
5. **Terminal 3**, la de los comandos del guion. **Terminal 4**, la de la suite (Acto 1).
6. **Verificación rápida:** `python scripts/demo/ensayo.py --rapido` (unos 3 minutos). Corre un
   escenario corto de cada acto, restaura la base y termina con una tabla: todo tiene que decir OK.
   Si algo falla, se usa el plan B de ese escenario.

**Correos:** no hay servidor de correo en la demostración. Cada correo (activación,
recuperación, bloqueo) aparece completo en la Terminal 1, con su enlace a la vista para copiarlo.

---

## Acto 1 · Las pruebas prueban (10 minutos)

**D1-01 · La suite, en paralelo y en orden aleatorio.** Se lanza al principio en la Terminal 4 y
se vuelve a ella al final:

    python -m pytest -n auto --randomly-seed=<una semilla que diga el público> -q --no-cov

Qué se ve: la semilla en el encabezado, y al final **1890 pasan, 0 fallan**, en unos 2 minutos.
Se ensayó con cuatro semillas distintas; ninguna prueba depende del orden. Plan B:
`docs/pruebas/demo/suite.txt`.

**D1-02 · Sabotaje controlado.** Se rompe el sistema a propósito en una copia, y la suite lo detecta:

    python scripts/demo/sabotaje.py acceso
    python scripts/demo/sabotaje.py dinero
    python scripts/demo/sabotaje.py invariante

| Sabotaje | Qué se rompe | Qué tiene que pasar |
| --- | --- | --- |
| acceso | El log de auditoría deja de exigir el rol de Administrador | 2 pruebas en rojo: el Cajero y el Cliente entran |
| dinero | El coeficiente de importación se redondea antes de aplicarlo | 1 prueba en rojo |
| invariante | El resguardo del último Administrador deja de proteger | 6 pruebas en rojo |

Al final de cada uno el script dice «Directorio de trabajo real: sin cambios». Unos 30 segundos
cada uno. Plan B: `docs/pruebas/demo/sabotaje.txt`.

**D1-03 · Mutación (ensayado).** mutmut no corre en Windows: se corrió en un contenedor Linux
(`python scripts/demo/mutacion.py precios`). Sobre el cálculo de precios: **62 mutantes, 62
muertos, 0 sobrevivientes**. Se muestra `docs/pruebas/demo/mutacion_precios.txt`.

**D1-04 · Trazabilidad.** Se abre [COBERTURA.md](COBERTURA.md): cuántos contratos tienen prueba.
Se elige `CO-058 confirmarBajaDeOferta` y se lee al lado de
`apps/catalog/tests/test_contratos_03_ofertas.py`: cada postcondición, incluida la negativa (el
precio guardado del producto no cambia), tiene su `assert`.

**D1-05 · Las puertas.** `ruff check .`, `black --check .`,
`bandit -r apps config scripts -x "*/tests/*,*/migrations/*"`,
`python scripts/demo/manejar.py check --deploy --fail-level WARNING` y
`pip-audit -r requirements.txt`. Todas sin hallazgos (ver el registro del ensayo para los que
aparecieron hoy y cómo se resolvieron).

---

## Acto 2 · Casos borde (8 minutos)

Se muestran como pruebas, que corren en segundos:

    python -m pytest apps/catalog/tests/test_casos_borde.py -v --no-cov -p no:randomly

Qué se ve, caso por caso:
- **Textos:** «Ñandú», «鬼滅の刃» y un emoji se guardan tal cual; el máximo exacto entra y uno
  más no; sólo espacios se rechaza; «One Piece Press» y «  one   PIECE press » son el mismo nombre.
- **Códigos:** ISBN-10 e ISBN-13 con y sin guiones; el dígito verificador incorrecto se rechaza
  con su motivo; código interno y código de barras repetidos se bloquean.
- **Dinero:** cero, negativo, tres decimales, texto y un dígito de más se rechazan sin registrar
  nada; el importe máximo exacto entra y un centavo más no; el coeficiente de importación conserva
  sus decimales hasta el precio final.
- **Plazos:** una oferta descuenta a las 23:59 del día de vencimiento, en hora argentina, y no a
  las 00:00. **Este caso encontró un defecto hoy** (ver el cierre).

En vivo, en el navegador del Administrador: dar de alta la editorial «鬼滅の刃 Ediciones» y después
«  鬼滅の刃 EDICIONES »: la segunda avisa que ya existe, con el enlace a la primera.

---

## Acto 3 · Ataques (12 minutos)

**D3-01 · El rol equivocado, en todas las direcciones.**

    python scripts/demo/rutas_protegidas.py

Recorre **todas** las rutas del sistema (106) con tres visitantes: sin sesión, Cliente y Cajero.
Esperado: **85 rutas protegidas, 318 pedidos, 0 fallas**; cada 403 sin datos en el cuerpo. La tabla
completa queda en `scripts/demo/salida/rutas_protegidas.md` (plan B:
`docs/pruebas/demo/rutas_protegidas.md`).

**D3-02 a D3-09 · Ataques con veredicto.**

    python scripts/demo/ataques.py

| Código | Ataque | Qué se ve |
| --- | --- | --- |
| D3-02 | 20 inicios de sesión fallidos | El quinto activa el bloqueo, queda en auditoría, y la contraseña correcta tampoco entra |
| D3-03 | Recuperar contraseña de una cuenta que existe y de una que no | Respuestas idénticas byte a byte (8079 bytes las dos) |
| D3-04 | SQL en las búsquedas y `<script>` en un nombre | Búsquedas 200; el nombre se guarda como texto y se muestra escapado |
| D3-05 | POST sin token CSRF | 403 y ninguna editorial nueva |
| D3-06 | Tocar la línea del carrito de otro cliente | 404 y la línea ajena intacta |
| D3-07 | Ejecutable renombrado, imagen de 21 MB, SVG con script, nombre con `../` | Los tres rechazados con su mensaje; el válido guardado en WebP con nombre propio |
| D3-08 | Dos cuentas con la misma contraseña | Hashes PBKDF2 distintos, sin la contraseña en claro |
| D3-09 | Cambiar el rol de una cuenta con sesión abierta | Su próxima petición va al inicio de sesión |

Esperado: **8 de 8 OK**. Plan B: `docs/pruebas/demo/ataques.md`. Después: `python scripts/demo/restaurar.py`.

**D3-10 · La inmutabilidad del log.** En `python scripts/demo/manejar.py shell`:

    from apps.core.models import RegistroAuditoria as R
    e = R.objects.first()
    e.detalle = "alterado"; e.save()                          # rechazado por el modelo
    R.objects.filter(pk=e.pk).update(detalle="alterado")      # rechazado por la base
    from django.db import connection
    connection.cursor().execute("DELETE FROM core_registroauditoria WHERE id = %s", [e.pk])  # rechazado por la base

Los tres terminan en «El log de auditoría es inmutable». **Hasta esta mañana los dos últimos
pasaban**: se corrigió hoy con un disparador de PostgreSQL (ver el cierre). Límite que queda:
`TRUNCATE`, que exige ser el dueño de la tabla.

**D3-11 · Dependencias.** `pip-audit -r requirements.txt`: **sin vulnerabilidades conocidas**.
Hoy aparecieron 13 (virtualenv y sqlparse) y se actualizaron.

---

## Acto 4 · Concurrencia (8 minutos)

    python scripts/demo/carreras.py --veces 20
    python -m pytest apps/accounts/tests/test_concurrencia_ultimo_administrador.py --no-cov -p no:randomly -v

Hilos reales contra PostgreSQL, soltados juntos por una barrera. En todas, el criterio es doble:
el efecto declarado se cumple **y ninguna respuesta es un 500**.

| Código | Carrera | Esperado |
| --- | --- | --- |
| D4-01 | Dos Administradores se quitan el rol o se dan de baja a la vez | Siempre queda uno, sin 500. **Encontró un defecto hoy** |
| D4-02 | Dos aprobaciones del mismo correo | Una procesa, la otra informa el estado |
| D4-03 | El mismo correo dos veces; reprocesar uno procesado | Una sola fila; el reproceso sigue a `CO-019` |
| D4-04 | Doble clic en el alta de una editorial | Una sola editorial, sin 500. **Encontró un defecto hoy** |
| D4-05 | Dos pestañas suman el mismo producto al carrito | Una línea con la suma |
| D4-06 | Dos ofertas solapadas a la vez | Una sola oferta; la otra informa el conflicto |

Todas quedaron también como pruebas de la suite. Después: `python scripts/demo/restaurar.py`.

---

## Acto 5 · Carga y volumen (10 minutos)

**D5-01 · Línea base, un solo usuario:** `python scripts/demo/linea_base.py`.

**D5-02 · 50 sesiones (RNF-07).** En vivo, la corrida corta de un minuto:

    locust -f scripts/demo/locustfile.py --headless -u 50 -r 10 -t 1m --host https://127.0.0.1:8443 --only-summary

La corrida completa de 10 minutos es la evidencia (`docs/pruebas/demo/carga_50.txt`). Los números
y la comparación con la línea base están en [DEMO-ENSAYO.md](DEMO-ENSAYO.md), Acto 5. **Se dice
el número real aunque no cumpla:** la degradación relativa supera el 20 % que pide RNF-07, con
tiempos absolutos muy por debajo de los 2 segundos de RNF-02.

**D5-03 · Hasta dónde llega (ensayado).** Se muestra el gráfico
`docs/pruebas/demo/carga_escalones.svg`: percentiles por escalón de 50, 100, 200 y 400 sesiones,
con la línea de los 2 segundos.

**D5-04 · Volumen sin degradación.** Con 20 000 productos y 100 000 entradas de auditoría, cada
listado paginado hace las mismas consultas que con diez registros:

    python -m pytest apps/core/tests/test_volumen_consultas.py -v --no-cov -p no:randomly

**Encontró un defecto hoy:** el catálogo público hacía una consulta por cada artículo no
editorial (ver el cierre).

**D5-05 · Indicador de carga (Reserva, no ensayado).** El indicador aparece en toda navegación y
en todo envío de formulario del mostrador, sin esperar un segundo: con respuestas de 50 ms casi no
se ve. Para mostrarlo, en el navegador del Administrador: herramientas de desarrollo → Red →
«Slow 3G», y clic en «Inventario». Las descargas (exportaciones) no lo muestran, a propósito: no
cambian de pantalla. No se pudo ensayar desde la consola; se dice así si se muestra.

---

## Acto 6 · Dependencias caídas y recuperación (10 minutos)

**D6-01 y D6-02 · El modelo de lenguaje caído, o respondiendo basura.**

    python scripts/demo/modelo_caido.py

1. Caído: el diagnóstico dice «El servicio no respondió»; el correo aprobado queda en «Falló el
   procesamiento» con su motivo, y se puede reprocesar.
2. JSON roto: falla con «El modelo respondió algo que no se pudo interpretar».
3. Datos inventados con forma válida: el borrador queda en «Extracción incompleta», con el ISBN,
   el precio y la fecha descartados, cada uno con su reparo.
4. **Productos en el catálogo: 20 000 → 20 000.** El modelo propone, nunca aplica.

Se dice también el límite: un título inventado pero verosímil no se puede verificar; queda como
borrador que una persona tiene que confirmar. Después: `python scripts/demo/restaurar.py`.

**D6-03 · Cotizaciones caídas.** `python -m pytest apps/core/tests/test_cotizaciones.py -v --no-cov -p no:randomly`:
sin la API se usa el respaldo local, que informa su fecha.

**D6-04 · La base de datos se cae con el servidor andando.**

    python scripts/demo/caida_base.py

Se detiene el contenedor de la base: el catálogo responde 500 con la página genérica (145 bytes,
sin traza ni configuración). Se levanta: vuelve a responder 200 en menos de un segundo, sin
reiniciar la aplicación.

**D6-05 · Atomicidad.** `python -m pytest apps/catalog/tests/test_alta_lote_nacional.py -k fallo_tecnico -v --no-cov -p no:randomly`:
una falla forzada a mitad del lote no deja ningún producto.

**D6-06 · Respaldo y restauración (ensayado).** `python scripts/demo/respaldo.py`: 38 tablas, mismo
recuento fila por fila en la base restaurada.

---

## Cierre · Lo que no está, y lo que encontramos (5 minutos)

**Lo que se encontró preparando esta demostración, y se corrigió hoy**, cada uno con su prueba
escrita antes y su entrada de bitácora:

| Defecto | Cómo se rompía | Bitácora |
| --- | --- | --- |
| El último Administrador, bajo concurrencia | Interbloqueo: la invariante se sostenía, pero una petición daba 500 | B-13-006 |
| El log se podía alterar con SQL | `update()` y `DELETE` directos pasaban | B-16-004 |
| Doble clic en altas de catálogos y proveedores | Error 500 por la restricción de unicidad | B-17-016, B-17-017, B-04-006 |
| El catálogo público con muchos productos | Una consulta por cada artículo no editorial | B-07-007 |
| El sistema contaba los días en UTC | Las ofertas vencían a las 21:00 | B-03-012 |
| Una prueba dependiente de la fecha | Empezaba a fallar al día siguiente | DEMO-ENSAYO, Paso 0 |
| Dependencias con vulnerabilidades | virtualenv y sqlparse | DEMO-ENSAYO, D3-11 |

**Límites conocidos, que no se corrigieron hoy:**
- RNF-07: la degradación con 50 sesiones supera el 20 % relativo, en esta máquina compartida.
- Las portadas de producto no pasan por el procesamiento de imágenes de RNF-05 (deuda del módulo 01).
- `TRUNCATE` sobre el log de auditoría no lo frena el disparador.
- No se ensayaron las carreras de unicidad en el alta de productos y en el registro de clientes
  (`DEUDA.md`).
- `requirements.txt` mezcla las dependencias de producción con las de desarrollo.

**Lo que no se mostró porque no está construido:** la compra online y los pedidos (sin `Pedido`
ni `TransaccionPago`), la caja y las ventas presenciales, restock, devoluciones, puntos y stock en
local, y la lectura de la casilla de correo por IMAP (`CO-016`). El estado completo está en
[ESTADO.md](../ESTADO.md).

**Y para terminar, la Terminal 4:** la suite que se lanzó al principio, con su semilla, en verde.
