#!/bin/bash

echo "This script expects an argument which is the netmorph model file to run (this message shows if you have or have not given one)"

# Check if $1 is empty
if [ -z "$1" ]; then
  # Set $1 to a default value
  set -- "nesvbp-xor-res-sep-targets"
fi

./xor_scnm_groundtruth_reservoir.py -modelfile "$1"
./xor_scnm_groundtruth_connectome.py

./xor_scnm_acquisition_direct.py -RenderEM -NoDownloadEM -SubdivideSize 10 -Neuroglancer -Resolution_um 0.1

