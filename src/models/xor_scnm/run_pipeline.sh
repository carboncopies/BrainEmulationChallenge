#!/bin/bash
 
# =============================================================================
# run_pipeline.sh
# Automates: acquisition → build HDF5 → run metrics
#
# Usage:
#   ./run_pipeline.sh                           # full pipeline
#   ./run_pipeline.sh --skip-acquisition        # reuse existing raw data
#   ./run_pipeline.sh --output-folder output/20260412121829.917106-acquisition
# =============================================================================
#
# set -e  # Exit on any error
#
# ---- Defaults ----

mkdir -p output

NETWORK_CONFIG="network_config.json"
SKIP_ACQUISITION=false
FULL_REBUILD=true
OUTPUT_FOLDER=""

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--network-config) NETWORK_CONFIG="$2";   shift 2;;
        --skip-acquisition)  SKIP_ACQUISITION=false;  shift;;
        --full-rebuild)      FULL_REBUILD=true;      shift;;
        --raw-folder)        OUTPUT_FOLDER="$2";        shift 2;;
        -h|--help)
            echo "Usage: ./run_pipeline.sh [options]"
            echo "  -n, --network-config PATH Path to network_config.json"
            echo "  --skip-acquisition        Skip step 1, reuse existing raw data"
            echo "  --full-rebuild            Regrow network from scratch (NETMORPH + tune + acquire)"
            echo "  --output-folder PATH      Path to existing output data folder"
            exit 0;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

echo "============================================="
echo " Brain Emulation Challenge Pipeline"
echo "============================================="
echo ""

# ---- Step 1: Acquisition ----
# Run_flat.sh -x flag controls where to start:
#   -x r = full rebuild (NETMORPH growth → connectome tuning → acquisition)
#   -x c = connectome tuning → acquisition
#   -x a = acquisition only (model already grown and tuned)
if [ "$SKIP_ACQUISITION" = false ]; then
    if [ "$FULL_REBUILD" = true ]; then
        echo "[Step 1/4] Full rebuild: growing network + tuning + acquisition..."
        ./Run_flat.sh -x r
    else
        echo "[Step 1/4] Running acquisition only (model already built)..."
        ./Run_flat.sh -x a
    fi

    OUTPUT_FOLDER=$(ls -dt output/*-acquisition | head -1)
    echo "  Output: $OUTPUT_FOLDER"
else
    if [ -z "$OUTPUT_FOLDER" ]; then
        OUTPUT_FOLDER=$(ls -dt output/*-acquisition | head -1)
    fi
    echo "[Step 1/4] Skipping acquisition, using: $OUTPUT_FOLDER"
fi

# Verify output files exist
for f in groundtruth-Vm.csv groundtruth-spikes.csv trial_map.json; do
    if [ ! -f "$OUTPUT_FOLDER/$f" ]; then
        echo "ERROR: Missing $f in $OUTPUT_FOLDER"
        exit 1
    fi
done
echo "  Output files verified."
echo ""

# ---- Step 2: Copy network config into raw folder ----
echo "[Step 2/4] Adding network_config.json..."

if [ ! -f "$OUTPUT_FOLDER/network_config.json" ]; then
    if [ -f "$NETWORK_CONFIG" ]; then
        cp "$NETWORK_CONFIG" "$OUTPUT_FOLDER/network_config.json"
        echo "  Copied $NETWORK_CONFIG → $OUTPUT_FOLDER/"
    else
        echo "ERROR: network_config.json not found at $NETWORK_CONFIG"
        echo "  Provide path with --network-config /path/to/file"
        exit 1
    fi
else
    echo "  Already present in $OUTPUT_FOLDER/"
fi
echo ""

# ---- Step 3: Build HDF5 ----
echo "[Step 3/4] Building HDF5 file..."

H5_FOLDER="output/GT_h5"
mkdir -p "$H5_FOLDER"
H5_FILE="$H5_FOLDER/groundtruth.h5"

if [ -f "$H5_FILE" ]; then
    echo "  Removing old $H5_FILE"
    rm "$H5_FILE"
fi

python -c "
import sys
sys.path.insert(0, '.')
from build_h5 import build_h5

converter = build_h5(
    vm_csv='$OUTPUT_FOLDER/groundtruth-Vm.csv',
    spikes_csv='$OUTPUT_FOLDER/groundtruth-spikes.csv',
    net_con='$OUTPUT_FOLDER/network_config.json',
    t_map='$OUTPUT_FOLDER/trial_map.json',
    h5_file_path='$H5_FILE',
)
converter.build()
"

echo "  Output: $H5_FILE"
echo ""

# ---- Step 4: Run metrics ----
echo "[Step 4/4] Running in-domain metrics..."

export MPLBACKEND=Agg

METRICS_FOLDER="output/GT_h5"
mkdir -p "$METRICS_FOLDER"

python in_domain_metrics.py \
    --gt "$H5_FILE" \
    --output "$METRICS_FOLDER" \
    2>&1 | tee "$METRICS_FOLDER/metrics_log.txt"

echo ""
echo "============================================="
echo " Pipeline complete!"
echo "============================================="
echo " output data:    $OUTPUT_FOLDER"
echo " HDF5:        $H5_FILE"
echo " Metrics:     $METRICS_FOLDER"
echo "============================================="


