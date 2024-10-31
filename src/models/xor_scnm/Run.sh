#!/bin/bash

echo "This script expects an argument which is the netmorph model file to run (this message shows if you have or have not given one)"

./xor_scnm_groundtruth_reservoir.py -modelfile "$1"
./xor_scnm_groundtruth_connectome.py

./xor_scnm_acquisition_direct.py -RenderEM -NoDownloadEM -SubdivideSize 8 -Neuroglancer

