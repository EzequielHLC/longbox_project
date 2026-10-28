#!/usr/bin/env bash
# Sube el sistema a la VM de Azure y lo instala (docs/despliegue/DEMOSTRACION.md, ruta VM).
#
# Desde la raíz del repositorio, en Git Bash:
#
#   bash scripts/despliegue/subir_a_vm.sh               # sólo el código
#   bash scripts/despliegue/subir_a_vm.sh --con-base    # además, reemplaza la base y media/
#
# El código son los archivos versionados más los cambios sin commitear, sin nada
# de lo que ignora git: ni el `.env`, ni `media/`, ni el entorno virtual. Con
# `--con-base` sube un respaldo verificado de la base del `.env` local y, de
# `media/`, sólo lo que esa base referencia: no los restos de las pruebas.
set -euo pipefail

VM=${VM:-longbox@longbox.chilecentral.cloudapp.azure.com}
CLAVE=${CLAVE:-$HOME/.ssh/longbox_azure}
PYTHON=${PYTHON:-venv/Scripts/python}
RAIZ=$(cd "$(dirname "$0")/../.." && pwd)
TEMP=$(mktemp -d)
trap 'rm -rf "$TEMP"' EXIT
cd "$RAIZ"

echo "1. Código"
git -c core.quotepath=off ls-files -z -co --exclude-standard > "$TEMP/archivos.lst"
tar --force-local --null -czf "$TEMP/codigo.tar.gz" -T "$TEMP/archivos.lst"
archivos=("$TEMP/codigo.tar.gz")

if [ "${1:-}" = "--con-base" ]; then
    echo "2. Base y media/"
    PYTHONIOENCODING=utf-8 "$PYTHON" manage.py respaldar_base --destino "$TEMP" --conservar 0
    LISTA="$TEMP/media.lst" PYTHONIOENCODING=utf-8 "$PYTHON" manage.py shell -c "
import os
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.db import models
raiz = Path(settings.MEDIA_ROOT)
nombres = set()
for modelo in apps.get_models():
    for campo in [c.name for c in modelo._meta.get_fields() if isinstance(c, models.FileField)]:
        for nombre in modelo.objects.exclude(**{campo: ''}).values_list(campo, flat=True):
            if nombre and (raiz / nombre).is_file():
                nombres.add(Path(nombre).as_posix())
Path(os.environ['LISTA']).write_bytes(b'\0'.join(n.encode() for n in sorted(nombres)))
print(len(nombres), 'archivos de media/')
"
    tar --force-local --null -czf "$TEMP/media.tar.gz" -C media -T "$TEMP/media.lst"
    archivos+=("$TEMP"/*.dump "$TEMP/media.tar.gz")
fi

echo "3. Subida"
ssh -i "$CLAVE" "$VM" 'rm -rf /tmp/longbox && mkdir -m 700 /tmp/longbox'
scp -q -i "$CLAVE" "${archivos[@]}" "$VM:/tmp/longbox/"

echo "4. Instalación"
ssh -i "$CLAVE" "$VM" 'bash -s' < scripts/despliegue/instalar_en_vm.sh
ssh -i "$CLAVE" "$VM" 'rm -rf /tmp/longbox'
