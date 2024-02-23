#!/bin/bash

echo "Pushing and recursively pushing submodule commits as well..."

git push --recurse-submodules=on-demand

echo "Done."
