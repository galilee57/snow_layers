#!/bin/bash
# Lance le prototype local dans le navigateur par défaut.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  /usr/bin/python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
"$VENV_DIR/bin/python" -m pip install --quiet -r requirements.txt

export PYTHONPATH="$PROJECT_DIR/src"
open "http://127.0.0.1:5000"
exec "$VENV_DIR/bin/python" app.py
