# ============================================
# SCRIPT DE CONFIGURACIÓN AUTOMÁTICA
# Sistema de Nómina - Proyecto Flask
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN AUTOMÁTICA - SISTEMA NÓMINA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# 1. VERIFICAR PYTHON
# ============================================
Write-Host "[1/7] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python no está instalado" -ForegroundColor Red
    Write-Host "  Descarga Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Verificar versión mínima (3.8+)
$versionNumber = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$versionNumber -lt [version]"3.8") {
    Write-Host "  ✗ Se requiere Python 3.8 o superior. Versión actual: $versionNumber" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================
# 2. VERIFICAR/CREAR ENTORNO VIRTUAL
# ============================================
Write-Host "[2/7] Configurando entorno virtual..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Write-Host "  ⚠ Entorno virtual existente encontrado" -ForegroundColor Yellow
    $response = Read-Host "  ¿Desea recrearlo? (S/N)"
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host "  Eliminando entorno virtual anterior..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
        Write-Host "  Creando nuevo entorno virtual..." -ForegroundColor Yellow
        python -m venv .venv
        Write-Host "  ✓ Entorno virtual recreado" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Usando entorno virtual existente" -ForegroundColor Green
    }
} else {
    Write-Host "  Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "  ✓ Entorno virtual creado" -ForegroundColor Green
}

Write-Host ""

# ============================================
# 3. INSTALAR DEPENDENCIAS
# ============================================
Write-Host "[3/7] Instalando dependencias..." -ForegroundColor Yellow

Write-Host "  Actualizando pip..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m pip install --upgrade pip --quiet

Write-Host "  Instalando paquetes..." -ForegroundColor Cyan
$packages = @("flask", "python-dotenv", "pyodbc", "reportlab")

foreach ($package in $packages) {
    Write-Host "    - Instalando $package..." -ForegroundColor Gray
    & .venv\Scripts\pip.exe install $package --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✓ $package instalado" -ForegroundColor Green
    } else {
        Write-Host "      ✗ Error instalando $package" -ForegroundColor Red
    }
}

Write-Host ""

# ============================================
# 4. VERIFICAR SQL SERVER
# ============================================
Write-Host "[4/7] Verificando SQL Server..." -ForegroundColor Yellow

$sqlService = Get-Service -Name "MSSQLSERVER" -ErrorAction SilentlyContinue

if ($sqlService) {
    if ($sqlService.Status -eq "Running") {
        Write-Host "  ✓ SQL Server está corriendo" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ SQL Server está detenido" -ForegroundColor Yellow
        Write-Host "  Intentando iniciar SQL Server..." -ForegroundColor Cyan
        try {
            Start-Service -Name "MSSQLSERVER"
            Write-Host "  ✓ SQL Server iniciado" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ No se pudo iniciar SQL Server (se requieren permisos de administrador)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ✗ SQL Server no está instalado" -ForegroundColor Red
    Write-Host "  Instala SQL Server Express desde:" -ForegroundColor Yellow
    Write-Host "  https://www.microsoft.com/sql-server/sql-server-downloads" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# 5. VERIFICAR ODBC DRIVER
# ============================================
Write-Host "[5/7] Verificando ODBC Driver..." -ForegroundColor Yellow

$odbcDrivers = @(
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server"
)

$driverFound = $false
foreach ($driver in $odbcDrivers) {
    $registryPath = "HKLM:\SOFTWARE\ODBC\ODBCINST.INI\$driver"
    if (Test-Path $registryPath) {
        Write-Host "  ✓ $driver encontrado" -ForegroundColor Green
        $driverFound = $true
        break
    }
}

if (-not $driverFound) {
    Write-Host "  ✗ No se encontró ningún driver ODBC" -ForegroundColor Red
    Write-Host "  Descarga ODBC Driver desde:" -ForegroundColor Yellow
    Write-Host "  https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# 6. CREAR ARCHIVO .env (SI NO EXISTE)
# ============================================
Write-Host "[6/7] Configurando archivo .env..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "  Creando archivo .env..." -ForegroundColor Cyan
    
    $envContent = @"
# Configuración de la aplicación
SECRET_KEY=dev-secret-key-change-in-production-$(Get-Random)
FLASK_ENV=development
FLASK_DEBUG=True

# Configuración de base de datos
DB_SERVER=localhost
DB_NAME=proyecto
DB_USER=sa
DB_PASSWORD=123
USE_WINDOWS_AUTH=True

# Porcentaje de IGSS (default: 4.83%)
IGSS_PCT=4.83

# Puerto de la aplicación
PORT=5000
"@
    
    Set-Content -Path ".env" -Value $envContent
    Write-Host "  ✓ Archivo .env creado" -ForegroundColor Green
} else {
    Write-Host "  ✓ Archivo .env ya existe" -ForegroundColor Green
}

Write-Host ""

# ============================================
# 7. PROBAR CONEXIÓN
# ============================================
Write-Host "[7/7] Probando conexión a la base de datos..." -ForegroundColor Yellow

$testResult = & .venv\Scripts\python.exe test_conexion.py 2>&1

if ($testResult -match "Conexión exitosa") {
    Write-Host "  ✓ Conexión a base de datos exitosa" -ForegroundColor Green
    
    # Extraer número de tablas
    if ($testResult -match "Tablas en la base de datos \((\d+)\)") {
        $numTablas = $Matches[1]
        Write-Host "  ✓ $numTablas tablas encontradas en la base de datos" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ Error de conexión a la base de datos" -ForegroundColor Red
    Write-Host "  Revisa la configuración en db.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Detalles del error:" -ForegroundColor Yellow
    Write-Host $testResult -ForegroundColor Gray
}

Write-Host ""

# ============================================
# RESUMEN Y PRÓXIMOS PASOS
# ============================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Activar el entorno virtual:" -ForegroundColor White
Write-Host "   .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Ejecutar la aplicación:" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Abrir en el navegador:" -ForegroundColor White
Write-Host "   http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Credenciales por defecto:" -ForegroundColor White
Write-Host "   Usuario: admin" -ForegroundColor Cyan
Write-Host "   Contraseña: (ver base de datos)" -ForegroundColor Cyan
Write-Host ""

# ============================================
# OPCIÓN DE EJECUTAR AUTOMÁTICAMENTE
# ============================================
$response = Read-Host "¿Desea ejecutar la aplicación ahora? (S/N)"
if ($response -eq "S" -or $response -eq "s") {
    Write-Host ""
    Write-Host "Iniciando aplicación..." -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
    Write-Host ""
    & .venv\Scripts\python.exe app.py
}

Write-Host ""
Write-Host "¡Configuración completada! 🎉" -ForegroundColor Green
