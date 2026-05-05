$ErrorActionPreference = "Stop"

$AuthorPage = "https://amarufo.github.io/PAGE-AIP/"
$TesseractUrl = "https://github.com/UB-Mannheim/tesseract"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "+------------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "| $Message" -ForegroundColor Cyan
    Write-Host "+------------------------------------------------------------+" -ForegroundColor Cyan
}

function Find-Python {
    $candidates = @(
        @{ Command = "py"; Args = @("-3.12", "-c", "import sys; print(sys.executable)") },
        @{ Command = "py"; Args = @("-3", "-c", "import sys; print(sys.executable)") },
        @{ Command = "python"; Args = @("-c", "import sys; print(sys.executable)") }
    )
    foreach ($candidate in $candidates) {
        try {
            $path = & $candidate.Command @($candidate.Args) 2>$null
            if ($LASTEXITCODE -eq 0 -and $path) {
                return $path.Trim()
            }
        } catch {
        }
    }
    return $null
}

function Test-Tesseract {
    $paths = @(
        (Get-Command tesseract -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
        "C:\Program Files\Tesseract-OCR\tesseract.exe",
        "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Tesseract-OCR\tesseract.exe")
    )
    foreach ($path in $paths) {
        if ($path -and (Test-Path $path)) {
            return $path
        }
    }
    return $null
}

function Show-Tesseract-Guide {
    Write-Host ""
    Write-Host "OCR necesita Tesseract para Windows." -ForegroundColor Yellow
    Write-Host "Pagina recomendada: $TesseractUrl" -ForegroundColor Cyan
    Write-Host "Descarga el instalador de UB-Mannheim, instalalo y vuelve a ejecutar esta herramienta." -ForegroundColor Yellow
}

if (Test-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "ascci.txt")) {
    Get-Content -Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "ascci.txt") | Write-Host -ForegroundColor Green
} else {
    Write-Host @"
 /\_/\
( o.o )   Instalador amaru_fo PDF TOOL
 > ^ <
"@ -ForegroundColor Green
}

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = Join-Path $env:LOCALAPPDATA "AmaruFoPdfTool"
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopDir "amaru_fo PDF TOOL.lnk"

Write-Step "1. Preparando carpeta de instalacion"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $SourceDir "pdftool.py") -Destination $InstallDir -Force
Copy-Item -Path (Join-Path $SourceDir "requirements.txt") -Destination $InstallDir -Force
Copy-Item -Path (Join-Path $SourceDir "requirements-optional.txt") -Destination $InstallDir -Force
Copy-Item -Path (Join-Path $SourceDir "ascci.txt") -Destination $InstallDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $SourceDir "README.md") -Destination $InstallDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $SourceDir "PDFTOOL.md") -Destination $InstallDir -Force
Copy-Item -Path (Join-Path $SourceDir "LEEME_PRIMERO.txt") -Destination $InstallDir -Force -ErrorAction SilentlyContinue

Write-Step "2. Buscando Python"
$PythonExe = Find-Python
if (-not $PythonExe) {
    Write-Host "No encontre Python instalado." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Intentare instalar Python 3.12 con winget. Acepta los permisos si Windows los pide." -ForegroundColor Yellow
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        $PythonExe = Find-Python
    }
}

if (-not $PythonExe) {
    Write-Host "" -ForegroundColor Red
    Write-Host "No se pudo instalar o encontrar Python automaticamente." -ForegroundColor Red
    Write-Host "Instala Python desde https://www.python.org/downloads/ y marca 'Add Python to PATH'." -ForegroundColor Red
    Write-Host "Luego vuelve a ejecutar install_windows.bat." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "Python encontrado: $PythonExe" -ForegroundColor Green

Write-Step "3. Creando entorno de la herramienta"
$VenvDir = Join-Path $InstallDir ".venv"
& $PythonExe -m venv $VenvDir
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Write-Step "4. Instalando dependencias necesarias"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $InstallDir "requirements.txt")

Write-Step "5. OCR opcional: Tesseract y librerias extra"
$InstallOcr = Read-Host "Quieres instalar soporte OCR ahora? Recomendado para PDFs escaneados. [S/n]"
if ($InstallOcr.Trim().ToLower() -ne "n") {
    & $VenvPython -m pip install -r (Join-Path $InstallDir "requirements-optional.txt")
    $TesseractPath = Test-Tesseract
    if ($TesseractPath) {
        Write-Host "Tesseract encontrado: $TesseractPath" -ForegroundColor Green
    } elseif (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Intentare instalar Tesseract OCR de UB-Mannheim con winget." -ForegroundColor Yellow
        winget install --id UB-Mannheim.TesseractOCR -e --accept-package-agreements --accept-source-agreements
        $TesseractPath = Test-Tesseract
        if ($TesseractPath) {
            Write-Host "Tesseract instalado: $TesseractPath" -ForegroundColor Green
        } else {
            Show-Tesseract-Guide
            Start-Process $TesseractUrl
        }
    } else {
        Show-Tesseract-Guide
        Start-Process $TesseractUrl
    }
} else {
    Write-Host "OCR omitido. Puedes instalarlo despues desde: $TesseractUrl" -ForegroundColor Yellow
}

Write-Step "6. Creando archivo para abrir la herramienta"
$RunBat = Join-Path $InstallDir "abrir_amaru_fo_pdf_tool.bat"
@"
@echo off
cd /d "%~dp0"
title amaru_fo PDF TOOL
"%~dp0.venv\Scripts\python.exe" "%~dp0pdftool.py" menu
echo.
echo Puedes cerrar esta ventana.
pause >nul
"@ | Set-Content -Path $RunBat -Encoding ASCII

Write-Step "7. Creando acceso directo en el Escritorio"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $RunBat
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.WindowStyle = 1
$Shortcut.Description = "amaru_fo PDF TOOL"
$Shortcut.Save()

Write-Step "Instalacion terminada"
Write-Host @"
 /\_/\
( ^.^ )   Listo. Busca en el Escritorio: amaru_fo PDF TOOL
 > ^ <
"@ -ForegroundColor Green
Write-Host "Carpeta instalada: $InstallDir" -ForegroundColor Green
Write-Host "Pagina: $AuthorPage" -ForegroundColor Cyan
Write-Host "OCR/Tesseract: $TesseractUrl" -ForegroundColor Cyan
Read-Host "Presiona Enter para cerrar"
