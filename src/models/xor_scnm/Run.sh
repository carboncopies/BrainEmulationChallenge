#!/bin/bash

# Local front-end to remote API server options
Rhost="pve.braingenix.org"
Rport="8000"

# Default values
executeat="r"
subdivide="10"
resolution="0.1"
modelfile="nesvbp-xor-res-sep-targets"
modelname="xor_scnm"
neuroglancer=""
segmentation=""
meshes=""
simID=""
host=""
port=""
forceURLbase=""

# Function to display usage
usage() {
    echo "Usage: $0 [-R] [-x execute-at] [-s subdivide] [-r resolution] [-f modelfile] [-m modelname] [-n] [-S] [-M] [-F baseURL] [-i simID]"
    echo "  -R  running locally to remote API server at $Rhost:$Rport"
    echo "  -x  start executing at step (default r)"
    echo "      options are:"
    echo "        r - reservoir generation (Netmorph)"
    echo "        c - connectome tuning"
    echo "        a - acquisition of data set"
    echo "  -s  subdivide size (default 10)"
    echo "  -r  resolution (default 0.1 um)"
    echo "  -f  model file name (default nesvbp-xor-res-sep-targets)"
    echo "  -m  model name (default xor_scnm)"
    echo "  -n  Generate Neuroglancer data"
    echo "  -S  Generate segmentation files"
    echo "  -M  Generate mesh files"
    echo "  -F  Force URL base of Neuroglancer URL (only needed if running"
    echo "      this script on remote API server but browsing locally)"
    echo "  -i  reconnect with simID and (re)run acquisition"
    exit 1
}

# Parse command line arguments
while getopts "Rs:r:f:m:x:nSMF:i:" opt; do
  case ${opt} in
    R )
      host="-Host $Rhost"
      port="-Port $Rport"
      ;;
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
    n )
      neuroglancer="-Neuroglancer"
      ;;
    S )
      segmentation="-Segmentation"
      ;;
    M )
      meshes="-Meshes"
      ;;
    F )
      forceURLbase="-NeuroglancerURLBase $OPTARG"
      ;;
    i )
      simID=$OPTARG
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

if [ "$host" != "" -a "$neuroglancer" != "" -a "$forceURLbase" == "" ]; then
  forceURLbase="-NeuroglancerURLBase http://$Rhost:$Rport"
fi

if [ "$simID" = "" ]; then
  modelname="$USER-$modelname"
else
  modelfile=""
  modelname=""
  executeat="a"
fi

echo "Using:"
echo "  execute-at  : $executeat"
echo "  subdivide   : $subdivide"
echo "  resolution  : $resolution"
echo "  modelfile   : $modelfile"
echo "  modelname   : $modelname"
echo "  neuroglancer: $neuroglancer"
echo "  segmentation: $segmentation"
echo "  meshes      : $meshes"
echo "  simID       : $simID"
echo "  host        : $host"
echo "  port        : $port"
echo "  forceURLbase: $forceURLbase"

if [ "$executeat" = "r" ]; then
# Use Netmorph to build the reservoir
./xor_scnm_groundtruth_reservoir.py $host $port -modelfile "$modelfile" -modelname "$modelname"
fi

if [ "$executeat" = "r" -o "$executeat" = "c" ]; then
# Tune the synapses in the reservoir
./xor_scnm_groundtruth_connectome.py $host $port -modelname "$modelname"
fi

if [ "$simID" = "" ]; then
  # Acquire data sets
  ./xor_scnm_acquisition_direct.py $host $port -modelname "$modelname-tuned" -RenderEM -SubdivideSize "$subdivide" $neuroglancer $segmentation $meshes $forceURLbase -Resolution_um "$resolution"
else
  # Acquire data sets by rerunning a simulation that is still in NES server memory
  ./xor_scnm_acquisition_direct.py $host $port -simID "$simID" -RenderEM -SubdivideSize "$subdivide" $neuroglancer $segmentation $meshes $forceURLbase -Resolution_um "$resolution"
fi
