# ============================================
# SCRIPT DE VERIFICACIÓN DEL SISTEMA
# Diagnóstico completo del entorno
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  VERIFICACIÓN DEL SISTEMA - DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$errores = 0
$advertencias = 0

# ============================================
# 1. PYTHON
# ============================================
Write-Host "[1/8] Python" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    $versionNumber = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    Write-Host "  ✓ Python instalado: $pythonVersion" -ForegroundColor Green
    Write-Host "    Ruta: $(which python)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Python NO instalado" -ForegroundColor Red
    $errores++
}

# ============================================
# 2. ENTORNO VIRTUAL
# ============================================
Write-Host "`n[2/8] Entorno Virtual" -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  ✓ Entorno virtual existe" -ForegroundColor Green
    if (Test-Path ".venv\Scripts\python.exe") {
        $venvPython = & .venv\Scripts\python.exe --version 2>&1
        Write-Host "    Python en .venv: $venvPython" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Entorno virtual NO existe" -ForegroundColor Red
    Write-Host "    Ejecuta: python -m venv .venv" -ForegroundColor Yellow
    $errores++
}

# ============================================
# 3. DEPENDENCIAS
# ============================================
Write-Host "`n[3/8] Dependencias de Python" -ForegroundColor Yellow
$requiredPackages = @("flask", "pyodbc", "python-dotenv", "reportlab")

foreach ($package in $requiredPackages) {
    $installed = & .venv\Scripts\pip.exe show $package 2>&1
    if ($installed -match "Name: $package") {
        $version = ($installed | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "  ✓ $package $version" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $package NO instalado" -ForegroundColor Red
        $errores++
    }
}

# ============================================
# 4. SQL SERVER
# ============================================
Write-Host "`n[4/8] SQL Server" -ForegroundColor Yellow
$sqlServices = Get-Service -Name "*SQL*" -ErrorAction SilentlyContinue | Where-Object {$_.Name -like "*MSSQL*"}

if ($sqlServices) {
    foreach ($service in $sqlServices) {
        if ($service.Status -eq "Running") {
            Write-Host "  ✓ $($service.DisplayName): Running" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ $($service.DisplayName): $($service.Status)" -ForegroundColor Yellow
            $advertencias++
        }
    }
} else {
    Write-Host "  ✗ SQL Server NO encontrado" -ForegroundColor Red
    $errores++
}

# ============================================
# 5. ODBC DRIVERS
# ============================================
Write-Host "`n[5/8] ODBC Drivers" -ForegroundColor Yellow
$odbcDrivers = @(
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server"
)

$driverFound = $false
foreach ($driver in $odbcDrivers) {
    $registryPath = "HKLM:\SOFTWARE\ODBC\ODBCINST.INI\$driver"
    if (Test-Path $registryPath) {
        Write-Host "  ✓ $driver" -ForegroundColor Green
        $driverFound = $true
    }
}

if (-not $driverFound) {
    Write-Host "  ✗ No hay drivers ODBC instalados" -ForegroundColor Red
    $errores++
}

# ============================================
# 6. ARCHIVOS DE CONFIGURACIÓN
# ============================================
Write-Host "`n[6/8] Archivos de Configuración" -ForegroundColor Yellow

$configFiles = @{
    "app.py" = "Aplicación principal"
    "db.py" = "Configuración de BD"
    "requirements.txt" = "Dependencias"
    "CREATE_DATABASE_COMPLETE.sql" = "Script de BD"
}

foreach ($file in $configFiles.Keys) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length / 1KB
        Write-Host "  ✓ $file ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file NO encontrado" -ForegroundColor Red
        $errores++
    }
}

if (Test-Path ".env") {
    Write-Host "  ✓ .env encontrado" -ForegroundColor Green
} else {
    Write-Host "  ⚠ .env NO encontrado (opcional)" -ForegroundColor Yellow
    $advertencias++
}

# ============================================
# 7. CONEXIÓN A BASE DE DATOS
# ============================================
Write-Host "`n[7/8] Conexión a Base de Datos" -ForegroundColor Yellow

if (Test-Path "test_conexion.py") {
    $testResult = & .venv\Scripts\python.exe test_conexion.py 2>&1
    
    if ($testResult -match "Conexión exitosa") {
        Write-Host "  ✓ Conexión exitosa" -ForegroundColor Green
        
        if ($testResult -match "Base de datos actual: (\w+)") {
            Write-Host "    BD: $($Matches[1])" -ForegroundColor Gray
        }
        
        if ($testResult -match "Tablas en la base de datos \((\d+)\)") {
            Write-Host "    Tablas: $($Matches[1])" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ Error de conexión" -ForegroundColor Red
        $errores++
        if ($testResult -match "Login failed") {
            Write-Host "    Error: Credenciales incorrectas" -ForegroundColor Red
        }
        elseif ($testResult -match "Error al buscar el servidor") {
            Write-Host "    Error: Servidor no encontrado" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ⚠ test_conexion.py NO encontrado" -ForegroundColor Yellow
    $advertencias++
}

# ============================================
# 8. PUERTOS
# ============================================
Write-Host "`n[8/8] Puertos" -ForegroundColor Yellow

$port = 5000
$portInUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "  ⚠ Puerto $port en uso" -ForegroundColor Yellow
    Write-Host "    PID: $($portInUse.OwningProcess)" -ForegroundColor Gray
    $advertencias++
} else {
    Write-Host "  ✓ Puerto $port disponible" -ForegroundColor Green
}

# ============================================
# RESUMEN
# ============================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  RESUMEN DEL DIAGNÓSTICO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($errores -eq 0 -and $advertencias -eq 0) {
    Write-Host "`n✅ TODO CORRECTO" -ForegroundColor Green
    Write-Host "   El sistema está listo para ejecutarse" -ForegroundColor Green
} elseif ($errores -eq 0) {
    Write-Host "`n⚠ SISTEMA FUNCIONAL CON ADVERTENCIAS" -ForegroundColor Yellow
    Write-Host "   Advertencias: $advertencias" -ForegroundColor Yellow
    Write-Host "   El sistema puede ejecutarse pero revisa las advertencias" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ SISTEMA CON ERRORES" -ForegroundColor Red
    Write-Host "   Errores: $errores" -ForegroundColor Red
    Write-Host "   Advertencias: $advertencias" -ForegroundColor Yellow
    Write-Host "   Corrige los errores antes de ejecutar" -ForegroundColor Red
}

# ============================================
# INFORMACIÓN DEL SISTEMA
# ============================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  INFORMACIÓN DEL SISTEMA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`nSistema Operativo:" -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "  $($os.Caption) - $($os.Version)" -ForegroundColor Gray

Write-Host "`nMemoria RAM:" -ForegroundColor Yellow
$totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
Write-Host "  Total: $totalRAM GB | Libre: $freeRAM GB" -ForegroundColor Gray

Write-Host "`nProcesador:" -ForegroundColor Yellow
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
Write-Host "  $($cpu.Name)" -ForegroundColor Gray

Write-Host "`nEspacio en Disco (C:):" -ForegroundColor Yellow
$disk = Get-PSDrive C
$totalSpace = [math]::Round($disk.Used / 1GB + $disk.Free / 1GB, 2)
$freeSpace = [math]::Round($disk.Free / 1GB, 2)
Write-Host "  Total: $totalSpace GB | Libre: $freeSpace GB" -ForegroundColor Gray

Write-Host ""
