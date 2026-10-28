#!/usr/bin/env bash
# Instala o actualiza el sistema en la VM (docs/despliegue/DEMOSTRACION.md, ruta VM).
#
# Espera en /tmp/longbox lo que sube la máquina de desarrollo:
#   codigo.tar.gz   los archivos versionados y los cambios sin commitear
#   env.vm          (sólo la primera vez) el .env de la VM
#   *.dump          (opcional) el respaldo que reemplaza la base
#   media.tar.gz    (opcional) los archivos que esa base referencia
#
# Lo sube `subir_a_vm.sh`. Sin respaldo, actualiza el código y conserva la base y
# `media/`; sin `env.vm`, conserva el `.env` que ya tiene la VM.
set -euo pipefail

ORIGEN=/tmp/longbox
DESTINO=/srv/longbox
cd "$DESTINO"

echo "1. Código"
tar -xzf "$ORIGEN/codigo.tar.gz" -C "$DESTINO"
if [ -f "$ORIGEN/env.vm" ]; then
    install -m 600 "$ORIGEN/env.vm" "$DESTINO/.env"
fi
[ -f "$DESTINO/.env" ] || { echo "Falta el .env: subir env.vm la primera vez." >&2; exit 1; }

echo "2. Entorno virtual"
[ -d venv ] || python3.14 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

DB_NAME=$(grep '^DB_NAME=' .env | cut -d= -f2)
DB_USER=$(grep '^DB_USER=' .env | cut -d= -f2)
DB_PASSWORD=$(grep '^DB_PASSWORD=' .env | cut -d= -f2)

echo "3. Base"
sudo -u postgres psql -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASSWORD';
  ELSE
    ALTER ROLE $DB_USER PASSWORD '$DB_PASSWORD';
  END IF;
END \$\$;
SQL
RESPALDO=$(ls "$ORIGEN"/*.dump 2>/dev/null | head -1 || true)
if [ -n "$RESPALDO" ]; then
    echo "   se reemplaza con $(basename "$RESPALDO")"
    sudo systemctl stop longbox 2>/dev/null || true
    sudo -u postgres dropdb --if-exists "$DB_NAME"
    sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
    # Como el dueño de la base y no como superusuario: así los disparadores y
    # las tablas quedan de `longbox_user`, igual que en desarrollo.
    PGPASSWORD="$DB_PASSWORD" pg_restore --no-owner --no-privileges -h 127.0.0.1 \
        -U "$DB_USER" -d "$DB_NAME" "$RESPALDO"
    if [ -f "$ORIGEN/media.tar.gz" ]; then
        rm -rf media && mkdir media
        tar -xzf "$ORIGEN/media.tar.gz" -C media
    fi
fi
mkdir -p media privado

echo "4. Migraciones, estáticos y control de despliegue"
export DJANGO_SETTINGS_MODULE=config.settings.production
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput -v 0
venv/bin/python manage.py check --deploy --fail-level WARNING

echo "5. Servicios"
sudo install -m 644 config/systemd/longbox.service /etc/systemd/system/
sudo install -m 644 config/systemd/longbox-temporizador.service /etc/systemd/system/
sudo install -m 644 config/systemd/longbox-temporizador.timer /etc/systemd/system/
# El reloj por minuto reemplaza a la vigilancia de la casilla (B-19-011).
if [ -f /etc/systemd/system/longbox-casilla.timer ]; then
    sudo systemctl disable --now longbox-casilla.timer 2>/dev/null || true
    sudo rm -f /etc/systemd/system/longbox-casilla.service /etc/systemd/system/longbox-casilla.timer
fi
for unidad in longbox-reloj longbox-respaldo; do
    sudo install -m 644 "config/systemd/$unidad.service" /etc/systemd/system/
    sudo install -m 644 "config/systemd/$unidad.timer" /etc/systemd/system/
done
# Con el respaldo diario programado, el bot avisa si falta (B-19-013).
grep -q '^VIGILAR_RESPALDO=' .env || echo 'VIGILAR_RESPALDO=True' >> .env
mkdir -p respaldos
sudo install -d /etc/systemd/system/caddy.service.d
sudo install -m 644 config/systemd/caddy-longbox.conf /etc/systemd/system/caddy.service.d/longbox.conf
sudo systemctl daemon-reload
sudo systemctl enable --now longbox longbox-temporizador.timer longbox-reloj.timer longbox-respaldo.timer
sudo systemctl restart longbox caddy

echo "Listo."
