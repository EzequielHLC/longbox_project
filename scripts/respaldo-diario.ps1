<#
.SYNOPSIS
    Respaldo diario de la base. Lo invoca el Programador de tareas de Windows.

.DESCRIPTION
    Envuelve a `manage.py respaldar_base`. El envoltorio existe porque una tarea
    programada corre sin consola, sin el entorno virtual activado y sin nadie
    que lea un error en pantalla, así que hace tres cosas que el comando de
    Django no puede hacer por sí solo:

      - usa el Python del entorno virtual por ruta absoluta, sin depender de que
        el PATH de la tarea se parezca al de una consola interactiva;
      - deja todo en un archivo de registro, que es el único lugar donde alguien
        se va a enterar de que algo falló;
      - devuelve un código de salida distinto de cero cuando falla, que es lo
        que hace que el Programador marque la tarea en rojo. Sin eso, una tarea
        que nunca respaldó nada figura como "completada correctamente" durante
        meses.

    Para darlo de alta, desde una consola con permisos de administrador:

        schtasks /Create `
          /TN "Longbox - respaldo diario" `
          /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\Ezequiel\Desktop\Longbox\scripts\respaldo-diario.ps1" `
          /SC DAILY /ST 03:00 /RL HIGHEST

    Y para probarla sin esperar a las tres de la mañana:

        schtasks /Run /TN "Longbox - respaldo diario"

.PARAMETER Conservar
    Cuántos respaldos dejar en la carpeta. Con uno diario, 7 es una semana.

.PARAMETER Verificar
    No respalda: relee los respaldos guardados y falla si alguno no se puede
    abrir. Conviene programarlo aparte, una vez por semana — un respaldo que se
    corrompió en disco después de escribirse no lo detecta nadie más.
#>
[CmdletBinding()]
param(
    [int]$Conservar = 7,
    [switch]$Verificar
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$python = Join-Path $raiz "venv\Scripts\python.exe"
$registro = Join-Path $raiz "respaldos\respaldo.log"

function Anotar($texto) {
    $linea = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $texto
    Add-Content -Path $registro -Value $linea -Encoding utf8
    Write-Output $linea
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $registro) | Out-Null

if (-not (Test-Path $python)) {
    Anotar "ERROR  No se encontro el entorno virtual en $python"
    exit 1
}

$argumentos = @("manage.py", "respaldar_base", "--conservar", $Conservar)
if ($Verificar) { $argumentos = @("manage.py", "respaldar_base", "--verificar-solo") }

# stderr va a un archivo aparte, y `$ErrorActionPreference` baja a `Continue`
# solo mientras dura la llamada. Windows PowerShell 5.1 envuelve cada línea de
# error de un ejecutable en un ErrorRecord en cuanto se redirige stderr, y con
# `Stop` eso aborta el script en la primera línea: quedaría el código de salida
# correcto y el registro vacío, que es justo lo que este archivo existe para que
# no pase. El código de salida se sigue leyendo de `$LASTEXITCODE`, que es lo
# único que dice de verdad si el comando anduvo.
$errores = New-TemporaryFile
$preferenciaPrevia = $ErrorActionPreference

try {
    Push-Location $raiz
    $ErrorActionPreference = "Continue"
    $salida = & $python @argumentos 2> $errores
    $codigo = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $preferenciaPrevia
    Pop-Location
}

# PowerShell adorna cada error de un ejecutable con el fragmento de código, un
# subrayado y dos líneas de categoría. En una consola sirve; en un registro que
# alguien va a leer meses después, esconde el único renglón que importa.
$decoracion = '^\s*(\+|En .+: \d+ Car)|CategoryInfo|FullyQualifiedErrorId'

function AnotarSalida($lineas) {
    foreach ($linea in $lineas) {
        $texto = "$linea".TrimEnd()
        if ($texto -and $texto -notmatch $decoracion) { Anotar $texto }
    }
}

AnotarSalida $salida
AnotarSalida (Get-Content $errores -ErrorAction SilentlyContinue)
Remove-Item $errores -Force -ErrorAction SilentlyContinue

if ($codigo -ne 0) {
    Anotar "ERROR  El respaldo fallo con codigo $codigo"
    exit $codigo
}

Anotar "Listo"
exit 0
