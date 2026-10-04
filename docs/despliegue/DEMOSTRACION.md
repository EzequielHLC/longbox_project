> **Tipo: Normativo.** Define cómo se levanta el sistema para una demostración accesible desde
> internet. El resultado de la última verificación es una fotografía y va al final, fechado.

# Demostración accesible desde internet

El sistema corre en esta máquina y se accede desde afuera por una dirección HTTPS. Hay dos rutas,
y cuál sirve lo decide la conexión (paso 0):

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
```

- `ALLOWED_HOSTS` lo lee sólo la configuración de producción; desarrollo sigue igual.
- Los orígenes de confianza del CSRF se derivan solos: `.trycloudflare.com` pasa a
  `https://*.trycloudflare.com`.
- Cada correo sale por SMTP y además queda copiado en la ventana de `servir`, con el enlace de
  activación o de recuperación a la vista. Sin `EMAIL_HOST`, el correo queda sólo en esa ventana
  y una línea lo avisa. Un servidor que rechaza el envío también queda anotado ahí.
- **Los pedidos a proveedores salen de verdad** al `correo_comercial` de cada ficha. Antes de
  cerrar una sesión de revisión en la demostración, conviene que esos correos sean propios.
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
- el catálogo de Ivrea limpio: 487 series y 3594 tomos con portada y sinopsis, sin las páginas que
  agrupan franquicias ni el código del sitio que venía pegado a la sinopsis;
- el proveedor Ivrea con una casilla `.demo` y tres correos de novedades pendientes;
- tres ofertas, tres banners armados con portadas y cinco filas en la portada;
- la identidad visual y los parámetros de la base anterior, y unas preguntas frecuentes reales.

Requiere `scripts/demo/datos/` (lo arma `raspar_ivrea.py`). `--reemplazar` la rehace desde la
base anterior. Para volver: `DB_NAME=longbox_db` en el `.env` y `media/` desde el respaldo.

## Después

- Cerrar las ventanas: al cerrar el túnel, la dirección deja de existir.
- Respaldar la base si durante la demostración se cargaron datos: [RESPALDOS.md](RESPALDOS.md).
- Ruta NoIP: si la máquina no va a seguir publicada, quitar el reenvío de puertos.

---

## Última verificación

> **Fotografía del 2026-09-30.**

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
