#!/bin/bash

# Shift Register LIFC - Run Script
# Connects to BrainGenix NES server and runs the shift register simulation.

# Local front-end to remote API server options
Rhost="pve.braingenix.org"
Rport="8000"

# Default values
host=""
port=""
seed="0"
stdp=""
reload=""
burst=""
long_burst=""

# Function to display usage
usage() {
    echo "Usage: $0 [-R] [-S seed] [--stdp] [--reload] [--burst] [--long]"
    echo "  -R       connect to remote API server at $Rhost:$Rport"
    echo "  -S seed  set random seed (default 0)"
    echo "  --stdp   enable STDP learning"
    echo "  --reload reload saved model instead of creating new"
    echo "  --burst  burst input mode"
    echo "  --long   long burst driver"
    echo ""
    echo "Examples:"
    echo ""
    echo "  ./Run.sh -R"
    echo "  Runs the shift register simulation on the remote NES server."
    echo ""
    echo "  ./Run.sh"
    echo "  Runs the shift register simulation on localhost:8000."
    echo ""
    echo "  ./Run.sh -R -S 42"
    echo "  Remote run with seed 42."
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -R)
      host="-Host $Rhost"
      port="-Port $Rport"
      shift
      ;;
    -S)
      seed="$2"
      shift 2
      ;;
    --stdp)
      stdp="-STDP"
      shift
      ;;
    --reload)
      reload="-Reload"
      shift
      ;;
    --burst)
      burst="-Burst"
      shift
      ;;
    --long)
      long_burst="-Long"
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

echo "Shift Register LIFC"
echo "==================="
echo "Using:"
echo "  host   : ${host:-localhost}"
echo "  port   : ${port:-8000}"
echo "  seed   : $seed"
echo "  stdp   : ${stdp:-disabled}"
echo "  reload : ${reload:-no}"
echo "  burst  : ${burst:-no}"
echo "  long   : ${long_burst:-no}"
echo ""

# Create output directory
mkdir -p output

# Run the shift register simulation
./shift_register_lifc.py $host $port -Seed "$seed" $stdp $reload $burst $long_burst
