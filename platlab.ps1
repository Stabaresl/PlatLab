<#
.SYNOPSIS
    Instala y administra PlatLAB en este computador (Windows 10/11).

.DESCRIPTION
    Deja la plataforma completa funcionando con Docker Desktop: base de datos,
    backend, workers, laboratorios Docker y la interfaz web, todo detrás de un
    solo puerto. Se puede volver a ejecutar sin miedo: no borra datos y sirve
    también para actualizar.

.EXAMPLE
    instalar.cmd
    Doble clic: instala (o actualiza) haciendo las preguntas necesarias.

.EXAMPLE
    .\platlab.ps1 instalar -Modo red -AdminEmail profe@universidad.edu.co

.EXAMPLE
    .\platlab.ps1 iniciar | detener | estado | logs [servicio] | actualizar | desinstalar [-BorrarDatos]
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('instalar', 'iniciar', 'detener', 'estado', 'logs', 'actualizar', 'desinstalar', 'ayuda')]
    [string]$Accion = 'instalar',

    [Parameter(Position = 1)]
    [string]$Servicio,

    [ValidateSet('local', 'red')]
    [string]$Modo,

    [ValidateRange(0, 65535)]
    [int]$Puerto = 0,

    [string]$AdminEmail,

    [string]$AdminNombre = 'Administrador',

    [switch]$SinPreguntas,

    [switch]$BorrarDatos
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$EnvPath = Join-Path $PSScriptRoot '.env'
$EnvExample = Join-Path $PSScriptRoot '.env.example'
$ComposeArgs = @('compose', '-f', 'docker-compose.yml', '-f', 'docker-compose.local.yml')
$ComposeMinimo = [version]'2.24.4'   # `!reset` / `!override` en docker-compose.local.yml
$Utf8SinBom = New-Object System.Text.UTF8Encoding($false)

# --- Salida ---------------------------------------------------------------

function Write-Titulo([string]$Texto) {
    Write-Host ''
    Write-Host "== $Texto " -ForegroundColor Cyan
}
function Write-Ok([string]$Texto) { Write-Host "  [ok] $Texto" -ForegroundColor Green }
function Write-Info([string]$Texto) { Write-Host "  $Texto" }
function Write-Aviso([string]$Texto) { Write-Host "  [!] $Texto" -ForegroundColor Yellow }
function Stop-ConError([string]$Texto) {
    Write-Host ''
    Write-Host "  [x] $Texto" -ForegroundColor Red
    exit 1
}

function Read-SiNo([string]$Pregunta, [bool]$PorDefecto = $true) {
    if ($SinPreguntas) { return $PorDefecto }
    $sufijo = if ($PorDefecto) { '[S/n]' } else { '[s/N]' }
    $r = (Read-Host "  $Pregunta $sufijo").Trim().ToLower()
    if ($r -eq '') { return $PorDefecto }
    return ($r -eq 's' -or $r -eq 'si' -or $r -eq 'sí' -or $r -eq 'y')
}

# --- Docker ---------------------------------------------------------------

function Invoke-Docker {
    # Llama a docker con los argumentos dados y falla si el código de salida
    # no es 0 (los ejecutables nativos no lanzan excepción por sí solos).
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "docker $($args -join ' ') terminó con código $LASTEXITCODE" }
}

function Invoke-Compose {
    $todo = $ComposeArgs + $args
    & docker @todo
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($args -join ' ') terminó con código $LASTEXITCODE" }
}

function Invoke-ConReintentos([scriptblock]$Bloque, [string]$Que, [int]$Intentos = 4) {
    # Descargar imágenes es lo único que depende de internet, y en redes de
    # aula (o con el DNS de Docker Desktop) los cortes momentáneos son comunes.
    for ($i = 1; $i -le $Intentos; $i++) {
        try { & $Bloque; return } catch {
            if ($i -eq $Intentos) { throw }
            Write-Aviso "$Que falló (intento $i de $Intentos), probablemente por la red. Reintento en 10 s..."
            Start-Sleep -Seconds 10
        }
    }
}

function Invoke-NativoSilencioso {
    # Ejecuta un comando nativo descartando su stderr; quien llama revisa
    # $LASTEXITCODE. En Windows PowerShell 5.1, redirigir stderr con
    # $ErrorActionPreference='Stop' convierte cualquier línea de stderr en una
    # excepción (ej. "docker info" con el motor apagado): aquí se baja a
    # 'Continue' solo dentro de esta función.
    $ErrorActionPreference = 'Continue'
    $exe = $args[0]
    $resto = @($args | Select-Object -Skip 1)
    & $exe @resto 2> $null
}

function Test-DockerActivo {
    Invoke-NativoSilencioso docker info --format '{{.ServerVersion}}' | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-IdContenedor([string]$Nombre) {
    $todo = $ComposeArgs + @('ps', '-q', $Nombre)
    $id = Invoke-NativoSilencioso docker @todo
    if ($LASTEXITCODE -ne 0 -or -not $id) { return $null }
    return ($id | Select-Object -First 1).Trim()
}

# --- .env -----------------------------------------------------------------

function New-Secreto([int]$Bytes = 32) {
    # Hex: sin caracteres que docker compose interprete en .env ($, comillas).
    $buffer = New-Object byte[] $Bytes
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($buffer)
    $rng.Dispose()
    return (($buffer | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Get-EnvValor([string]$Clave) {
    if (-not (Test-Path -LiteralPath $EnvPath)) { return $null }
    foreach ($linea in [System.IO.File]::ReadAllLines($EnvPath)) {
        if ($linea -match "^\s*$([regex]::Escape($Clave))\s*=(.*)$") { return $Matches[1].Trim() }
    }
    return $null
}

function Set-EnvValor([string]$Clave, [string]$Valor) {
    $lineas = New-Object System.Collections.Generic.List[string]
    $encontrada = $false
    if (Test-Path -LiteralPath $EnvPath) {
        foreach ($linea in [System.IO.File]::ReadAllLines($EnvPath)) {
            if ($linea -match "^\s*#?\s*$([regex]::Escape($Clave))\s*=") {
                if (-not $encontrada) { $lineas.Add("$Clave=$Valor"); $encontrada = $true }
                continue
            }
            $lineas.Add($linea)
        }
    }
    if (-not $encontrada) { $lineas.Add("$Clave=$Valor") }
    [System.IO.File]::WriteAllLines($EnvPath, $lineas, $Utf8SinBom)
}

function Test-ClaveDebil([string]$Valor) {
    return (-not $Valor) -or $Valor.Length -lt 40 -or $Valor -match 'changeme|insecure|cambiar'
}

# --- Red ------------------------------------------------------------------

function Get-IpLocal {
    try {
        $ip = Get-NetIPConfiguration |
            Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
            ForEach-Object { $_.IPv4Address.IPAddress } |
            Select-Object -First 1
        if ($ip) { return $ip }
    } catch { }
    return $null
}

function Test-EsAdministrador {
    $identidad = [Security.Principal.WindowsIdentity]::GetCurrent()
    return (New-Object Security.Principal.WindowsPrincipal($identidad)).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

# --- Pasos ----------------------------------------------------------------

function Assert-Requisitos {
    Write-Titulo 'Revisando requisitos'

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Stop-ConError ("No encontré Docker. Instala Docker Desktop desde " +
            "https://docs.docker.com/desktop/setup/install/windows-install/ , ábrelo una vez y vuelve a ejecutar este instalador.")
    }

    $versionTexto = Invoke-NativoSilencioso docker compose version --short
    if ($LASTEXITCODE -ne 0 -or -not $versionTexto) {
        Stop-ConError 'Docker está instalado pero falta "docker compose" (v2). Actualiza Docker Desktop.'
    }
    $versionLimpia = ($versionTexto.Trim() -replace '^v', '') -replace '[-+].*$', ''
    try { $versionCompose = [version]$versionLimpia } catch { $versionCompose = [version]'0.0' }
    if ($versionCompose -lt $ComposeMinimo) {
        Stop-ConError "Tu docker compose es $versionTexto y PlatLAB necesita $ComposeMinimo o superior. Actualiza Docker Desktop."
    }
    Write-Ok "docker compose $versionTexto"

    if (-not (Test-DockerActivo)) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (Test-Path -LiteralPath $desktop) {
            Write-Info 'Docker Desktop no está corriendo; lo abro y espero a que arranque (hasta 3 min)...'
            Start-Process -FilePath $desktop | Out-Null
            $limite = (Get-Date).AddMinutes(3)
            while (-not (Test-DockerActivo)) {
                if ((Get-Date) -gt $limite) { Stop-ConError 'Docker Desktop no terminó de arrancar. Ábrelo a mano, espera a que diga "Engine running" y vuelve a intentar.' }
                Start-Sleep -Seconds 3
            }
        } else {
            Stop-ConError 'Docker no está corriendo. Abre Docker Desktop, espera a que diga "Engine running" y vuelve a intentar.'
        }
    }
    Write-Ok 'Docker está corriendo'

    $memoria = Invoke-NativoSilencioso docker info --format '{{.MemTotal}}'
    if ($memoria -and ([int64]$memoria) -lt 6GB) {
        Write-Aviso ("Docker tiene {0:N1} GB de RAM. Con menos de 6 GB los laboratorios pueden fallar con muchos estudiantes: " -f ($memoria / 1GB) +
            'súbela en Docker Desktop > Settings > Resources.')
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Aviso 'No encontré git: la instalación funciona igual, pero "actualizar" no podrá descargar versiones nuevas.'
    }
}

function Resolve-Modo {
    if ($Modo) { return $Modo }
    $guardado = Get-EnvValor 'PLATLAB_MODO'
    if ($SinPreguntas) { if ($guardado) { return $guardado } else { return 'local' } }

    Write-Titulo '¿Cómo se va a usar PlatLAB?'
    Write-Info '[1] Solo en este computador: ideal para probar. Trae cuentas demo con contraseñas conocidas.'
    Write-Info '[2] En red / aula: otros equipos entran por la IP de este. Las cuentas demo se desactivan'
    Write-Info '    y creas tu propia cuenta de administrador.'
    $defecto = if ($guardado -eq 'red') { '2' } else { '1' }
    while ($true) {
        $r = (Read-Host "  Elige 1 o 2 [$defecto]").Trim()
        if ($r -eq '') { $r = $defecto }
        if ($r -eq '1') { return 'local' }
        if ($r -eq '2') { return 'red' }
    }
}

function Initialize-Env([string]$ModoElegido, [int]$PuertoElegido) {
    Write-Titulo 'Preparando la configuración (.env)'

    if (-not (Test-Path -LiteralPath $EnvPath)) {
        Copy-Item -LiteralPath $EnvExample -Destination $EnvPath
        Set-EnvValor 'SECRET_KEY' (New-Secreto 32)
        Set-EnvValor 'FLAG_HASH_KEY' (New-Secreto 32)
        Set-EnvValor 'POSTGRES_PASSWORD' (New-Secreto 24)
        Set-EnvValor 'DEBUG' 'False'
        Set-EnvValor 'DJANGO_ADMIN_URL' ("panel-$(New-Secreto 6)/")
        Write-Ok '.env creado con claves aleatorias nuevas'
    } else {
        $copia = "$EnvPath.respaldo-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item -LiteralPath $EnvPath -Destination $copia
        Write-Ok "Usando el .env existente (respaldo en $(Split-Path -Leaf $copia))"

        $secret = Get-EnvValor 'SECRET_KEY'
        if (Test-ClaveDebil $secret) {
            # Las flags y respuestas de examen guardadas se firmaron con la
            # SECRET_KEY vieja: se conserva como FLAG_HASH_KEY para que sigan
            # validando después de rotarla.
            if (-not (Get-EnvValor 'FLAG_HASH_KEY') -and $secret) { Set-EnvValor 'FLAG_HASH_KEY' $secret }
            Set-EnvValor 'SECRET_KEY' (New-Secreto 32)
            Write-Ok 'SECRET_KEY era débil: la cambié por una aleatoria (las sesiones abiertas se cierran)'
        }
        if ((Get-EnvValor 'POSTGRES_PASSWORD') -eq 'changeme') {
            Write-Aviso ('POSTGRES_PASSWORD sigue en "changeme". No la cambio solo porque la base ya existe con esa clave; ' +
                'la base no está expuesta fuera de Docker, así que el riesgo es bajo.')
        }
    }

    Set-EnvValor 'PLATLAB_MODO' $ModoElegido
    Set-EnvValor 'PLATLAB_PORT' "$PuertoElegido"
    if ($ModoElegido -eq 'red') { Set-EnvValor 'PLATLAB_BIND' '0.0.0.0' } else { Set-EnvValor 'PLATLAB_BIND' '127.0.0.1' }
}

function Resolve-Puerto {
    if ($Puerto -gt 0) { return $Puerto }
    $guardado = Get-EnvValor 'PLATLAB_PORT'
    if ($guardado -match '^\d+$') { return [int]$guardado }
    return 8080
}

function Assert-PuertoLibre([int]$PuertoElegido) {
    if (Get-IdContenedor 'gateway') { return }   # ya es nuestro
    $ocupado = Get-NetTCPConnection -LocalPort $PuertoElegido -State Listen -ErrorAction SilentlyContinue
    if ($ocupado) {
        Stop-ConError "El puerto $PuertoElegido ya lo usa otro programa. Vuelve a ejecutar con otro, por ejemplo: .\platlab.ps1 instalar -Puerto 8090"
    }
}

function Build-ImagenesLaboratorio {
    Write-Titulo 'Construyendo las imágenes de los laboratorios'
    $targets = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'docker\targets') -Directory -ErrorAction SilentlyContinue
    foreach ($dir in $targets) {
        $archivoImagen = Join-Path $dir.FullName 'IMAGE'
        if (-not (Test-Path -LiteralPath $archivoImagen)) { continue }
        $tag = ([System.IO.File]::ReadAllText($archivoImagen)).Trim()
        Write-Info "$tag  <-  docker\targets\$($dir.Name)"
        $contexto = $dir.FullName
        Invoke-ConReintentos -Que "La imagen $tag" -Bloque { Invoke-Docker build --quiet -t $tag $contexto | Out-Null }
        Write-Ok $tag
    }
}

function Start-Plataforma([switch]$Construir) {
    if ($Construir) {
        Write-Titulo 'Construyendo y levantando PlatLAB (la primera vez tarda varios minutos)'
        Invoke-ConReintentos -Que 'La construcción' -Bloque { Invoke-Compose up -d --build --remove-orphans }
    } else {
        Write-Titulo 'Levantando PlatLAB'
        Invoke-Compose up -d --remove-orphans
    }
}

function Wait-Plataforma([int]$PuertoElegido) {
    Write-Info 'Esperando a que el backend termine de arrancar (migraciones incluidas)...'
    $limite = (Get-Date).AddMinutes(6)
    while ($true) {
        $id = Get-IdContenedor 'web'
        if ($id) {
            $salud = Invoke-NativoSilencioso docker inspect -f '{{.State.Health.Status}}' $id
            if ($salud -eq 'healthy') { break }
        }
        if ((Get-Date) -gt $limite) {
            Stop-ConError 'El backend no arrancó a tiempo. Revisa qué pasó con: .\platlab.ps1 logs web'
        }
        Start-Sleep -Seconds 3
    }
    $url = "http://127.0.0.1:$PuertoElegido/api/v1/health/"
    $limite = (Get-Date).AddMinutes(2)
    while ($true) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { break }
        } catch { }
        if ((Get-Date) -gt $limite) {
            Stop-ConError 'El backend está arriba pero la interfaz web no responde. Revisa: .\platlab.ps1 logs gateway'
        }
        Start-Sleep -Seconds 2
    }
    Write-Ok 'PlatLAB responde'
}

function Invoke-Semillas([string]$ModoElegido) {
    Write-Titulo 'Cargando laboratorios, mapa de aprendizaje y catálogo de logros'
    # actualizar_contenido_labs va después de los seeds: les pone las guías paso a
    # paso, la consola realista y el examen (también a instalaciones viejas).
    foreach ($comando in @('seed_demo_data', 'seed_roadmap_labs', 'seed_labs_expansion', 'seed_gamification_catalog', 'actualizar_contenido_labs')) {
        Write-Info $comando
        Invoke-Compose exec -T web python manage.py $comando | Out-Null
    }
    Write-Ok 'Contenido cargado'

    if ($ModoElegido -ne 'red') {
        # Si antes se instaló en modo red/aula, las cuentas demo quedaron deshabilitadas.
        Invoke-Compose exec -T web python manage.py seed_demo_data --activar-cuentas-demo | Out-Null
        Invoke-Compose exec -T web python manage.py seed_sala_demo | Out-Null
        Write-Ok 'Cuentas demo activas y sala demo lista (código PRUEBA)'
    }

    if ($ModoElegido -eq 'red') {
        Invoke-Compose exec -T web python manage.py seed_demo_data --desactivar-cuentas-demo | Out-Null
        Write-Ok 'Cuentas demo desactivadas (sus contraseñas son públicas en el repositorio)'
        New-Administrador
    }
}

function New-Administrador {
    $email = $AdminEmail
    $nombre = $AdminNombre
    if (-not $email) {
        if ($SinPreguntas) {
            Write-Aviso 'Sin -AdminEmail no creo administrador. Créalo luego con: .\platlab.ps1 instalar -AdminEmail tu@correo'
            return
        }
        Write-Titulo 'Cuenta de administrador'
        while ($true) {
            $email = (Read-Host '  Correo del administrador').Trim()
            if ($email -match '^[^@\s]+@[^@\s]+\.[^@\s]+$') { break }
            Write-Aviso 'Ese correo no parece válido.'
        }
        $n = (Read-Host "  Nombre completo [$nombre]").Trim()
        if ($n) { $nombre = $n }
    }
    # La contraseña la genera el comando y la muestra UNA vez (no queda en
    # ningún archivo ni en el historial de la consola).
    Invoke-Compose exec -T web python manage.py create_production_users --admin-email $email --admin-nombre $nombre
}

function Set-Firewall([int]$PuertoElegido) {
    $nombreRegla = "PlatLAB ($PuertoElegido)"
    $existe = Get-NetFirewallRule -DisplayName $nombreRegla -ErrorAction SilentlyContinue
    if ($existe) { Write-Ok "El firewall ya permite el puerto $PuertoElegido"; return }

    $comando = "New-NetFirewallRule -DisplayName '$nombreRegla' -Direction Inbound -Protocol TCP -LocalPort $PuertoElegido -Action Allow -Profile Private,Domain"
    if (Test-EsAdministrador) {
        New-NetFirewallRule -DisplayName $nombreRegla -Direction Inbound -Protocol TCP -LocalPort $PuertoElegido `
            -Action Allow -Profile Private, Domain | Out-Null
        Write-Ok "Firewall: abierto el puerto $PuertoElegido para redes privadas"
    } else {
        Write-Aviso 'Para que otros equipos entren, abre el puerto en el firewall. En una PowerShell "como administrador":'
        Write-Host "      $comando" -ForegroundColor Gray
    }

    $publicas = Get-NetConnectionProfile -ErrorAction SilentlyContinue | Where-Object { $_.NetworkCategory -eq 'Public' }
    if ($publicas) {
        Write-Aviso ("Tu red '$($publicas[0].Name)' está marcada como Pública y Windows bloquea conexiones entrantes en ella. " +
            'Cámbiala a Privada en Configuración > Red e Internet > Propiedades.')
    }
}

function Show-Resumen([string]$ModoElegido, [int]$PuertoElegido) {
    Write-Host ''
    Write-Host '  ==============================================================' -ForegroundColor Green
    Write-Host '   PlatLAB está listo' -ForegroundColor Green
    Write-Host '  ==============================================================' -ForegroundColor Green
    Write-Info "En este computador:   http://localhost:$PuertoElegido"
    if ($ModoElegido -eq 'red') {
        $ip = Get-IpLocal
        if ($ip) { Write-Info "Desde otros equipos:  http://${ip}:$PuertoElegido" }
        else { Write-Info "Desde otros equipos:  http://<IP-de-este-equipo>:$PuertoElegido" }
    } else {
        Write-Info ''
        Write-Info 'Cuentas demo (solo accesibles desde este computador):'
        Write-Info '  administrador  admin@platlab.demo        Admin1234'
        Write-Info '  instructor     instructor@platlab.demo   Instructor1234'
        Write-Info '  estudiante     estudiante@platlab.demo   Estudiante1234'
        Write-Info 'Sala de prueba: entra como estudiante a Salas y usa el código PRUEBA.'
    }
    $panel = Get-EnvValor 'DJANGO_ADMIN_URL'
    if ($panel) { Write-Info "Admin de Django:      http://localhost:$PuertoElegido/$panel" }
    Write-Info ''
    Write-Info 'Para el día a día:  .\platlab.ps1 iniciar | detener | estado | logs | actualizar'
}

# --- Acciones -------------------------------------------------------------

function Invoke-Instalar([switch]$Actualizando) {
    Assert-Requisitos
    $modoElegido = Resolve-Modo
    $puertoElegido = Resolve-Puerto
    Assert-PuertoLibre $puertoElegido
    Initialize-Env $modoElegido $puertoElegido
    Build-ImagenesLaboratorio
    Start-Plataforma -Construir
    Wait-Plataforma $puertoElegido
    Invoke-Semillas $modoElegido
    if ($modoElegido -eq 'red') { Set-Firewall $puertoElegido }
    Show-Resumen $modoElegido $puertoElegido
    if (-not $SinPreguntas -and (Read-SiNo '¿Abrir PlatLAB en el navegador ahora?')) {
        Start-Process "http://localhost:$puertoElegido"
    }
}

function Invoke-Desinstalar {
    if (-not (Test-DockerActivo)) { Stop-ConError 'Docker no está corriendo.' }
    if ($BorrarDatos) {
        Write-Aviso 'Esto borra TODOS los datos de PlatLAB: usuarios, progreso, archivos subidos.'
        if (-not $SinPreguntas) {
            $r = Read-Host '  Escribe BORRAR para confirmar'
            if ($r -ne 'BORRAR') { Write-Info 'Cancelado.'; return }
        }
        Invoke-Compose down --remove-orphans --volumes
    } else {
        Invoke-Compose down --remove-orphans
    }
    $labs = & docker ps -aq --filter 'label=platlab.lab-environment=true'
    if ($labs) { Invoke-Docker rm -f @labs | Out-Null }
    Write-Ok 'PlatLAB detenido y contenedores eliminados.'
    if (-not $BorrarDatos) { Write-Info 'Los datos se conservan. Para borrarlos también: .\platlab.ps1 desinstalar -BorrarDatos' }
}

try {
    switch ($Accion) {
        'instalar' { Invoke-Instalar }
        'actualizar' {
            if ((Get-Command git -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.git'))) {
                Write-Titulo 'Descargando la última versión'
                & git pull --ff-only
                if ($LASTEXITCODE -ne 0) { Stop-ConError 'git pull falló (¿cambios locales sin guardar?). Resuélvelo y vuelve a intentar.' }
            }
            $SinPreguntas = $true
            Invoke-Instalar
        }
        'iniciar' {
            Assert-Requisitos
            $p = Resolve-Puerto
            Start-Plataforma
            Wait-Plataforma $p
            Show-Resumen (Get-EnvValor 'PLATLAB_MODO') $p
        }
        'detener' { Invoke-Compose stop; Write-Ok 'PlatLAB detenido. Para volver: .\platlab.ps1 iniciar' }
        'estado' { Invoke-Compose ps }
        'logs' {
            if ($Servicio) { Invoke-Compose logs -f --tail 200 $Servicio } else { Invoke-Compose logs -f --tail 50 }
        }
        'desinstalar' { Invoke-Desinstalar }
        'ayuda' { Get-Help $PSCommandPath -Detailed }
    }
} catch {
    Stop-ConError $_.Exception.Message
}
