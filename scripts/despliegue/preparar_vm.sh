#!/usr/bin/env bash
# Deja la VM lista para recibir el sistema (docs/despliegue/DEMOSTRACION.md, ruta VM).
#
# Se corre una vez, como el usuario de la VM, después de `crear_vm_azure.ps1`:
#
#   ssh ... 'bash -s' < scripts/despliegue/preparar_vm.sh
#
# Instala las mismas versiones que la máquina de desarrollo —PostgreSQL 18 y
# Python 3.14—, Caddy, y deja PostgreSQL ajustado a 1 GiB de memoria. No toca el
# código ni la base: eso lo hace `instalar_en_vm.sh`.
set -euo pipefail

sudo apt-get update -q
sudo apt-get install -yq curl ca-certificates gnupg software-properties-common debian-keyring \
    debian-archive-keyring apt-transport-https

# PostgreSQL 18, del repositorio oficial: Ubuntu 24.04 trae la 16, y un volcado de
# la 18 no se restaura en una versión anterior.
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    https://www.postgresql.org/media/keys/ACCC4CF8.asc
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt noble-pgdg main" \
    | sudo tee /etc/apt/sources.list.d/pgdg.list >/dev/null

# Python 3.14: el proyecto se desarrolla y se prueba con esa versión.
sudo add-apt-repository -y ppa:deadsnakes/ppa

# Caddy, del repositorio oficial.
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | sudo gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
    | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null

sudo apt-get update -q
sudo apt-get install -yq postgresql-18 python3.14 python3.14-venv caddy

# 1 GiB de memoria compartido con waitress: los valores por defecto de PostgreSQL
# suponen una máquina más grande. Para una demostración sobra.
sudo tee /etc/postgresql/18/main/conf.d/longbox.conf >/dev/null <<'EOF'
shared_buffers = 128MB
effective_cache_size = 384MB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 30
EOF
sudo systemctl restart postgresql

# Donde vive el sistema. Caddy lee `staticfiles/` y `media/`, así que la carpeta
# es legible por todos; el `.env` no (lo protege `instalar_en_vm.sh`).
sudo install -d -o "$USER" -g "$USER" -m 755 /srv/longbox

python3.14 --version
psql --version
caddy version
