> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de construir y **no se reescribe** después: lo que cambie durante el ensayo
> va a la bitácora del módulo. El registro del ensayo (`DEMO-ENSAYO.md`) se retiró el 2026-10-07:
> sus hallazgos están en las bitácoras y sus escenarios, en `docs/pruebas/CASOS_DE_PRUEBA.md`.

# Plan — `00` Demostración de resistencia

**Estado del plan:** Aprobado el 2026-10-04 con las decisiones del apartado 1 bis · **Fecha:** 2026-10-04

La demostración no es un recorrido de pantallas: muestra que el sistema **se rompe bien** ante
entradas absurdas, ataques, concurrencia, carga y dependencias caídas, y que la suite detecta
cuando algo se rompe de verdad. Sólo se demuestra lo que `docs/ESTADO.md` da por construido.

---

## 0. Punto de partida (2026-10-04)

| Qué | Estado |
| --- | --- |
| Casos de uso | 48 verificados, 9 construidos sin verificar, 15 parciales, 31 pendientes (`ESTADO.md`, 2026-10-03) |
| Suite | Última corrida completa: **1812 pruebas, 7 min 44 s, 96 %** (2026-10-03). **La de hoy no se pudo medir**: PostgreSQL está detenido desde el 2026-10-03 21:45 y su servicio arranca en modo manual. Se vuelve a medir apenas esté levantado; ése es el número que se dice |
| PostgreSQL | 18 como servidor (12 y 16 también instalados). `psql`/`pg_dump` no están en el `PATH`: las herramientas los buscan en `C:\Program Files\PostgreSQL\18\bin` |
| Modelo de lenguaje | LM Studio no responde en `127.0.0.1:1234` |
| Docker Desktop | Instalado, motor detenido |
| freezegun | Instalado |
| pytest-xdist, pytest-randomly, locust, mutmut, pip-audit, openpyxl | **No instalados.** Todos tienen versión para Python 3.14 en Windows (verificado con `pip install --dry-run`). Van a `requirements-dev.txt` |
| gunicorn | **No corre en Windows** (depende de `fcntl`). Ver decisión 1 |

---

## 1. Decisiones que necesito antes de construir

| # | Punto | Opciones | Recomiendo |
| --- | --- | --- | --- |
| 1 | **Servidor de producción.** La consigna pide gunicorn, que no corre en Windows | **(a)** `manage.py servir` (waitress), que es el servidor de producción que el proyecto ya usa, con la misma configuración de producción. **(b)** gunicorn dentro de WSL o Docker | **(a)**: es el que se va a usar de verdad, y el guion lo dice |
| 2 | **HTTPS local.** La configuración de producción redirige a HTTPS y marca las cookies como seguras: un cliente de carga por HTTP no puede sostener la sesión | **(a)** Caddy con certificado local (`tls internal`) delante de waitress, en `https://localhost:8443`: la configuración de producción **no se toca**. **(b)** Un `config/settings/demo.py` sin redirección | **(a)** |
| 3 | **Caída de la base (D6-04).** Detener el servicio de PostgreSQL exige una terminal de administrador | **(a)** Terminal de administrador abierta durante la demostración. **(b)** `longbox_demo` en un contenedor PostgreSQL 18 de Docker: se detiene sin permisos y no toca la base de desarrollo | **(b)** si Docker levanta hoy; si no, **(a)** |
| 4 | **I-13, inmutabilidad del log.** Hoy la garantizan `save()` y `delete()` del modelo. `QuerySet.update()`, `QuerySet.delete()` y SQL directo la esquivan. `DEUDA.md` la da por cubierta («La respeta cualquier escritura: Sí»), y eso no es exacto | **(a)** Mañana se muestra como **límite conocido**, se corrige `DEUDA.md` y la solución (un disparador en PostgreSQL que permita sólo el `SET NULL` del actor) va después de la demostración. **(b)** Hacer el disparador hoy | **(a)**: es un cambio de esquema la noche anterior, y la baja de cuentas actualiza esas filas |
| 5 | **I-12, último Administrador.** Leyendo el código: cada transacción bloquea a los *otros* administradores, no al afectado. Si A y B se quitan el rol mutuamente a la vez, se interbloquean; PostgreSQL aborta una de las dos y esa petición termina en error 500. La invariante probablemente se sostiene, pero se rompe **mal** | Se confirma en el ensayo (D4-01) antes de tocar nada. Si se confirma: prueba primero, y después bloquear a todos los administradores activos, incluido el afectado, en orden fijo. Son pocas líneas | Corregir hoy si el ensayo lo confirma |
| 6 | **Las siete mejoras de interfaz** (selects y barras propias, flechas de cantidad, agregar desde la tarjeta, ícono de pausa, filtro en tiempo real, filas por etiqueta en la portada, precio en otra moneda) | **(a)** Después de la demostración, con su plan. **(b)** Hoy las tres chicas: ícono de pausa, flechas de cantidad, estilos de select y barras | **(a)**. Cada cambio la noche anterior es una regresión posible en algo que mañana se muestra. Detalle en el apartado 6 |
| 7 | **Datos de Ivrea.** El sitio publica unas 523 **series**, con título, autor, géneros, demografía, estado y formato. **No** publica ISBN, precio ni la lista de tomos. `robots.txt` lo permite | **(a)** Se raspan las 523 series una vez, con una petición por segundo, y se guardan en `scripts/demo/datos/ivrea.xlsx`. `poblar.py` arma los tomos a partir de ellas, con semilla fija: ISBN-13 sintéticos con dígito verificador válido, precios de la tabla de precios. Sin portadas ni sinopsis: son contenido de Ivrea. **(b)** Datos sintéticos sin Ivrea | **(a)**: nombres reales y etiquetas reales, con lo inventado marcado como sintético |
| 8 | **Casilla de recepción.** La consigna pide un módulo de desarrollo que mande correos a una casilla, y que el sistema la lea en producción. Lo segundo es `CO-016`, el ciclo de monitoreo de `CU-ALT-NOV`: un caso de uso con contrato, que hoy no existe | **(a)** Hoy, sólo el emisor de desarrollo, `scripts/demo/enviar_novedades.py`: arma correos con el formato de novedades de una editorial (una tabla, un producto por fila) a partir del Excel. Los deja como `.eml`, que el sistema ya ingiere con `ingerir_correos`, y opcionalmente los manda por SMTP. `CO-016` (lectura IMAP disparada por el Temporizador) va después, con su plan. **(b)** Construir `CO-016` hoy | **(a)** |
| 9 | **Mutación (D1-03).** mutmut 3 se instala pero no suele correr en Windows nativo. cosmic-ray no se puede instalar en este entorno (conflicto de dependencias) | Se prueba mutmut en el ensayo. Si no corre: en WSL, si está disponible; si no, pasa a Reserva y los sabotajes de D1-02 cubren la idea | Como se describe |

### 1 bis. Lo que decidió el responsable (2026-10-04)

| # | Decisión |
| --- | --- |
| 1 | **(a)** waitress con la configuración de producción |
| 2 | **(a)** Caddy con `tls internal` |
| 3 | **(b)** `longbox_demo` en un contenedor PostgreSQL 18 |
| 4 | **(b)** El disparador de inmutabilidad se hace hoy: «hay que hacer las cosas bien» |
| 5 | De acuerdo: se confirma en el ensayo y, si se confirma, se corrige con la prueba primero |
| 6 | **(b)** Las tres mejoras chicas (ícono de pausa, flechas de cantidad, estilo de selects y barras), **al final**. Las otras cuatro, después de la demostración |
| 7 | **(a)**, **con el contenido real de Ivrea**: sinopsis y portadas de `https://www.ivrea.com.ar/titulo/*`. Son datos de un catálogo público, se usan sólo para la demostración en clase, no se publican y **se eliminan al terminar** |
| 8 | **(a)** Sólo el emisor de desarrollo; `CO-016` queda fuera |
| 9 | mutmut; si no corre en Windows, dentro de un contenedor Linux |

---

## 2. Entorno

| Pieza | Cómo |
| --- | --- |
| Base | `longbox_demo`, nunca la de desarrollo. Todas las herramientas leen `DB_NAME` del entorno y **se niegan a correr** si no es `longbox_demo` |
| Servidor | `manage.py servir` con `config.settings.production`, `DEBUG=False`, estáticos recolectados, Caddy con `tls internal` (decisiones 1 y 2). Cliente y servidor comparten la máquina: el guion lo dice al presentar los números de carga |
| Correo | `EMAIL_HOST` vacío: el correo queda en la consola de `servir`, con el enlace a la vista (B-00-008) |
| `poblar.py` | Semilla fija. 500 clientes, 10 de personal, 20 000 productos (unos 14 000 tomos de las series de Ivrea y 6 000 no editoriales sintéticos), 50 proveedores, 1 000 correos en todos sus estados, 100 000 entradas de auditoría. ISBN con dígito correcto, dos decimales, fechas relativas a hoy. Los productos van uno por uno, no con `bulk_create`: la herencia multitabla no lo admite |
| `restaurar.py` | La instantánea es una base plantilla, `longbox_demo_base`. Restaurar es borrar `longbox_demo` y crearla `TEMPLATE longbox_demo_base`: segundos, no minutos. Se mide en el ensayo |

---

## 3. Escenarios

Marca: **V** en vivo · **E** ensayado (se muestra el resultado guardado) · **R** reserva. Duración
estimada en vivo.

### Acto 1 · Las pruebas prueban

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D1-01 | Suite completa con `-n auto` y orden aleatorio, semilla a la vista. Ensayo con tres semillas | V (corre de fondo) | 1 min |
| D1-02 | `sabotaje.py` sobre un `git worktree` temporal: (1) quitar el mixin de rol de una vista de administración, (2) redondear el coeficiente de importación antes de aplicarlo, (3) quitar el resguardo del último Administrador. Cada uno pone en rojo sus pruebas; si alguno no, se escribe la que falta | V | 3 min |
| D1-03 | Mutación sobre `catalog/precios.py` y `accounts/services.py` (decisión 9) | E | 1 min |
| D1-04 | `COBERTURA.md` regenerado; un contrato (`CO-058`) leído al lado de sus pruebas, postcondición por postcondición | V | 2 min |
| D1-05 | Ruff, Black, Bandit, `check --deploy` y `pip-audit`, con su resultado real | V | 1 min |

### Acto 2 · Casos borde (sobre lo construido)

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D2-01 | Textos: máximo exacto y uno más, sólo espacios, acentos, ñ, 鬼滅の刃, emojis; «One Piece» frente a « one piece » en editorial, tipo, etiqueta y proveedor | V | 2 min |
| D2-02 | ISBN-10 e ISBN-13 con y sin guiones, dígito incorrecto; código de barras y código interno repetidos | V | 2 min |
| D2-03 | Dinero: cero, negativo, máximo del campo y uno más, tres decimales; lote importado donde redondear antes cambia el precio; oferta del 33,33 % y monto fijo igual al precio | V | 2 min |
| D2-04 | Plazos con freezegun: enlace de activación a las 48 h menos un segundo y más un segundo; ventana de intentos; oferta el día de vencimiento a las 23:59 y a las 00:00 en hora argentina | V (como pruebas) | 2 min |
| D2-05 | Duplicados en un mismo lote y contra el catálogo: homónimos que avisan, códigos que bloquean | E | — |
| D2-06 | Bajas con referencias: editorial, tipo con ofertas, etiqueta en uso; lo que la usaba se conserva | E | — |

### Acto 3 · Ataques

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D3-01 | RNF-03: `rutas_protegidas.py` recorre **todas** las rutas con sesión de Cajero, de Cliente y sin sesión, y arma la tabla de códigos; ningún cuerpo de 403 trae datos | V | 2 min |
| D3-02 | `CO-114`: 20 intentos; bloqueo al quinto, entrada en auditoría, la contraseña correcta tampoco entra | V | 1 min |
| D3-03 | `CO-117`: la recuperación responde igual exista o no la cuenta, comparado byte a byte (salvo el token CSRF) | V | 1 min |
| D3-04 | SQL en búsquedas y filtros; `<script>` en producto, etiqueta y proveedor: escapado, nunca ejecutado | V | 2 min |
| D3-05 | POST sin token CSRF: 403 y nada cambia | V | 1 min |
| D3-06 | Recursos ajenos: la línea del carrito de otro (404), el carrito de otra sesión | V | 1 min |
| D3-07 | RNF-05: ejecutable renombrado, imagen de 20 MB, SVG con script, nombre con `../`; lo válido se guarda sólo procesado | V | 2 min |
| D3-08 | RNF-04: dos cuentas con la misma contraseña, consulta directa: hashes distintos | V | 1 min |
| D3-09 | `CO-121`: cambiar el rol de una cuenta corta su sesión en la petición siguiente (dos navegadores) | V | 2 min |
| D3-10 | I-13: modificar y borrar desde el shell. `save()`/`delete()` rechazan; `QuerySet.update()` y SQL **pasan** (decisión 4) | V, como límite | 2 min |
| D3-11 | `pip-audit -r requirements.txt` | V | 1 min |

### Acto 4 · Concurrencia (hilos reales contra PostgreSQL)

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D4-01 | I-12: dos Administradores se quitan el rol o se dan de baja a la vez, 100 repeticiones. Siempre queda uno, **y ninguna respuesta es un 500** (decisión 5) | V (20 rep.) / E (100) | 2 min |
| D4-02 | `CO-017` E1: dos aprobaciones del mismo correo; una procesa y la otra informa el estado | V | 1 min |
| D4-03 | I-16 y `CO-019`: encolar dos veces el mismo `message_id`, reprocesar uno procesado: mismo estado | V | 1 min |
| D4-04 | Doble envío del alta (doble clic): un alta, o la segunda rechazada | V | 1 min |
| D4-05 | **Agregado:** dos pestañas suman el mismo producto al carrito a la vez (bloqueo de `CO-083`): una línea, la suma de las dos | V | 1 min |
| D4-06 | **Agregado:** dos Administradores registran a la vez ofertas solapadas sobre el mismo producto (I-20): una sola queda | V | 1 min |

Cada carrera que pase queda como prueba de contrato de la suite.

### Acto 5 · Carga y volumen

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D5-01 | Línea base con un usuario: búsqueda en el inventario, ficha, listado de correos, listado de cuentas, inicio de sesión | V | 1 min |
| D5-02 | RNF-07: 50 sesiones con locust, mezcla de los tres roles; p50 y p95 por operación, errores, degradación. Éxito: p95 < 2 s y degradación < 20 % | E (10 min) / V (1 min) | 2 min |
| D5-03 | Escalones 50, 100, 200, 400 hasta que p95 pase 2 s o aparezcan errores; cómo se degrada | E | — |
| D5-04 | Volumen: cada listado paginado hace las mismas consultas con 10 que con 20 000 (`django_assert_max_num_queries`). Queda en la suite | V (como pruebas) | 1 min |
| D5-05 | RNF-02: toda operación de más de 1 s muestra el indicador de carga | V | 1 min |

Gráfico en `scripts/demo/salida/`: percentiles por escalón con la línea de los 2 s.

### Acto 6 · Dependencias caídas y recuperación

| Código | Pone a prueba | Marca | Dur. |
| --- | --- | --- | --- |
| D6-01 | Modelo de lenguaje caído: el diagnóstico de `CU-CFG-LLM` tipifica el error; el correo aprobado queda en «Falló el procesamiento» y se puede reprocesar | V | 2 min |
| D6-02 | El modelo responde basura: `llm_falso.py`, un servidor local que contesta JSON roto o datos inventados con forma válida. No se crean borradores falsos | V | 2 min |
| D6-03 | Cotizaciones caídas: respaldo local con su fecha | V | 1 min |
| D6-04 | La base se cae con el servidor andando: página genérica sin detalle; se levanta y responde sin reiniciar la aplicación (decisión 3). La aplicación no reutiliza conexiones (`CONN_MAX_AGE` 0), así que debería volver sola | V | 2 min |
| D6-05 | Atomicidad del lote: una falla forzada a mitad de la confirmación no deja productos. Con su prueba | V (como prueba) | 1 min |
| D6-06 | `respaldar_base`, restauración en una base vacía, recuentos por tabla iguales | E | — |

**Total en vivo estimado: unos 60 minutos**, más D1-01 corriendo de fondo.

---

## 4. Descartes

| Escenario de la consigna | Motivo |
| --- | --- |
| RNF-06, dos compras del último ejemplar | `CU-TDA-CMP` no existe (no hay `Pedido` ni `TransaccionPago`) |
| Recursos ajenos en pedidos, puntos, devoluciones, historial del cliente | Módulos 08, 09, 10 y `CU-CLI-HIS` sin construir |
| Cualquier escenario de caja, ventas presenciales, restock o stock en local | Módulos 05, 06, 14 y 18 sin construir |
| Lectura de la casilla por IMAP | `CO-016` no existe (decisión 8) |

---

## 5. Herramientas (`scripts/demo/`)

No tocan `apps/`. Montan datos, generan carga, simulan fallas y muestran resultados.

| Archivo | Qué hace |
| --- | --- |
| `entorno.py` | Lo común: exige `DB_NAME=longbox_demo`, ubica los binarios de PostgreSQL 18 |
| `raspar_ivrea.py` | Una vez: las 523 series a `datos/ivrea.xlsx`, una petición por segundo, sin imágenes ni sinopsis |
| `poblar.py` | El volumen del apartado 2, con semilla fija |
| `restaurar.py` | Instantánea y restauración por base plantilla |
| `enviar_novedades.py` | Correos de novedades desde el Excel, como `.eml` y opcionalmente por SMTP (decisión 8) |
| `sabotaje.py` | D1-02 en un `git worktree` temporal, que se descarta al terminar |
| `rutas_protegidas.py` | D3-01: todas las rutas, todos los roles, tabla de resultados |
| `ataques.py` | D3-02 a D3-08, cada uno con su veredicto |
| `carreras.py` | D4-01 a D4-06 con hilos reales y N repeticiones |
| `locustfile.py` y `escalones.py` | D5-02 y D5-03, y el gráfico |
| `llm_falso.py` | D6-02 |
| `Caddyfile.demo` | HTTPS local (decisión 2) |

---

## 6. Las mejoras de interfaz pedidas (para después de la demostración)

| Pedido | Qué implica | Riesgo |
| --- | --- | --- |
| Selects y barras de desplazamiento propios | Barras: CSS puro (`scrollbar-color`, `::-webkit-scrollbar`). Selects: `appearance: none` y una flecha propia. Una lista desplegable dibujada a mano necesita JavaScript y accesibilidad de teclado | Bajo (CSS) / medio (lista propia) |
| Flechas de cantidad en la ficha | Botones − / + junto al campo, con el mismo tope de stock | Bajo |
| Agregar al carrito desde la tarjeta | La tarjeta es un enlace entero, y un formulario no puede ir dentro de un enlace: hay que reestructurar la tarjeta | Medio |
| Ícono de pausa y reanudación del carrusel | Cambiar el ícono y la etiqueta según el estado | Bajo |
| Filtro del catálogo en tiempo real | `fetch` con espera de unos 300 ms y reemplazo de la estantería; sin JavaScript sigue el botón «Filtrar» | Medio |
| Filas por etiqueta en la portada | Qué grupos se muestran es contenido de la tienda: lo elige el Administrador en la identidad visual. Es un agregado a `CU-TDA-CAT` y a `CU-CFG-VIS` | Medio |
| Precio de referencia en otra moneda | Toca `CU-PVP-TBA`/`TBM`. Lectura recomendada: se escribe en la moneda, se convierte a pesos con la cotización del día y **se guarda en pesos**; la auditoría anota la cotización usada. Guardar la moneda y recalcular cada día sería un campo nuevo que cambia el comportamiento (regla 3 del dominio) y necesita decisión | Medio, y necesita decisión |

---

## 7. Orden de trabajo (se corta por abajo)

1. Entorno: `longbox_demo`, servidor con HTTPS local, `poblar.py`, `restaurar.py` (y el raspado de Ivrea, si se aprueba la decisión 7).
2. Acto 1 sin mutación.
3. Actos 3 y 4, con la corrección de I-12 si el ensayo la confirma.
4. Acto 5: línea base, 50 sesiones, consultas por volumen.
5. Acto 6.
6. Acto 2 sobre los formularios principales.
7. Mutación, escalones de carga y `enviar_novedades.py`.
