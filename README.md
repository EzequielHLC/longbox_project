# LongBox · Comic Store Manager

Sistema de gestión integral para Shibuya Comic Store, una comiquería: tienda online, mostrador del local
y administración en un solo sistema. Catálogo de material editorial y no editorial, precios de
importados calculados desde el costo de origen, pre-ventas, proveedores con novedades leídas por un
modelo de lenguaje, restock, pedidos, devoluciones, puntos, caja, reportes, auditoría inmutable y
cuentas por rol.

**Versión 1.0** · noviembre de 2026 · cierre de la iteración de Construcción C1.

---

## Proyecto académico

Trabajo Final de la carrera **Analista en Sistemas de Computación**, de **Pulikoski, Mauricio
Ezequiel**, para la Facultad de Ciencias Exactas, Químicas y Naturales de la Universidad Nacional de
Misiones.

El desarrollo sigue el Proceso Unificado. El Documento de Análisis y Especificación de Requisitos
(versión 14) declara los casos de uso, sus diagramas de secuencia de sistema y los contratos de
operación; el código los implementa, y cada contrato tiene al menos una prueba que lleva su código
en el nombre (`test_CO013_…`). Sostener esa correspondencia entre documento y código es parte del
trabajo.

---

## Qué hace

| Rol | Dónde trabaja | Qué puede hacer |
| --- | --- | --- |
| **Cliente** | La tienda | Comprar con envío o retiro, reservar pre-ventas, pagar con puntos, anotarse en avisos de stock, decidir ante un artículo demorado, pedir el envío de lo guardado en el local, reclamar un defecto |
| **Cajero** | El mostrador | Cobrar ventas con lector de códigos y canje de puntos, cerrar la caja, entregar lo que los clientes tienen guardados, consultar el inventario |
| **Administrador** | La administración | Todo lo anterior, más catálogo, lotes nacionales e importados, borradores del modelo de lenguaje, precios y ofertas, proveedores, restock, llegadas y demoras, pedidos, devoluciones, configuración de la tienda, cuentas, reportes, auditoría y avisos por Telegram |

El modelo de lenguaje **propone y nunca aplica**: lee los correos de novedades de las editoriales y
arma borradores, que un Administrador confirma.

---

## Tecnología

| | |
| --- | --- |
| Lenguaje y framework | Python 3.14 · Django 6.0 |
| Base de datos | PostgreSQL 18 |
| Interfaz | Plantillas de Django, CSS propio (sistema visual «Viñeta Nocturna», sin framework) y JavaScript sin dependencias |
| Servidor | `waitress` detrás de Caddy, que termina el HTTPS y sirve los archivos estáticos |
| Procesos periódicos | Un comando por minuto (`manage.py cada_minuto`) y el temporizador diario, con timers de systemd |
| Integraciones | MercadoPago (con una pasarela de prueba propia), modelo de lenguaje con API compatible con OpenAI (local con LM Studio o remoto), casilla IMAP de novedades, SMTP, bot de Telegram, Georef (localidades argentinas), cotizaciones de monedas |
| Pruebas | pytest, pytest-django, pytest-xdist, factory_boy, freezegun, coverage; locust y scripts propios para la resistencia |
| Calidad | Ruff, Black, Bandit, pip-audit, pre-commit y GitHub Actions |

---

## Estructura

```text
config/              ajustes (base, development, production), URLs, Caddy y unidades de systemd
apps/
  accounts/          cuentas, roles, ingreso, recuperación y activación
  catalog/           productos, lotes, borradores, editoriales, tipos, formatos, etiquetas, precios y ofertas
  suppliers/         proveedores, correos de novedades, pedidos a proveedores y llegadas
  restock/           propuestas de reposición y avisos de stock
  tienda/            carrito y compra online, pasarelas de pago
  ventas/            mostrador
  caja/              cierres de caja
  pedidos/           pedidos de clientes, pre-ventas y demoras
  almacen/           artículos guardados en el local
  devoluciones/      reclamos, cambios y reembolsos
  puntos/            lotes y movimientos de puntos
  reportes/          reportes operativos
  avisos/            canales de aviso y bot de Telegram
  core/              tienda pública, panel, auditoría, configuración, servicios externos
templates/  static/  plantillas y estilos comunes
scripts/             despliegue y herramientas de demostración
docs/                documentación en PDF, estado, deuda, planes, pruebas y despliegue
bitacora/            decisiones tomadas durante la construcción
```

---

## Instalación local

Requisitos: Python 3.14, PostgreSQL 18 y Git.

```powershell
git clone <url-del-repositorio> longbox
cd longbox
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

Crear en PostgreSQL la base y el usuario, con permiso `CREATEDB` (la suite crea una base temporal),
y un archivo `.env` en la raíz:

```ini
SECRET_KEY=una-clave-larga-y-aleatoria
DB_NAME=longbox
DB_USER=longbox_user
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
```

Las demás variables son opcionales y tienen valores por omisión: correo saliente (`EMAIL_*`,
`DEFAULT_FROM_EMAIL`), casilla de novedades (`CASILLA_*`), modelo de lenguaje (`LLM_URL`,
`LLM_MODELO`, `LLM_API_KEY`, `LLM_TIMEOUT`, `LLM_TEMPERATURA`), `MERCADOPAGO_ACCESS_TOKEN`,
`TELEGRAM_BOT_TOKEN`, `URL_PUBLICA`, `RESPALDOS_DIR` y, en producción, `ALLOWED_HOSTS`. Sin ellas,
el sistema funciona con la pasarela de prueba y sin casilla de novedades. Cada correo que envía deja además una copia en la consola.

```powershell
python manage.py migrate
python manage.py crear_administrador_inicial
python manage.py runserver
```

La primera cuenta de Administrador se crea por consola; las demás, desde la administración. No hay
admin de Django ni superusuarios: ninguna escritura ocurre fuera de una operación especificada.

---

## Pruebas y calidad

```powershell
pytest -n auto                 # la suite, con cobertura sobre apps/
ruff check .
black --check .
bandit -r apps config scripts -x "*/tests/*,*/migrations/*"
pip-audit -r requirements.txt
python manage.py check --deploy --settings=config.settings.production
```

Un caso de uso está terminado cuando pasa las **siete puertas**: suite sin fallos, una prueba por
contrato, cobertura de al menos 80 %, análisis estático, formato, seguridad y configuración de
despliegue. Al cierre de la versión 1.0: 4031 pruebas, todas pasan, 97 % de cobertura, y los 258
contratos del documento con su prueba.

- Cómo se escribe una prueba: [`docs/pruebas/ESPECIFICACION.md`](docs/pruebas/ESPECIFICACION.md).
- Los casos de prueba por riesgo: [`docs/pruebas/CASOS_DE_PRUEBA.md`](docs/pruebas/CASOS_DE_PRUEBA.md).
- Cada prueba y si pasa: [`docs/pruebas/CATALOGO.md`](docs/pruebas/CATALOGO.md).
- Qué contrato cubre cada prueba: [`docs/pruebas/COBERTURA.md`](docs/pruebas/COBERTURA.md).

Los scripts de `scripts/demo/` ejercitan el sistema real sobre una base de demostración de 20 000
productos: ataques, carreras de concurrencia, carga con locust, caída de la base, respaldo y
restauración. `python scripts/demo/ensayo.py` los corre todos.

GitHub Actions corre las mismas puertas en cada push a `main` y `develop`
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

---

## Despliegue

En producción el sistema corre con `manage.py servir` (waitress) en `127.0.0.1:8000`, detrás de
Caddy, con PostgreSQL local y los timers de `config/systemd/` para el minuto, el temporizador diario
y el respaldo. La guía, con sus tres rutas (máquina virtual en Azure, túnel de Cloudflare y nombre
dinámico), está en [`docs/despliegue/DEMOSTRACION.md`](docs/despliegue/DEMOSTRACION.md); los
respaldos, en [`docs/despliegue/RESPALDOS.md`](docs/despliegue/RESPALDOS.md).

---

## Documentación

| Qué | Dónde |
| --- | --- |
| Estado de cada caso de uso | [`docs/ESTADO.md`](docs/ESTADO.md) |
| Deuda y decisiones abiertas | [`docs/DEUDA.md`](docs/DEUDA.md) |
| Documento de Análisis y manuales | [`docs/documentacion/`](docs/documentacion/) |
| Planes por módulo | [`docs/planes/`](docs/planes/) |
| Decisiones de construcción | [`bitacora/`](bitacora/) |

El Documento de Análisis, el Manual de Usuario y el Manual de Pruebas están en PDF en
[`docs/documentacion/`](docs/documentacion/).

---

## Autor

**Pulikoski, Mauricio Ezequiel** · Analista en Sistemas de Computación
Facultad de Ciencias Exactas, Químicas y Naturales · Universidad Nacional de Misiones
