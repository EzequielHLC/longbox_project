<#
Crea la VM de Azure para la demostración: Ubuntu 24.04 en una B2ats_v2 de Chile Central.

Requiere la Azure CLI con la sesión iniciada (`az login`) y la clave SSH propia de
la VM (`~/.ssh/longbox_azure`). Crea, en un grupo de recursos propio:

- Un grupo de seguridad de red: SSH sólo desde la IP de quien corre el script; 80
  y 443 abiertos, para Caddy y el certificado de Let's Encrypt.
- La VM con su IP pública fija y el nombre `<Dns>.chilecentral.cloudapp.azure.com`.
- Un disco Premium SSD de 64 GiB (P6), el que cubre la oferta de estudiante.

No programa el apagado automático: Azure no lo ofrece en Chile Central, y tampoco
hace falta, porque la oferta cubre 750 horas por mes de esta VM y un mes entero
son 744.

Borrar todo lo creado: `az group delete --name rg-longbox`.
#>

param(
    [string]$Grupo = "rg-longbox",
    [string]$Region = "chilecentral",
    [string]$Vm = "longbox-vm",
    [string]$Dns = "longbox",
    [string]$Usuario = "longbox",
    [string]$ClavePublica = "$env:USERPROFILE\.ssh\longbox_azure.pub"
)

$ErrorActionPreference = "Stop"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path

function Correr {
    # Un comando nativo que falla no detiene PowerShell: se mira el código de salida.
    & $az @args --only-show-errors
    if ($LASTEXITCODE -ne 0) { throw "Falló: az $($args -join ' ')" }
}

if (-not (Test-Path $ClavePublica)) { throw "Falta la clave pública: $ClavePublica" }
$miIp = (Invoke-RestMethod https://api.ipify.org).Trim()
# El bloque /24 y no la IP sola: un proveedor con CGNAT saca la conexión por más de
# una dirección (pasó el 2026-10-23: .181 y .182), y con una sola SSH entra a veces.
$bloque = ($miIp -replace '\.\d+$', '.0') + "/24"
Write-Host "SSH quedará abierto sólo para $bloque"

Write-Host "1. Grupo de recursos"
Correr group create --name $Grupo --location $Region --output none

Write-Host "2. Reglas de red"
Correr network nsg create --resource-group $Grupo --name "nsg-$Vm" --output none
Correr network nsg rule create --resource-group $Grupo --nsg-name "nsg-$Vm" --name ssh-propio `
    --priority 100 --protocol Tcp --destination-port-ranges 22 --source-address-prefixes $bloque `
    --access Allow --direction Inbound --output none
Correr network nsg rule create --resource-group $Grupo --nsg-name "nsg-$Vm" --name web `
    --priority 110 --protocol Tcp --destination-port-ranges 80 443 --source-address-prefixes Internet `
    --access Allow --direction Inbound --output none

Write-Host "3. La VM (tarda un par de minutos)"
Correr vm create --resource-group $Grupo --name $Vm --location $Region `
    --image Ubuntu2404 --size Standard_B2ats_v2 `
    --admin-username $Usuario --ssh-key-values $ClavePublica --authentication-type ssh `
    --nsg "nsg-$Vm" --public-ip-sku Standard --public-ip-address-dns-name $Dns `
    --storage-sku Premium_LRS --os-disk-size-gb 64 `
    --os-disk-delete-option Delete --nic-delete-option Delete `
    --custom-data (Join-Path $aqui "cloud-init.yaml") --output none

$nombre = & $az vm show --resource-group $Grupo --name $Vm --show-details --query fqdns -o tsv
$ip = & $az vm show --resource-group $Grupo --name $Vm --show-details --query publicIps -o tsv
Write-Host ""
Write-Host "Lista: $nombre ($ip)"
Write-Host "Entrar: ssh -i $env:USERPROFILE\.ssh\longbox_azure $Usuario@$nombre"
