#!/bin/bash

echo "Checking remote submodules repositories for updates..."

git submodule update --remote PythonClient

echo "Done. Your submodules are up to date."
