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

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

- `ALLOWED_HOSTS` lo lee sólo la configuración de producción; desarrollo sigue igual.
- Los orígenes de confianza del CSRF se derivan solos: `.trycloudflare.com` pasa a
  `https://*.trycloudflare.com`.
- Con el correo de consola, los enlaces de activación y de recuperación aparecen en la ventana
  de `servir`.
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

Tres ventanas, desde la raíz del repositorio:

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

No se probó todavía: Caddy y `cloudflared` no están instalados en esta máquina.
