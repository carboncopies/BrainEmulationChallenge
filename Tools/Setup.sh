#!/bin/bash

echo "Completing repository cloning by initializing submodules..."

cd ..
git submodule update --init
cd PythonClient
git checkout origin/main

# Create venv and install dependencies
echo "Creating virtual environment and installing dependencies..."
python3 -m venv ../venv
../venv/bin/pip install -r ../requirements.txt

echo "Done. Required submodules are up to date."
echo "Activate the virtual environment with: source venv/bin/activate"