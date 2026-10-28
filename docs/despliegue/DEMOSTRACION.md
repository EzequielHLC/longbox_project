> **Tipo: Normativo.** Define cómo se levanta el sistema para una demostración accesible desde
> internet. El resultado de la última verificación es una fotografía y va al final, fechado.

# Demostración accesible desde internet

Hay tres rutas. La **ruta 3** corre el sistema en una VM de Azure, con dirección fija y sin
depender de esta máquina ni de la conexión de la casa: es la que se usa desde el 2026-10-23. Las
rutas 1 y 2 lo corren en esta máquina y quedan como alternativa; cuál de las dos sirve lo decide
la conexión (paso 0):

| | Túnel de Cloudflare | Nombre dinámico (NoIP) |
| --- | --- | --- |
| Sirve con CGNAT | **Sí** | No |
| Toca el router | No | Sí: reenvío de puertos 80 y 443 |
| Dirección | `algo-al-azar.trycloudflare.com`, **cambia en cada arranque** | Fija: `longbox.ddns.net` |
| Cuenta | No hace falta | NoIP gratuita, confirmar cada 30 días |
| Quién pone el HTTPS | Cloudflare | Caddy, con Let's Encrypt |

En las dos, Django corre con `manage.py servir` (waitress) en `127.0.0.1:8000` y **nunca se expone
directamente**. Delante va Caddy, que sirve `static/` y `media/` y le pasa el resto.

---

## 0. ¿La conexión admite tráfico entrante?

1. Abrir <https://api.ipify.org> y anotar la IP.
2. Entrar al router y mirar la IP de la WAN (o «IP de internet»).
3. **Si son distintas, hay CGNAT**: la IP pública se comparte con otros clientes y nada de lo que
   se configure en el router hace llegar tráfico a esta máquina. **Usar el túnel.** Si son
   iguales, sirven las dos rutas.

---

## Pasos comunes

### A. Programas

```powershell
winget install CaddyServer.Caddy
winget install --id Cloudflare.cloudflared   # sólo para la ruta del túnel
```

Abrir una terminal nueva después de instalar, para que tome los programas.

### B. `.env`

Sobre el `.env` que ya existe, agregar:

```ini
# Ruta del túnel: el punto adelante acepta cualquier subdominio, porque la
# dirección cambia en cada arranque.
ALLOWED_HOSTS=.trycloudflare.com

# Ruta NoIP, en su lugar:
# ALLOWED_HOSTS=longbox.ddns.net

# Correo real, con copia en la ventana de `servir`. Con Gmail: verificación en
# dos pasos y una contraseña de aplicación; el remitente es la misma cuenta.
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=la.cuenta@gmail.com
EMAIL_HOST_PASSWORD=la-contraseña-de-aplicación
DEFAULT_FROM_EMAIL=Longbox <la.cuenta@gmail.com>

# Ruta NoIP: los enlaces de los correos del Temporizador. Con el túnel la
# dirección cambia en cada arranque y conviene dejarla vacía.
# URL_PUBLICA=https://longbox.ddns.net
```

- `ALLOWED_HOSTS` lo lee sólo la configuración de producción; desarrollo sigue igual.
- Los orígenes de confianza del CSRF se derivan solos: `.trycloudflare.com` pasa a
  `https://*.trycloudflare.com`.
- Cada correo sale por SMTP y además queda copiado en la ventana de `servir`, con el enlace de
  activación o de recuperación a la vista. Sin `EMAIL_HOST`, el correo queda sólo en esa ventana
  y una línea lo avisa. Un servidor que rechaza el envío también queda anotado ahí.
- **Los pedidos a proveedores salen de verdad** al `correo_comercial` de cada ficha, al cerrar una
  sesión de revisión y al despachar una propuesta de restock. En la demostración conviene que esos
  correos sean propios.
- Sin `URL_PUBLICA`, los correos que manda el Temporizador salen sin enlace; los que salen de una
  pantalla lo llevan igual.
- `SECRET_KEY` tiene que ser propia de esta instalación (ver `.env.example`).

### C. Preparar

Desde la raíz del repositorio, con el entorno virtual activado, una vez y después de cada cambio
de código o de estáticos:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.production"
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

`check --deploy` tiene que terminar en «no issues». Si la base es nueva, crear el primer
Administrador con `python manage.py crear_administrador_inicial`.

---

## Ruta 1 · Túnel de Cloudflare

**Con doble clic en `demostracion.bat`**, en la raíz del repositorio, se hace todo lo de esta
ruta. Revisa que estén el entorno virtual, Caddy, `cloudflared`, el `.env` y los puertos 8000 y
8080 libres. Corre el paso C y abre las tres ventanas de abajo. Muestra la dirección pública y la
copia al portapapeles. Una tecla en su ventana cierra las tres; cerrarla con la cruz las deja
corriendo. Antes de levantar corre el Temporizador (`manage.py ejecutar_temporizador`), que deja
al día el estado de las ofertas.

**Si la máquina queda encendida varios días**, el Temporizador se programa una vez por día. En
PowerShell, desde la raíz del repositorio:

```powershell
$accion = New-ScheduledTaskAction -Execute "$PWD\venv\Scripts\python.exe" -Argument "manage.py ejecutar_temporizador" -WorkingDirectory "$PWD"
Register-ScheduledTask -TaskName "Longbox temporizador" -Action $accion -Trigger (New-ScheduledTaskTrigger -Daily -At 00:05)
```

Aunque no corra, las ofertas empiezan y terminan a tiempo: el precio con descuento se calcula con
las fechas. Lo que espera al Temporizador es el estado que muestra la lista y la entrada de
auditoría del vencimiento.

A mano son tres ventanas, desde la raíz del repositorio:

```powershell
# Ventana 1 — Django
$env:DJANGO_SETTINGS_MODULE = "config.settings.production"
python manage.py servir
```

```powershell
# Ventana 2 — Caddy, sólo local y en HTTP: el HTTPS lo pone el túnel
caddy run --config config/caddy/Caddyfile.tunel
```

```powershell
# Ventana 3 — el túnel
cloudflared tunnel --url http://127.0.0.1:8080
```

La ventana 3 imprime la dirección pública, del estilo `https://palabras-al-azar.trycloudflare.com`.
Es la que se comparte. **Cambia cada vez que se arranca el túnel**: conviene arrancarlo una sola
vez, antes de la demostración, y no cerrarlo.

Un túnel rápido de Cloudflare no tiene garantía de disponibilidad: es para pruebas y
demostraciones. Si hace falta una dirección fija, las dos alternativas son un túnel con nombre de
Cloudflare —exige un dominio propio administrado en Cloudflare— o el dominio estático gratuito de
ngrok. Las dos piden cuenta y cambian `ALLOWED_HOSTS`.

## Ruta 2 · Nombre dinámico (NoIP)

Sólo si el paso 0 dice que no hay CGNAT.

1. **NoIP.** Crear una cuenta en <https://www.noip.com> y un *hostname* gratuito de tipo **A**,
   por ejemplo `longbox.ddns.net`. Instalar el **Dynamic Update Client (DUC)**, iniciar sesión y
   marcar el nombre: mantiene la IP al día. El nombre gratuito se confirma cada 30 días desde el
   correo de NoIP.
2. **Router.** Reservar una IP local fija para esta máquina (reserva DHCP) y reenviar **TCP 80** y
   **TCP 443** a esa IP. El 80 hace falta aunque el sitio sea HTTPS: Let's Encrypt lo usa para
   validar el nombre.
3. **Firewall de Windows**, en PowerShell como administrador:

   ```powershell
   New-NetFirewallRule -DisplayName "Longbox HTTP"  -Direction Inbound -Protocol TCP -LocalPort 80  -Action Allow
   New-NetFirewallRule -DisplayName "Longbox HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
   ```

4. **Levantar**, en dos ventanas:

   ```powershell
   # Ventana 1 — Django
   $env:DJANGO_SETTINGS_MODULE = "config.settings.production"
   python manage.py servir
   ```

   ```powershell
   # Ventana 2 — Caddy, con HTTPS automático para el nombre
   $env:LONGBOX_HOST = "longbox.ddns.net"
   caddy run --config config/caddy/Caddyfile
   ```

## Ruta 3 · VM de Azure

Una B2ats_v2 (2 vCPU, 1 GiB) con Ubuntu 24.04 en Chile Central, de la oferta para estudiantes.
La dirección es fija: <https://longbox.chilecentral.cloudapp.azure.com>. Django corre como en las
otras rutas, con `servir` detrás de Caddy, pero como servicios de systemd que arrancan solos:
`longbox` (waitress), `caddy` (con el certificado de Let's Encrypt), `longbox-temporizador.timer`
(el Temporizador, todos los días a las 00:05), `longbox-reloj.timer` (cada minuto: la casilla de
novedades si le toca, el resumen de la mañana si es la hora y los controles de salud; B-19-011) y
`longbox-respaldo.timer` (el respaldo de la base, todos los días a las 03:30; B-19-013).

| | |
| --- | --- |
| Entrar | `ssh -i ~/.ssh/longbox_azure longbox@longbox.chilecentral.cloudapp.azure.com` |
| Dónde está | `/srv/longbox`, con su `.env` (600) y su entorno virtual |
| Registro del sistema | `sudo journalctl -u longbox -f` |
| SSH | Sólo desde el bloque del proveedor de la casa (`131.108.141.0/24`) y sólo con la clave |
| Costo | La oferta cubre 750 horas por mes de esta VM; un mes entero son 744. Azure no ofrece el apagado automático en Chile Central |

### Actualizar

Desde la raíz del repositorio, en Git Bash:

```bash
bash scripts/despliegue/subir_a_vm.sh               # el código, con los cambios sin commitear
bash scripts/despliegue/subir_a_vm.sh --con-base    # además, reemplaza la base y media/
```

Sube los archivos que versiona git más los nuevos sin ignorar —nunca el `.env`, `media/` ni el
entorno virtual— y corre `instalar_en_vm.sh`: dependencias, migraciones, `collectstatic`,
`check --deploy` y reinicio de los servicios. **`--con-base` pisa la base de la VM** con un respaldo
verificado de la del `.env` local, y de `media/` sube sólo lo que esa base referencia. Las
contraseñas del personal vuelven a ser las de la base local: hay que cambiarlas de nuevo (ver
abajo).

### Crearla desde cero

1. **La VM.** Con la Azure CLI y `az login`, en PowerShell: `scripts/despliegue/crear_vm_azure.ps1`.
   Crea el grupo `rg-longbox`, las reglas de red, la IP fija con el nombre y el disco P6 de 64 GiB,
   y deja configurados el intercambio de 2 GiB y la hora de Buenos Aires (`cloud-init.yaml`). La
   clave SSH va antes: `ssh-keygen -t ed25519 -f ~/.ssh/longbox_azure`.
2. **Los programas.** `ssh ... 'bash -s' < scripts/despliegue/preparar_vm.sh`: PostgreSQL 18
   ajustado a 1 GiB, Python 3.14 y Caddy.
3. **El `.env`.** A partir de `.env.example`, con una `SECRET_KEY` y una `DB_PASSWORD` propias,
   `ALLOWED_HOSTS` y `URL_PUBLICA` con el nombre de Azure, y el correo saliente. Se sube como
   `/tmp/longbox/env.vm` sólo la primera vez; después la VM conserva el suyo.
4. **El sistema.** `bash scripts/despliegue/subir_a_vm.sh --con-base`.
5. **Las contraseñas del personal.** La base de la presentación trae las de siempre, y en una
   dirección pública eso deja el panel abierto: se cambian con `manage.py shell` en la VM,
   pasando el código por la entrada estándar para que no queden en la línea de comandos.

Borrar todo: `az group delete --name rg-longbox`.

### El modelo de lenguaje: LM Studio de esta PC, por un túnel

LM Studio no entra en 1 GiB, pero la VM puede usar el de esta PC por un **túnel SSH inverso**:
la VM lo ve en su propio `127.0.0.1:1234`, y nada queda publicado en internet. Usa la misma clave y
el mismo acceso que la subida, así que anda desde la casa. No hace falta Cloudflare: un túnel
rápido publicaría el modelo en una dirección abierta, que además cambia en cada arranque.

1. En esta PC, LM Studio con el servidor arrancado (`Developer > Start Server`) y el modelo
   cargado.
2. El túnel, en una ventana que queda abierta:
   `powershell -ExecutionPolicy Bypass -File scripts\despliegue\tunel_lm_studio.ps1`. Si se corta,
   vuelve a conectar solo.
3. En Parámetros globales de la VM, *Modelo de lenguaje*: modo local, dirección
   `http://127.0.0.1:1234/v1/chat/completions` y el modelo (hoy `qwen/qwen3.5-9b`).

Sin túnel, aprobar un correo en la VM dice que el modelo no responde. Para volver a OpenRouter:
modo remoto, su dirección y su modelo; la clave sigue guardada.

### Lo que no hace la VM
- **Las fotos de devoluciones** (`privado/`) no se suben: la base de la presentación no tiene
  casos.

---

## El correo de prueba

Para probar en esta máquina lo que entra y sale por correo con los proveedores —la casilla de
novedades (`CO-016`), los pedidos del cierre de una sesión de revisión y los de Restock— sin
cuentas reales. Un servidor de prueba (smtp4dev, en Docker) recibe **todo** lo que el sistema
manda y hace de casilla. Nada sale a internet: un pedido a un proveedor o una activación de
cliente se quedan en la bandeja de prueba.

1. **Levantarlo**, con Docker Desktop abierto:

   ```bash
   docker compose -f config/correo-de-prueba/compose.yaml up -d
   ```

   La bandeja queda en <http://127.0.0.1:5000>. Arranca sola con Docker Desktop.

2. **El `.env`**: el bloque «Correo de prueba» de `.env.example` (SMTP en `127.0.0.1:2525`,
   casilla IMAP en `127.0.0.1:1143` sin SSL). La casilla sin SSL sólo se admite si es local: con
   cualquier otra, `casilla.abrir` la rechaza antes de conectar.

3. **Mandar una novedad** como si fuera la editorial. El remitente tiene que ser el correo
   comercial de un proveedor habilitado:

   ```bash
   python scripts/demo/enviar_novedades.py --cantidad 1 --smtp 127.0.0.1:2525 \
       --para casilla@longbox.demo --remitente proveedor@ejemplo.com
   ```

   **O escribirlo a mano**, con `python scripts/demo/redactar_correo.py` y la página
   <http://127.0.0.1:8770>: remitente, asunto, texto y tabla de productos con portadas, desde una
   plantilla de novedades, de demora o libre (una factura). «Mandar a la casilla» lo deja en el
   correo de prueba; «Bajar .eml» lo guarda para `manage.py ingerir_correos`.

4. **Que la lea el sistema**: el botón **«Revisar la casilla»** de *Proveedores → Correos
   recibidos*, o `python manage.py revisar_casilla`, la leen en el momento, sin mirar la
   frecuencia de Parámetros. Con el bot escuchando (`telegram escuchar`) se lee sola cada vez
   que pasa esa frecuencia, en minutos; en la VM, `longbox-reloj.timer` hace lo mismo. El correo queda Pendiente en la cola y el
   Administrador recibe el aviso, en la misma bandeja. Aprobarlo necesita el modelo de lenguaje.

5. **Ver lo que salió**: los pedidos a cada proveedor —al cerrar una sesión de revisión o al
   despachar una propuesta de Restock— aparecen en la bandeja con su destinatario.

Para volver al correo real, el `.env` vuelve al bloque de Gmail. La VM no usa el correo de
prueba: sigue con el correo real.

---

## El bot de Telegram

El bot (módulo 19) avisa al Administrador y le deja aprobar o descartar los correos de
proveedores desde el teléfono, consultar stock, llegadas, pendientes y caja, y cargar borradores
con una foto. Sin `TELEGRAM_BOT_TOKEN` en el `.env` no existe y todo sale por
correo.

1. **El token**, en el `.env` de esta PC y en el de la VM: `TELEGRAM_BOT_TOKEN=…` (lo da
   @BotFather con `/newbot`). Es la llave del bot: no se comparte ni se versiona.
2. **Que el bot escuche**:
   - En esta PC, mientras se prueba: `python manage.py telegram escuchar` (Ctrl+C para salir).
     También vigila la casilla: un correo nuevo llega al chat en los minutos de Parámetros.
   - En la VM, una vez después de subir el sistema: `python manage.py telegram webhook`, con
     `URL_PUBLICA` en `https://…`. Telegram entrega en `/telegram/webhook/` con su secreto.
   - Las dos cosas no van a la vez: `escuchar` saca el webhook. Después de probar en la PC, volver
     a correr `webhook` en la VM.
3. **Vincular**: en el sistema, **Mi perfil** (arriba del menú) → «Vincular Telegram», y abrir el
   enlace desde el teléfono (vence a los 15 minutos). El bot contesta con un número de seis
   cifras, que se escribe en el perfil para terminar (B-19-005). Después, en «Mis avisos», marcar
   qué llega por Telegram.
4. **Probarlo**: mandar un correo con la página de redacción; llega solo al chat con «Aprobar y
   procesar» y «Descartar». En el chat, `/ayuda` lista los comandos: `/stock Berserk 5`,
   `/llega`, `/pendientes`, `/caja`, y `/cargar` con un texto o una foto de la tapa con el texto
   como epígrafe (necesita el modelo de lenguaje). Una pregunta con palabras también sirve.

5. **Compartir productos desde cualquier chat** (modo inline), una sola vez: en Telegram, a
   **@BotFather**, `/setinline`, elegir el bot y escribir el texto de ayuda («Buscar un producto…»).
   Después, en cualquier chat: `@longbox_comiqueria_bot berserk`.

`python manage.py telegram estado` dice el nombre del bot y si el token sirve. En la VM, `/estado`
en el chat dice cómo anda: disco, memoria, base y el último respaldo.

---

## Verificar desde afuera

Desde un **teléfono con datos móviles**, no desde el wifi de la casa.

1. La dirección abre con candado y sin advertencias.
2. La pantalla de inicio de sesión carga con sus estilos (prueba que `static/` se sirve).
3. Iniciar sesión funciona (prueba el CSRF detrás del proxy).
4. La ficha de un producto con portada muestra la imagen (prueba que `media/` se sirve).

| Síntoma | Causa probable |
| --- | --- |
| «Bad Request (400)» | La dirección no está cubierta por `ALLOWED_HOSTS` |
| «Forbidden (403) CSRF» al iniciar sesión | El origen de la barra del navegador no está en `CSRF_TRUSTED_ORIGINS` |
| La página redirige en círculo | Caddy no está confiando en el túnel: se usó `Caddyfile` en vez de `Caddyfile.tunel` |
| Pantallas sin estilos | Falta `collectstatic`, o Caddy no se arrancó desde la raíz del repositorio |
| El túnel muestra un error 502 | Caddy o `servir` no están corriendo |
| Error 500 | El detalle aparece en la ventana de `servir` |
| Ruta NoIP: no responde nada | Reenvío de puertos, firewall, o CGNAT (paso 0) |
| Ruta NoIP: Caddy no obtiene el certificado | El puerto 80 no llega desde afuera |

Si la demostración usa el procesamiento de correos, el servicio del modelo de lenguaje
configurado en Parámetros globales tiene que estar corriendo. Con la modalidad local, eso es LM
Studio en esta misma máquina.

## La base de la presentación

Para mostrar el sistema con datos reales y sin restos de pruebas manuales:

```bash
python scripts/demo/presentacion.py --confirmar
```

No borra la base actual. Respalda la base y `media/` en `respaldos/presentacion-<fecha>/`,
crea `longbox_presentacion` y cambia **sólo** `DB_NAME` en el `.env` (anota la anterior en
`DB_NAME_ANTERIOR`). La base nueva queda con:

- tres cuentas, con las contraseñas de siempre: `admin@correo.com`, `cajero@correo.com` y
  `cliente@correo.com`;
- el catálogo de Ivrea limpio: 487 series y unos 3600 tomos con sinopsis y la portada de cada
  tomo (el tomo 0 cuando la serie lo tiene), sin las páginas que agrupan franquicias ni el código
  del sitio que venía pegado a la sinopsis;
- el proveedor Ivrea con una casilla `.demo` y tres correos de novedades pendientes;
- tres ofertas, tres banners armados con portadas y cinco filas en la portada, una con imagen;
- la identidad visual y los parámetros de la base anterior, y unas preguntas frecuentes reales.

Requiere `scripts/demo/datos/`: lo arman `raspar_ivrea.py` (series) y `raspar_portadas_tomos.py`
(portada de cada tomo, desde la galería PORTADAS de cada serie). `--reemplazar` la rehace desde la
base anterior. Para volver: `DB_NAME=longbox_db` en el `.env` y `media/` desde el respaldo.

## Después

- Cerrar las ventanas: al cerrar el túnel, la dirección deja de existir.
- Respaldar la base si durante la demostración se cargaron datos: [RESPALDOS.md](RESPALDOS.md).
- Ruta NoIP: si la máquina no va a seguir publicada, quitar el reenvío de puertos.

---

## Última verificación

> **Fotografía del 2026-10-28, más tarde, ruta 3: limpieza y modelo local.**

- **La base de la VM se limpió**, con un respaldo previo en
  `/srv/longbox/respaldos/antes-de-limpiar/`. Se borraron los 15 pedidos de prueba con lo que
  colgaba de ellos (pagos, cobros, puntos, 4 devoluciones, stock en local, 3 cierres de caja) y las
  cuentas de cliente de prueba; lo vendido volvió al stock de 19 productos. Las 59 pre-ventas
  salieron: el pedido a proveedor abierto se cerró sin recibir, por el servicio, y el resto pasó a
  Agotado sin fecha. Quedan `admin@`, `cajero@` y `cliente@correo.com`. El registro de auditoría no
  se tocó: es inmutable.
- **El modelo de lenguaje de la VM es LM Studio de esta PC**, por el túnel SSH: se cambió por la
  pantalla de Parámetros (auditado) y un pedido de prueba contestó en 0,6 s.

> **Fotografía del 2026-10-28, ruta 3: el bot de Telegram en la VM.**

Se subió sólo el código (`subir_a_vm.sh`, sin `--con-base`): aplicaron `avisos.0001` a `0003`,
`catalog.0026` y `0027` y `core.0046` a `0048`, y `check --deploy` quedó sin advertencias. Quedaron
activos `longbox-reloj.timer`, que corre cada minuto, y `longbox-respaldo.timer`. El primer respaldo
se corrió a mano y salió verificado (842 KB, en `/srv/longbox/respaldos`). El instalador agregó
`VIGILAR_RESPALDO=True` al `.env`, y el token del bot se copió desde el `.env` local sin mostrarlo.
`telegram webhook` dejó el webhook en `/telegram/webhook/`. Telegram lo informa sin errores ni
novedades pendientes, con mensajes, botones y búsquedas en línea. Un pedido sin el secreto, desde
afuera, recibe 403.

**La casilla de novedades de la VM es `longbox.news@gmail.com`** (IMAP con SSL y contraseña de
aplicación, en el `.env` de la VM), distinta de la cuenta que manda los correos. La conexión se probó
sin marcar nada, y el reloj la leyó a las 05:00: descartó los 8 avisos de Google con que se crea una
cuenta, porque no vienen de un proveedor. En el `.env` de esta PC esas líneas quedan comentadas
(`# [vm]`): si las dos instalaciones leyeran la misma casilla, cada una se quedaría con una parte de
los correos. **Para recibir uno de verdad**, el correo comercial de un proveedor de la VM tiene que
ser una dirección desde la que se pueda escribir. **La base de la VM es otra**, así que el chat se vincula de nuevo
desde «Mi perfil» en la VM. **Mientras el webhook esté puesto, `telegram escuchar` en esta PC no
recibe nada**; al correrlo saca el webhook, y después hay que volver a poner el de la VM.

> **Fotografía del 2026-10-23, ruta 3.**

La VM se creó con `crear_vm_azure.ps1`, se preparó con `preparar_vm.sh` (Python 3.14.9,
PostgreSQL 18.6, Caddy 2.11.7) y se instaló con la base `longbox_presentacion` y los 3591
archivos de `media/` que referencia. Desde esta máquina, por la dirección pública:

- El certificado de Let's Encrypt lo obtuvo Caddy solo y la conexión verifica sin advertencias.
- La pantalla de inicio de sesión carga sus estilos; el inicio de sesión del Administrador pasa
  el CSRF y llega al panel; una portada de `media/` responde 200.
- La portada de la tienda se revisó con una captura de Chrome sin interfaz, en escritorio. En
  390 px no se puede: la página no se deja cargar dentro de un iframe (`X-Frame-Options`), que es
  lo que corresponde en producción.
- `check --deploy` sin advertencias en la VM; la actualización sólo de código con `subir_a_vm.sh`
  conserva el `.env` y no deja nada en `/tmp/longbox`.

Con la VM en marcha quedan 518 MiB de memoria disponibles y el intercambio sin usar.

No se probó: el correo saliente desde la VM, el Temporizador corriendo a su hora (está
programado, todavía no le tocó) ni la carga de varios usuarios a la vez.

> **Fotografía del 2026-09-30, rutas 1 y 2.**

En esta máquina hay CGNAT: la IP de la WAN y la pública son distintas. Se verificó, sin el tramo
externo (el túnel, Caddy, NoIP):

- `check --deploy` con `ALLOWED_HOSTS=.trycloudflare.com`: sin advertencias. Los orígenes de
  confianza del CSRF se derivan a `https://*.trycloudflare.com`.
- `servir` con la configuración de producción, consultado como lo consulta Caddy detrás del
  túnel: la pantalla de inicio de sesión responde 200 con un subdominio cualquiera de
  `trycloudflare.com`, el inicio de sesión pasa el CSRF desde ese origen, el mismo envío desde un
  origen ajeno se rechaza con 403, y un nombre fuera de `ALLOWED_HOSTS` responde 400.
- Ruta NoIP con `ALLOWED_HOSTS` de prueba: 200 con `X-Forwarded-Proto: https`, redirección a
  HTTPS sin él.

No se probó todavía el tramo externo. El 2026-10-02 quedaron instalados Caddy 2.11.4 y
`cloudflared` 2026.9.3; `caddy validate` acepta `Caddyfile.tunel`, y de `demostracion.bat` se
probaron la extracción de la dirección pública sobre un registro de ejemplo y el `check --deploy`,
no el arranque completo.
