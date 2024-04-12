#!/bin/bash

echo "Completeing repository cloning by initializing submodules..."

cd ..
git submodule update --init
cd PythonClient
git checkout origin/main

echo "Done. Required submodules are up to date."
