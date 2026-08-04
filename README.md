# Longbox

Sistema de gestión integral para comiquerías: catálogo, ventas presenciales y online, pricing de importaciones, proveedores, restock, devoluciones, fidelización por puntos, caja, reportes, auditoría y administración de usuarios por rol.

![image](https://tenor.com/es-AR/view/smug-cat-smug-cat-smirk-smirking-cat-gif-12852186842938363616.gif)

---

## Proyecto académico

Este repositorio corresponde a un Trabajo Final de la carrera **Analista de Sistemas de Computación**, desarrollado por **Pulikoski, Mauricio Ezequiel** para la **Facultad de Ciencias Exactas Químicas y Naturales — Universidad Nacional de Misiones**.

El desarrollo sigue un proceso basado en el Proceso Unificado (UP), con documentación de casos de uso, diagramas de secuencia para los flujos de mayor complejidad y matriz de rastreabilidad de requisitos funcionales y no funcionales.

---

## Stack tecnológico

- **Lenguaje:** Python 3.14
- **Framework:** Django
- **Base de datos:** PostgreSQL
- **Estilos:** Tailwind CSS
- **Tareas asíncronas/programadas:** Celery + Redis
- **Pasarela de pagos:** MercadoPago
- **Testing:** pytest, pytest-django, factory_boy, coverage
- **Calidad de código:** Ruff, Black, Bandit, pre-commit
- **Integración continua:** GitHub Actions

---

## Estructura del proyecto

```
longbox_project/
  config/
    settings/
      base.py
      development.py
      production.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    accounts/        # Autenticación y gestión de usuarios (modelo de usuario custom)
    catalog/          # Catálogo de productos
    pricing/            # Precios nacionales e importados
    suppliers/            # Proveedores
    sales/                   # Ventas presenciales y caja
    store/                     # Tienda online
    returns/                     # Devoluciones
    loyalty/                       # Puntos de fidelización
    reports/                         # Reportes y auditoría
    core/                              # Utilidades compartidas
  requirements.txt
  requirements-dev.txt
  pyproject.toml
  pytest.ini
  .pre-commit-config.yaml
  .github/
    workflows/
      ci.yml
```

---

## Requisitos previos

- Python 3.14 o superior
- PostgreSQL 16 o superior
- Git for Windows (si se trabaja en Windows, necesario para que pre-commit funcione correctamente)

---

## Instalación y configuración local

1. Clonar el repositorio y crear el entorno virtual:
   ```
   git clone <url-del-repositorio>
   cd longbox_project
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Crear la base de datos en PostgreSQL y otorgar los permisos necesarios (base, esquema `public` y `CREATEDB` para las bases temporales de testing).

4. Crear un archivo `.env` en la raíz con las variables de entorno (ver sección siguiente).

5. Aplicar migraciones y correr el servidor:
   ```
   python manage.py migrate
   python manage.py runserver
   ```

6. Activar los hooks de calidad de código:
   ```
   pre-commit install
   ```

---

## Variables de entorno

El archivo `.env` (no versionado) debe definir:

```
SECRET_KEY=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

---

## Testing

Ejecutar la suite completa con reporte de cobertura:
```
pytest
```

La cobertura mínima exigida en el pipeline de integración continua es del 80% sobre el paquete `apps/`.

---

## Calidad de código

El proyecto usa Ruff (lint), Black (formateo) y Bandit (análisis de seguridad estático). Estas herramientas corren automáticamente antes de cada commit mediante pre-commit, y se revalidan en cada push mediante GitHub Actions.

Para correrlas manualmente:
```
ruff check .
black --check .
bandit -r apps
```

---

## Integración continua

Cada `push` o Pull Request contra las ramas `main` y `develop` dispara un workflow de GitHub Actions que:

- Levanta una instancia de PostgreSQL como servicio
- Instala dependencias
- Corre Ruff y Black en modo verificación
- Ejecuta la suite de tests con cobertura mínima exigida
- Publica el reporte de cobertura como artefacto del workflow

El workflow se encuentra en `.github/workflows/ci.yml`.

---

## Autor

**Pulikoski, Mauricio Ezequiel**
Analista de Sistemas de Computación
Facultad de Ciencias Exactas Químicas y Naturales — Universidad Nacional de Misiones