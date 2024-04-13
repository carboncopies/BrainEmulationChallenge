#!/bin/bash

echo "Checking remote submodules repositories for updates..."

cd ../PythonClient
git pull origin main

echo "Done. Your submodules are up to date."
