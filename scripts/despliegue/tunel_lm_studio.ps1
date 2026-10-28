# El túnel que deja a la VM usar el LM Studio de esta PC (docs/despliegue/DEMOSTRACION.md).
#
#   powershell -ExecutionPolicy Bypass -File scripts\despliegue\tunel_lm_studio.ps1
#
# Es un túnel SSH inverso: la VM ve este LM Studio en su propio 127.0.0.1:1234, y
# nada queda publicado en internet (el puerto escucha sólo dentro de la VM). Usa
# la misma clave y el mismo acceso que `subir_a_vm.sh`, así que anda desde la casa.
# En Parámetros globales de la VM, el modelo va en modo local con
# http://127.0.0.1:1234/v1/chat/completions.
#
# Si se corta (la PC se suspende, se cae el wifi), vuelve a conectar solo. Ctrl+C
# para cerrarlo; sin túnel, aprobar un correo en la VM dice que el modelo no responde.

param(
    [string]$Vm = "longbox@longbox.chilecentral.cloudapp.azure.com",
    [string]$Clave = "$HOME\.ssh\longbox_azure",
    [int]$Puerto = 1234
)

try {
    Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 "http://127.0.0.1:$Puerto/v1/models" | Out-Null
} catch {
    Write-Warning "LM Studio no responde en 127.0.0.1:$Puerto. Abrilo y arrancá el servidor (Developer > Start Server)."
}

while ($true) {
    Write-Host "$(Get-Date -Format 'HH:mm:ss')  Túnel a la VM abierto: la VM usa este LM Studio. Ctrl+C para cerrar."
    ssh -i $Clave -N `
        -o ExitOnForwardFailure=yes `
        -o ServerAliveInterval=30 `
        -o ServerAliveCountMax=3 `
        -R "127.0.0.1:${Puerto}:127.0.0.1:${Puerto}" `
        $Vm
    Write-Host "$(Get-Date -Format 'HH:mm:ss')  El túnel se cortó; reintento en 10 segundos."
    Start-Sleep -Seconds 10
}
