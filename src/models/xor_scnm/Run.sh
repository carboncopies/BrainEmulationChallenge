#!/bin/bash

echo "This script expects the following arguments:"
echo "  1: subdivide size (default 10)"
echo "  2: resolution (default 0.1 um)"
echo "  3: model file name (default nesvbp-xor-res-sep-targets)"
echo "  4: model name (default xor_scnm)"

subdivide=$1
resolution=$2
modelfile=$3
modelname=$4

if [ "$subdivide" = "" ]; then
  subdivide="10"
fi
if [ "$resolution" = "" ]; then
  resolution="0.1"
fi
if [ "$modelfile" = "" ]; then
  modelfile="nesvbp-xor-res-sep-targets"
fi
if [ "$modelname" = "" ]; then
  modelname="xor_scnm"
fi

echo "Using:"
echo "  subdivide : $subdivide"
echo "  resolution: $resolution"
echo "  modelfile : $modelfile"
echo "  modelname : $modelname"

# Use Netmorph to build the reservoir
./xor_scnm_groundtruth_reservoir.py -modelfile "$modelfile" -modelname "$modelname"

# Tune the synapses in the reservoir
./xor_scnm_groundtruth_connectome.py -modelname "$modelname"

# Acquire data sets
./xor_scnm_acquisition_direct.py -modelname "$modelname-tuned" -RenderEM -NoDownloadEM -SubdivideSize "$subdivide" -Neuroglancer -Resolution_um "$resolution"

