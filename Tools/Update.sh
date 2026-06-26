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

echo "Synchronizing and refreshing submodules..."
run_cmd git submodule sync --recursive
run_cmd git submodule update --init --recursive --remote

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Virtual environment not found at $VENV_DIR."
    echo "Run Tools/Setup.sh first."
    exit 1
fi

echo "Updating Python dependencies..."
run_cmd "$VENV_DIR/bin/python" -m pip install --upgrade pip
run_cmd "$VENV_DIR/bin/python" -m pip install -r "$REPO_ROOT/requirements.txt" --upgrade

echo "Done. Your submodules and dependencies are up to date."
