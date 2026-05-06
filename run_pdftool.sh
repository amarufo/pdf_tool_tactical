#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ -x .venv/bin/python ]]; then
    exec .venv/bin/python pdftool.py menu
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 pdftool.py menu
fi

if command -v python >/dev/null 2>&1; then
    exec python pdftool.py menu
fi

printf 'No encontre Python. Instala Python 3 y ejecuta ./install_linux.sh\n' >&2
exit 1