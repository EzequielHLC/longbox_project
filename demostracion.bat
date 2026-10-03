@echo off
chcp 65001 >nul
setlocal
rem ---------------------------------------------------------------------------
rem  Longbox - demostracion por el tunel de Cloudflare.
rem
rem  Lo mismo que la Ruta 1 de docs\despliegue\DEMOSTRACION.md, en un doble
rem  clic: prepara la base y los estaticos, y abre tres ventanas (Django con
rem  waitress, Caddy y el tunel). Al final muestra la direccion publica y la
rem  copia al portapapeles. Una tecla en esta ventana cierra las tres.
rem ---------------------------------------------------------------------------

cd /d "%~dp0"
title Demostración Longbox
set "PYTHON=venv\Scripts\python.exe"
set "DJANGO_SETTINGS_MODULE=config.settings.production"
set "REGISTRO_TUNEL=%TEMP%\longbox-tunel.log"

echo.
echo  ◆ LONGBOX · demostración
echo  ─────────────────────────────────────────────
echo.

rem --- Lo que tiene que estar instalado ------------------------------------
if not exist "%PYTHON%" (
    echo  Falta el entorno virtual: no está %PYTHON%.
    goto :fallo
)
where caddy >nul 2>&1 || (
    echo  Falta Caddy. Instalarlo con:  winget install CaddyServer.Caddy
    goto :fallo
)
where cloudflared >nul 2>&1 || (
    echo  Falta cloudflared. Instalarlo con:  winget install --id Cloudflare.cloudflared
    goto :fallo
)
if not exist ".env" (
    echo  Falta el archivo .env. Ver .env.example y DEMOSTRACION.md, paso B.
    goto :fallo
)

rem --- Que no haya otra demostracion corriendo ------------------------------
netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul && (
    echo  El puerto 8000 ya está en uso: ¿quedó abierta otra demostración o un runserver?
    goto :fallo
)
netstat -ano | findstr /r /c:":8080 .*LISTENING" >nul && (
    echo  El puerto 8080 ya está en uso: ¿quedó abierto otro Caddy?
    goto :fallo
)

rem --- Preparar: paso C de DEMOSTRACION.md ----------------------------------
echo  [1/4] Aplicando migraciones...
"%PYTHON%" manage.py migrate --noinput || goto :fallo
echo  [2/4] Juntando los estáticos...
"%PYTHON%" manage.py collectstatic --noinput --verbosity 0 || goto :fallo
echo  [3/4] Revisando la configuración de despliegue...
"%PYTHON%" manage.py check --deploy --fail-level WARNING || goto :fallo

rem --- Levantar: cada pieza en su ventana, para ver sus mensajes -------------
echo  [4/4] Levantando Django, Caddy y el túnel...
if exist "%REGISTRO_TUNEL%" del "%REGISTRO_TUNEL%"
start "Longbox Django" cmd /k %PYTHON% manage.py servir
start "Longbox Caddy" cmd /k caddy run --config config\caddy\Caddyfile.tunel
start "Longbox Tunel" cmd /k cloudflared tunnel --url http://127.0.0.1:8080 --logfile "%REGISTRO_TUNEL%"

rem --- La direccion publica: el tunel la anuncia en su registro --------------
echo.
echo  Esperando la dirección pública del túnel...
set "DIRECCION="
for /l %%i in (1,1,45) do (
    if not defined DIRECCION (
        timeout /t 1 /nobreak >nul
        for /f "usebackq delims=" %%u in (`powershell -NoProfile -Command "if (Test-Path $env:REGISTRO_TUNEL) { (Select-String -Path $env:REGISTRO_TUNEL -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -List).Matches.Value }"`) do set "DIRECCION=%%u"
    )
)

echo.
if defined DIRECCION (
    echo  ─────────────────────────────────────────────
    echo   Dirección pública:  %DIRECCION%
    echo  ─────────────────────────────────────────────
    echo   Copiada al portapapeles. Cambia cada vez que se arranca el túnel.
    <nul set /p "=%DIRECCION%" | clip
) else (
    echo  El túnel no anunció su dirección en 45 segundos. Mirá la ventana "Longbox Tunel".
)
echo.
echo  Si se van a procesar correos de proveedores, LM Studio tiene que estar corriendo.
echo  Los mensajes, los errores y la copia de cada correo enviado aparecen en "Longbox Django".
echo.
echo  Presioná una tecla para CERRAR la demostración (Django, Caddy y el túnel).
pause >nul

:cerrar
echo  Cerrando...
taskkill /fi "WINDOWTITLE eq Longbox Django*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Longbox Caddy*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Longbox Tunel*" /t /f >nul 2>&1
echo  Listo. La dirección pública dejó de existir.
timeout /t 3 >nul
exit /b 0

:fallo
echo.
echo  No se levantó nada. Corregí lo de arriba y volvé a ejecutar.
pause >nul
exit /b 1
