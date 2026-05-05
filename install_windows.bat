@echo off
setlocal
title Instalador amaru_fo PDF TOOL
cd /d "%~dp0"

echo.
echo =====================================================
echo   Instalador amaru_fo PDF TOOL
echo =====================================================
echo.
echo Este instalador preparara Python, dependencias, OCR opcional y un acceso directo.
echo Para OCR puede instalar o abrir la guia de Tesseract UB-Mannheim.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1"
echo.
echo Si no viste errores, ya puedes abrir "amaru_fo PDF TOOL" desde el Escritorio.
echo.
pause
