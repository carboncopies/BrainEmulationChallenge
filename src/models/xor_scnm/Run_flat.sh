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

# These are kept for backward compatibility with old Run.sh usage,
# but acquisition_template.py will NOT use them.
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
    echo "  -x  start executing at step (default r): r (reservoir), c (connectome), a (acquisition)"
    echo "  -s  subdivide size (default 10)   [not used by minimal acquisition template]"
    echo "  -r  resolution (default 0.1 um)   [not used by minimal acquisition template]"
    echo "  -f  model file name (default nesvbp-xor-res-sep-targets)"
    echo "  -m  model name (default xor_scnm)"
    echo "  -n  Generate Neuroglancer data    [not used by minimal acquisition template]"
    echo "  -S  Generate segmentation files   [not used by minimal acquisition template]"
    echo "  -M  Generate mesh files           [not used by minimal acquisition template]"
    echo "  -F  Force Neuroglancer URL base   [not used by minimal acquisition template]"
    echo "  -i  reconnect with simID          [not used by minimal acquisition template]"
    echo ""
    echo "Note: Acquisition now runs ./acquisition_template.py (minimal functional)."
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

# Preserve original behavior for remote neuroglancer URL base (unused now)
if [ "$host" != "" -a "$neuroglancer" != "" -a "$forceURLbase" == "" ]; then
  forceURLbase="-NeuroglancerURLBase http://$Rhost:$Rport"
fi

# Original naming behavior (keep)
if [ "$simID" = "" ]; then
  modelname="$USER-$modelname"
else
  # simID reuse not supported in template acquisition; force acquisition step anyway
  modelfile=""
  modelname=""
  executeat="a"
fi

echo "Using:"
echo "  execute-at  : $executeat"
echo "  modelfile   : $modelfile"
echo "  modelname   : $modelname"
echo "  host        : $host"
echo "  port        : $port"

if [ "$executeat" = "r" ]; then
  # Use Netmorph to build the reservoir
  ./xor_scnm_groundtruth_reservoir.py $host $port -modelfile "$modelfile" -modelname "$modelname"
fi

if [ "$executeat" = "r" -o "$executeat" = "c" ]; then
  # Tune the synapses in the reservoir
  ./xor_scnm_groundtruth_connectome.py $host $port -modelname "$modelname"
fi

# Acquire data sets (MINIMAL FUNCTIONAL TEMPLATE)
# IMPORTANT: this template does NOT use imaging/neuroglancer/subdivide/resolution/simID options.
if [ "$executeat" = "r" -o "$executeat" = "c" -o "$executeat" = "a" ]; then
  python3 acquisition_template.py $host $port -modelname "$modelname-tuned" -ExpsDB "./ExpsDB.json"
fi

echo " -- Done."
