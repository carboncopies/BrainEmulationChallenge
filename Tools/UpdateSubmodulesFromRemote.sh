#!/bin/bash

echo "Checking remote submodules repositories for updates..."

cd ../PythonClient
git pull

echo "Done. Your submodules are up to date."
