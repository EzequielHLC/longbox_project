> **Tipo: Bitácora.** Registro del ensayo de la demostración de resistencia (plan 00). Se anexa
> a medida que se ensaya; una corrida no se borra aunque la siguiente dé otro resultado.

# Ensayo de la demostración

Cada escenario: lo esperado, lo observado, cuántas corridas y cuánto tardó. Los hallazgos dicen qué
se decidió. La evidencia (salidas, gráficos, capturas) está en `docs/pruebas/demo/`.

---

## Paso 0 · Punto de partida (2026-10-04)

| Qué | Observado |
| --- | --- |
| PostgreSQL de desarrollo | **Detenido** desde el 2026-10-03 21:45 (apagado ordenado); el servicio arranca en modo manual. Lo levantó el responsable. Para mañana: `Set-Service postgresql-x64-18 -StartupType Automatic` |
| Suite completa, en serie | **1811 pasan, 1 falla**, 7 min 50 s, cobertura 97 % (6893 sentencias, 212 sin cubrir) |
| La falla | `test_CO083_el_invitado_crea_un_carrito_de_sesion_con_la_linea` congelaba el reloj en una fecha fija (2026-10-03) y leía la sesión con el reloj real: al día siguiente la sesión estaba vencida. **Prueba dependiente de la fecha.** Corregida: el momento es relativo a la hora real. La misma corrección arregló `test_CO086_sin_carrito_propio…`, que pasaba por la razón equivocada (afirmaba que la sesión no tenía el carrito, y no lo tenía porque estaba vencida entera) |
| Herramientas agregadas a `requirements-dev.txt` | pytest-xdist 3.8.0, pytest-randomly 5.0.0, locust 2.46.6, mutmut 3.8.0, pip-audit 2.10.1, openpyxl 3.1.5 |
| Base de la demostración | `longbox_demo` en un contenedor PostgreSQL 18 (`longbox-demo-db`, puerto 5433), migrada |

---

## Acto 1 · Las pruebas prueban

### D1-01 · Suite en paralelo y en orden aleatorio

| Corrida | Semilla | Resultado | Tiempo |
| --- | --- | --- | --- |
| 1 | 1001 | **1823 pasan**, 0 fallos | 1 min 47 s |

### D1-02 · Sabotaje controlado

`python scripts/demo/sabotaje.py todos`. Esperado: cada sabotaje pone en rojo pruebas de su zona, y el
directorio de trabajo real no cambia.

| Sabotaje | Defecto | Observado | Tiempo |
| --- | --- | --- | --- |
| acceso | El log de auditoría deja de exigir el rol | **2 fallan** (`test_el_rol_equivocado_no_consulta_ni_exporta[cajero]`, `[cliente]`) | 15 s |
| dinero | El CRE se redondea a 2 decimales antes de aplicarlo | **1 falla** (`test_el_cre_se_guarda_con_seis_decimales`) | 19 s |
| invariante | El resguardo del último Administrador deja de proteger | **6 fallan** (`CO121`, `CO123`, `CO198`, `CO202` y dos de baja y modificación) | 56 s |

Directorio real: sin cambios en los tres. **Observación:** el sabotaje de dinero lo detecta una sola
prueba, que mira cuántos decimales se guardan, no el precio final. Se agrega una que mida el efecto
sobre el precio (Acto 2, D2-03).

---

## Acto 3 y 4 · Hallazgos

### D4-01 · Último Administrador bajo concurrencia — **defecto encontrado y corregido**

| | |
| --- | --- |
| Esperado | Siempre queda un Administrador activo, y ninguna respuesta es un 500 |
| Observado antes | La invariante se sostuvo en todas las repeticiones, pero **en las tres carreras** (rol contra rol, baja contra baja, rol contra baja) PostgreSQL detectó un interbloqueo y una de las dos peticiones respondió **500** |
| Causa | El resguardo bloqueaba a los *otros* Administradores: cada transacción tomaba su fila y esperaba la ajena |
| Decisión | Corrección chica y segura, con la prueba primero: se bloquea a todos los Administradores activos en orden de clave (B-13-006) |
| Observado después | `test_concurrencia_ultimo_administrador.py`: 3 pruebas × 10 repeticiones, sin ningún 500, siempre un Administrador. Las 373 pruebas de cuentas siguen en verde |

### D3-10 · Inmutabilidad del log — **límite encontrado y corregido**

| | |
| --- | --- |
| Esperado | Ninguna entrada se modifica ni se borra, por ningún camino (I-13) |
| Observado antes | `save()` y `delete()` rechazaban; `QuerySet.update()`, `QuerySet.delete()` y SQL directo **pasaban** (6 de 8 pruebas en rojo). `DEUDA.md` decía lo contrario |
| Decisión | Del responsable: corregirlo hoy (plan 00, decisión 4). Disparador de PostgreSQL, `core.0023` (B-16-004) |
| Observado después | 8 de 8 en verde: update, delete y SQL directo rechazados con «El log de auditoría es inmutable»; la eliminación de una cuenta sigue funcionando (pone el actor en nulo y conserva el correo) |
| Límite que queda | `TRUNCATE` sobre la tabla. Se dice mañana como límite conocido |

### D3-07 · Archivos hostiles — límite conocido

Las portadas de producto **no** pasan por el procesamiento de RNF-05: es deuda del módulo 01, ya
registrada en el código (`apps/core/imagenes.py`). El escenario se muestra con banners y logo, y
las portadas van al cierre.

---

## Entorno de la demostración (2026-10-04)

| Pieza | Observado |
| --- | --- |
| Base | `longbox_demo` en el contenedor `longbox-demo-db` (PostgreSQL 18, puerto 5433) |
| Datos de Ivrea | `raspar_ivrea.py`: 523 series, una petición por segundo, unos 50 minutos. 35 fallaron en la primera pasada (32 por un nombre de portada que Windows no admite, 3 por pedidos cortados): `--reintentar` las recuperó todas |
| `poblar.py` | 510 cuentas, 20 000 productos (**3827 tomos reales** de 522 series de Ivrea; «Solo Leveling» aparece dos veces y se omitió la segunda), 50 proveedores, 1000 correos por la ingesta real, 100 000 entradas de auditoría. **2 minutos** |
| Hallazgos de `poblar.py` | Los catálogos y las etiquetas que siembran las migraciones chocaban con los nombres del script (se reutilizan); un `grep` al final de la cadena escondió una falla y guardó la instantánea a medio poblar (la cadena pasó a `set -o pipefail`) |
| `restaurar.py` | Instantánea por base plantilla: se guarda en 0,9 s y **se restaura en 1,1 s**. Al ser menos de un minuto, los actos que escriben no necesitan ir al final |
| Servidor | `manage.py servir` (waitress) con los ajustes de producción, detrás de Caddy con `tls internal` en `https://127.0.0.1:8443`. Por HTTP directo, waitress responde 301 a HTTPS |
| TLS | Los clientes de la demostración verifican el certificado contra la autoridad local de Caddy, no apagan la verificación (bandit marcaba `verify=False` como severidad alta) |

---

## Acto 1 · Las pruebas prueban (continuación)

### D1-01 · Suite en paralelo y en orden aleatorio

| Corrida | Semilla | Resultado | Tiempo |
| --- | --- | --- | --- |
| 2 | 2002 | **1823 pasan**, 0 fallos | 1 min 33 s |
| 3 | 3003 | **1823 pasan**, 0 fallos | 1 min 46 s |
| 4 | 4004 (después de la zona horaria) | 1863 pasan, **1 falla**: la prueba nueva de doble clic, intermitente. Llevó a B-17-017 | 1 min 51 s |

Ninguna prueba depende del orden: las tres semillas iniciales dieron el mismo resultado.

### D1-03 · Mutación

mutmut 3.8 no corre en Windows («please use the WSL»). Se corrió en un contenedor
`python:3.14-slim`; Docker Desktop no comparte las carpetas del usuario, así que la copia del
repositorio viaja al contenedor como un tar por la entrada estándar, **sin el `.env`**.

| Módulo | Pruebas | Mutantes | Muertos | Sobrevivientes | Tiempo |
| --- | --- | --- | --- | --- | --- |
| `apps/catalog/precios.py` | `test_precios.py`, `test_alta_lote_importado.py` | 62 | **62** | **0** | 62 s |

### D1-05 · Puertas

| Puerta | Observado en el ensayo | Qué se hizo |
| --- | --- | --- |
| ruff, black | Hallazgos de estilo en las pruebas y herramientas nuevas | Corregidos |
| bandit | 15 hallazgos, todos en `scripts/demo/`: `verify=False` (alta), contraseñas fijas de demostración, `random` para simular carga, `subprocess` | El de severidad alta se resolvió de verdad (verificación contra la autoridad local de Caddy). Los demás, `# nosec` con su motivo en la línea. Resultado: **sin hallazgos** |
| `check --deploy` | Sin advertencias, con producción y con los ajustes de la demostración | — |
| pip-audit | **13 vulnerabilidades conocidas**: 4 en `virtualenv` 21.7.1, 9 en `sqlparse` 0.5.5 (dependencia de Django) | `virtualenv` 21.7.13 (con `python-discovery` 1.6.1) y `sqlparse` 0.6.0. Como Django usa `sqlparse` para partir el SQL de las migraciones, se verificó que la migración del disparador aplica desde cero. Resultado: **sin vulnerabilidades conocidas** |

---

## Acto 2 · Casos borde

`apps/catalog/tests/test_casos_borde.py`, 27 pruebas, en verde.

| Caso | Observado |
| --- | --- |
| Textos no latinos, emoji, máximo y uno más, sólo espacios | Como se esperaba |
| Mayúsculas y espacios sobrantes en un nombre único | Se tratan como el mismo nombre, con el aviso y el enlace |
| ISBN-10 e ISBN-13 con y sin guiones, dígito incorrecto | Como se esperaba. **El primer intento de la prueba tenía mal dos ISBN-10** (el dígito de 84-376-0494 es X, no 2): el sistema tenía razón |
| Precio cero, negativo, tres decimales, texto, un dígito de más | Rechazados sin registrar |
| Importe máximo | El formulario tiene un tope propio, `IMPORTE_MAXIMO` = $ 9.999.999,99, más estricto que la columna: el exacto entra, un centavo más se rechaza |
| CRE con sus decimales | Con los decimales: $ 12.600; redondeado antes: otro precio. Cubre el hueco que dejó ver el sabotaje de dinero |
| **Oferta a las 23:59 del día de vencimiento, en hora argentina** | **Defecto:** no descontaba. `TIME_ZONE` era `UTC` (el valor por defecto de Django, sin decisión registrada): entre las 21:00 y la medianoche el sistema ya creía que era el día siguiente. Corregido: `America/Argentina/Buenos_Aires` (B-03-012). Suite completa en verde después |

---

## Acto 3 · Ataques (primer ensayo, base parcial)

| Escenario | Observado |
| --- | --- |
| D3-01 | 106 rutas, 85 protegidas por rol, 318 pedidos, **0 fallas** |
| D3-02 | El quinto intento fallido activa el bloqueo; desde el sexto, la respuesta dice «bloqueado». Auditado. La contraseña correcta no entra |
| D3-03 | Respuestas idénticas: estado 200, misma redirección, 8079 bytes las dos |
| D3-04 | Búsquedas con SQL: 200. La editorial con `<script>` se guarda como texto y el listado la muestra escapada |
| D3-05 | 403, editoriales 11 → 11 |
| D3-06 | 404 en modificar y quitar; la línea ajena intacta |
| D3-07 | Ejecutable: «El archivo no es una imagen o está dañado.»; 21 MB: «La imagen pesa 21.0 MB y el máximo es 10 MB.»; SVG: rechazado; el válido con nombre `../../…/evil.jpg` quedó como `banners/<uuid>.webp` |
| D3-08 | PBKDF2, hashes distintos, sin la contraseña en claro |
| D3-09 | **El primer ensayo falló por el script**, no por el sistema: intentaba pasar un Cajero a Cliente, rol que el formulario de personal no ofrece. Con el cambio a Administrador: antes 200, después 302 al inicio de sesión |
| D3-10 | `save()`, `update()` y `DELETE` directo rechazados con «El log de auditoría es inmutable»; la entrada sigue intacta |

---

## Acto 4 · Concurrencia

Primer ensayo, 10 repeticiones:

| Carrera | Observado | Decisión |
| --- | --- | --- |
| D4-02 | 10/10, estado final «fallido» (el modelo de lenguaje está apagado), sin 500 | Prueba en la suite: `test_concurrencia_correos.py` |
| D4-03 | Ingesta repetida 10/10. **El reproceso de un procesado le cambió el estado en 10/10** | **No es defecto:** `CO-019` permite reprocesar un Procesado y lo deja en Procesado o Falló. La expectativa del escenario estaba mal escrita; manda el contrato. El escenario ahora verifica lo que `CO-019` declara |
| D4-04 | **Defecto:** una sola editorial siempre, pero **6 de 10 dobles envíos respondieron 500** | Corregido (B-17-016); el alta de proveedor tenía el mismo defecto (B-04-006). Al repetir la prueba apareció un tercer camino, con el formulario de vuelta sin explicación (B-17-017) |
| D4-05 | 10/10, una línea con la suma, sin 500 | Prueba en la suite: `test_concurrencia_carrito.py` |
| D4-06 | 10/10, una sola oferta, sin 500 | Prueba en la suite: `test_concurrencia_ofertas.py` |

Segundo ensayo, 20 repeticiones, después de las correcciones: **5 de 5 carreras correctas, 0
respuestas 500**.

---

## Acto 5 · Volumen

### D5-04 · Consultas por página con pocos y con muchos registros

`apps/core/tests/test_volumen_consultas.py`, 8 listados. La primera versión de la prueba comparaba
mal (la primera petición carga cosas una sola vez); con una petición de calentamiento, los siete
listados del mostrador quedan constantes.

**Defecto:** el catálogo público pasaba de 8 a 15 consultas: la tarjeta leía la marca de cada
artículo no editorial, que no venía en la consulta (N+1). Corregido (B-07-007): constante.

---

## Acto 6 · Dependencias caídas (primer ensayo, base parcial)

| Escenario | Observado |
| --- | --- |
| D6-01 | Diagnóstico: «El servicio no respondió…» en 2,1 s; el correo queda «fallido» con su motivo |
| D6-02 roto | «fallido», «El modelo respondió algo que no se pudo interpretar» |
| D6-02 inventado | Borrador «Extracción incompleta» con ISBN, precio y fecha descartados, cada uno con su reparo. **Productos 20 000 → 20 000** |
| D6-04 | Base detenida: 500 genérico, 145 bytes, nada interno. Base levantada: 200 a los 0,1 s, sin reiniciar la aplicación (`CONN_MAX_AGE` 0) |
| D6-06 | Respaldo de 3,2 MB en 1,2 s, restaurado en 0,6 s; 38 tablas, 155 932 filas, todas iguales |
