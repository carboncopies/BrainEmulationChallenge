#!/bin/bash

echo "Checking remote submodules repositories for updates..."

cd ../PythonClient
git pull origin main

# Update dependencies if requirements.txt changed
echo "Updating Python dependencies..."
../venv/bin/pip install -r ../requirements.txt --upgrade

echo "Done. Your submodules and dependencies are up to date."