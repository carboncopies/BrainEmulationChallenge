#!/bin/bash

echo "Completeing repository cloning by initializing submodules..."

git submodule update --init

echo "Done. Required submodules are up to date."
