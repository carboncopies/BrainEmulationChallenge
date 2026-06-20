#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/venv"

run_cmd() {
    echo "Running: $*"
    "$@"
}

echo "Entering repository root: $REPO_ROOT"
cd "$REPO_ROOT"

echo "Synchronizing and initializing submodules..."
run_cmd git submodule sync --recursive
run_cmd git submodule update --init --recursive

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment at $VENV_DIR"
    run_cmd python3 -m venv "$VENV_DIR"
fi

echo "Installing Python dependencies..."
run_cmd "$VENV_DIR/bin/python" -m pip install --upgrade pip
run_cmd "$VENV_DIR/bin/python" -m pip install -r "$REPO_ROOT/requirements.txt"

echo "Done. Required submodules are up to date."
echo "Activate the virtual environment with: source $VENV_DIR/bin/activate"
