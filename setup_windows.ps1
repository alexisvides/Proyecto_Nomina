Param(
    [string]$PythonExe = "python",
    [string]$VenvDir = ".venv"
)

Write-Host "Creando virtualenv en $VenvDir ..."
& $PythonExe -m venv $VenvDir
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el virtualenv" }

$activate = Join-Path $VenvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) { throw "No se encontró el script de activación: $activate" }

Write-Host "Activando virtualenv..."
. $activate

Write-Host "Actualizando pip..."
python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    Write-Host "Instalando dependencias..."
    pip install -r requirements.txt
}
else {
    Write-Host "No existe requirements.txt, se omitirá instalación de dependencias."
}

# Copiar .env.example -> .env si no existe
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Write-Host "Generando .env desde .env.example..."
    Copy-Item ".env.example" ".env"
}

Write-Host "Iniciando la app Flask..."
python app.py
