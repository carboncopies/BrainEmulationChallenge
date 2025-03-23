#!/bin/bash

# Default values
executeat="r"
subdivide="10"
resolution="0.1"
modelfile="nesvbp-xor-res-sep-targets"
modelname="xor_scnm"

# Function to display usage
usage() {
    echo "Usage: $0 [-x execute-at] [-s subdivide] [-r resolution] [-f modelfile] [-m modelname]"
    echo "  -x  start executing at step (default r)"
    echo "      options are:"
    echo "        r - reservoir generation (Netmorph)"
    echo "        c - connectome tuning"
    echo "        a - acquisition of data set"
    echo "  -s  subdivide size (default 10)"
    echo "  -r  resolution (default 0.1 um)"
    echo "  -f  model file name (default nesvbp-xor-res-sep-targets)"
    echo "  -m  model name (default xor_scnm)"
    exit 1
}

# Parse command line arguments
while getopts ":s:r:f:m:x:" opt; do
  case ${opt} in
    x )
      executeat=$OPTARG
      ;;
    s )
      subdivide=$OPTARG
      ;;
    r )
      resolution=$OPTARG
      ;;
    f )
      modelfile=$OPTARG
      ;;
    m )
      modelname=$OPTARG
      ;;
    \? )
      echo "Invalid option: -$OPTARG" 1>&2
      usage
      ;;
    : )
      echo "Invalid option: -$OPTARG requires an argument" 1>&2
      usage
      ;;
  esac
done
shift $((OPTIND -1))

echo "Using:"
echo "  execute-at: $executeat"
echo "  subdivide : $subdivide"
echo "  resolution: $resolution"
echo "  modelfile : $modelfile"
echo "  modelname : $modelname"

if [ "$executeat" = "r" ]; then
# Use Netmorph to build the reservoir
./xor_scnm_groundtruth_reservoir.py -modelfile "$modelfile" -modelname "$modelname"
fi

if [ "$executeat" = "r" -o "$executeat" = "c" ]; then
# Tune the synapses in the reservoir
./xor_scnm_groundtruth_connectome.py -modelname "$modelname"
fi

# Acquire data sets
./xor_scnm_acquisition_direct.py -modelname "$modelname-tuned" -RenderEM -NoDownloadEM -SubdivideSize "$subdivide" -Neuroglancer -Resolution_um "$resolution"
