@echo off
setlocal
title amaru_fo PDF TOOL
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0pdftool.py" menu
    goto :end
)

echo.
echo =====================================================
echo   amaru_fo PDF TOOL no esta instalado todavia
echo =====================================================
echo.
echo Se abrira el instalador. Cuando termine, vuelve a abrir esta herramienta.
echo.
pause
call "%~dp0install_windows.bat"

:end
echo.
echo Puedes cerrar esta ventana.
pause >nul
