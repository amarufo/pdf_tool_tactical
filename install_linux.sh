#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

AUTHOR_PAGE="https://amarufo.github.io/PAGE-AIP/"

step() {
    printf '\n+------------------------------------------------------------+\n'
    printf '| %s\n' "$1"
    printf '+------------------------------------------------------------+\n'
}

find_python() {
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && {
                command -v "$candidate"
                return 0
            }
        fi
    done
    return 1
}

if [[ -f ascci.txt ]]; then
    cat ascci.txt
else
    printf 'amaru_fo PDF TOOL - instalador Linux\n'
fi

step "1. Buscando Python 3.10 o superior"
PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
    printf 'No encontre Python 3.10 o superior. Instala python3 y python3-venv.\n' >&2
    printf 'Debian/Ubuntu: sudo apt install python3 python3-venv python3-pip\n' >&2
    exit 1
fi
printf 'Python encontrado: %s\n' "$PYTHON_BIN"

step "2. Creando entorno virtual local"
"$PYTHON_BIN" -m venv .venv
VENV_PYTHON=".venv/bin/python"

step "3. Instalando dependencias necesarias"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt

step "4. OCR opcional"
read -r -p "Quieres instalar librerias Python para OCR ahora? [S/n] " INSTALL_OCR
if [[ "${INSTALL_OCR,,}" != "n" ]]; then
    "$VENV_PYTHON" -m pip install -r requirements-optional.txt
    if command -v tesseract >/dev/null 2>&1; then
        printf 'Tesseract encontrado: %s\n' "$(command -v tesseract)"
    else
        printf 'Tesseract no esta instalado. Para OCR instala tambien el motor del sistema.\n'
        printf 'Debian/Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-spa\n'
        printf 'Fedora: sudo dnf install tesseract tesseract-langpack-spa\n'
        printf 'Arch: sudo pacman -S tesseract tesseract-data-spa\n'
    fi
else
    printf 'OCR omitido. Puedes instalarlo despues con: ./.venv/bin/python -m pip install -r requirements-optional.txt\n'
fi

step "5. Preparando lanzador"
chmod +x run_pdftool.sh

step "Instalacion terminada"
printf 'Ejecuta la herramienta con: ./run_pdftool.sh\n'
printf 'O por CLI: ./.venv/bin/python pdftool.py --help\n'
printf 'Pagina: %s\n' "$AUTHOR_PAGE"