#!/bin/bash
 
# =============================================================================
# run_pipeline.sh
# Automates: acquisition → stage output/GT + output/SUB → HDF5 → metrics → dashboard
#
# Usage:
#   ./run_pipeline.sh --full-rebuild --pinggy           # full pipeline
#   ./run_pipeline.sh --skip-acquisition        # reuse existing raw data
#   ./run_pipeline.sh --output-folder output/20260412121829.917106-acquisition
#   ./run_pipeline.sh --no-dashboard            # skip dashboard launch
#   ./run_pipeline.sh --pinggy                  # expose dashboard via pinggy
#   ./run_pipeline.sh --skip-blackbox-sub       # skip IF SUB + substitute.h5 + gt_sub metrics
#
# Artifacts (for debugging failed steps):
#   output/GT/   — gt-Vm.csv, gt-spikes.csv, network_config.json, trial_map.json, groundtruth.h5
#   output/SUB/  — blackbox_sub-Vm.csv, blackbox_sub-spikes.csv, network_config.json, trial_map.json, substitute.h5
#   output/METRICS/ — dashboard copy, metric logs, gt_sub CSV/JSON, plots from in_domain_metrics
#
# Black-box IF XOR is vendored under vendor_if_xor/ (no IFneuron-model repo required).
# =============================================================================
#
# set -e  # Exit on any error
#
# ---- Defaults ----

mkdir -p output

NETWORK_CONFIG="network_config.json"
SKIP_ACQUISITION=false
FULL_REBUILD=false
OUTPUT_FOLDER=""
DASHBOARD_FILE="dashboard.py"
LAUNCH_DASHBOARD=true
USE_PINGGY=false
DASHBOARD_PORT=8501
SKIP_BLACKBOX_SUB=false

GT_DIR="output/GT"
SUB_DIR="output/SUB"
METRICS_DIR="output/METRICS"

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--network-config) NETWORK_CONFIG="$2";    shift 2;;
        --skip-acquisition)  SKIP_ACQUISITION=true;  shift;;
        --full-rebuild)      FULL_REBUILD=true;      shift;;
        --output-folder)     OUTPUT_FOLDER="$2";     shift 2;;
	-d|--dashboard)      DASHBOARD_FILE="$2";    shift 2;;
	--no-dashboard)      LAUNCH_DASHBOARD=false; shift;;
	--pinggy)            USE_PINGGY=true;        shift;;
	--port)              DASHBOARD_PORT="$2";    shift 2;;
	--skip-blackbox-sub) SKIP_BLACKBOX_SUB=true; shift;;
        -h|--help)
            echo "Usage: ./run_pipeline.sh [options]"
            echo "  -n, --network-config PATH Path to network_config.json"
            echo "  --skip-acquisition        Skip step 1 (use --output-folder or latest output/*-acquisition)"
            echo "  --full-rebuild            Build the full pipeline"
            echo "  --output-folder PATH      Path to existing output data folder"
	    echo "  -d, --dashboard PATH      Path to dashboard.py"
	    echo "  --no-dashboard            Skip launching the Streamlit dashboard"
	    echo "  --pinggy                  Expose dashboard via Pinggy tunnel"
	    echo "  --port PORT               Dashboard port (default: 8501)"
	    echo "  --skip-blackbox-sub       Skip IF black-box SUB, substitute.h5, and GT–SUB metrics"
            exit 0;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

echo "============================================="
echo " Brain Emulation Challenge Pipeline"
echo "============================================="
echo ""

# ---- Step 1: Acquisition ----
if [ "$SKIP_ACQUISITION" = false ]; then
    if [ "$FULL_REBUILD" = true ]; then
        echo "[Step 1] Full rebuild: growing network + tuning + acquisition..."
        ./Run_flat.sh -x r
    else
        echo "[Step 1] Running acquisition only (model already built)..."
        ./Run_flat.sh -x a
    fi

    OUTPUT_FOLDER=$(ls -dt output/*-acquisition | head -1)
    echo "  Output: $OUTPUT_FOLDER"
else
    if [ -z "$OUTPUT_FOLDER" ]; then
        OUTPUT_FOLDER=$(ls -dt output/*-acquisition | head -1)
    fi
    echo "[Step 1] Skipping acquisition, using: $OUTPUT_FOLDER"
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

# ---- Step 2: Copy network config into raw acquisition folder ----
echo "[Step 2] Adding network_config.json..."

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

# ---- Step 2b: Stage dedicated GT folder (inspectable if later steps fail) ----
echo "[Step 2b] Staging $GT_DIR/ ..."
mkdir -p "$GT_DIR"
cp "$OUTPUT_FOLDER/groundtruth-Vm.csv" "$GT_DIR/gt-Vm.csv"
cp "$OUTPUT_FOLDER/groundtruth-spikes.csv" "$GT_DIR/gt-spikes.csv"
cp "$OUTPUT_FOLDER/network_config.json" "$GT_DIR/network_config.json"
cp "$OUTPUT_FOLDER/trial_map.json" "$GT_DIR/trial_map.json"
echo "  → $GT_DIR/gt-Vm.csv, gt-spikes.csv, network_config.json, trial_map.json"
echo ""

# ---- Step 3: Build GT HDF5 ----
echo "[Step 3] Building GT HDF5 → $GT_DIR/groundtruth.h5 ..."

H5_FILE="$GT_DIR/groundtruth.h5"
if [ -f "$H5_FILE" ]; then
    echo "  Removing old $H5_FILE"
    rm "$H5_FILE"
fi

python -c "
import sys
sys.path.insert(0, '.')
from build_h5 import build_h5

build_h5(
    vm_csv='$GT_DIR/gt-Vm.csv',
    spikes_csv='$GT_DIR/gt-spikes.csv',
    net_con='$GT_DIR/network_config.json',
    t_map='$GT_DIR/trial_map.json',
    h5_file_path='$H5_FILE',
).build()
"

echo "  Output: $H5_FILE"
echo ""

# ---- Step 3b–3c: Black-box SUB + HDF5 + I/O metrics ----
SUB_H5="$SUB_DIR/substitute.h5"
ROOT="$(pwd)"
export XOR_GT_H5_PATH="$ROOT/$H5_FILE"
unset XOR_SUB_H5_PATH

if [ "$SKIP_BLACKBOX_SUB" = false ]; then
    echo "[Step 3b] Black-box SUB → $SUB_DIR/ ..."
    mkdir -p "$SUB_DIR"
    python blackbox_if_xor_sub.py \
        --trial-map "$GT_DIR/trial_map.json" \
        --network-config "$GT_DIR/network_config.json" \
        --out-dir "$SUB_DIR"

    if [ -f "$SUB_H5" ]; then
        echo "  Removing old $SUB_H5"
        rm "$SUB_H5"
    fi
    python -c "
import sys
sys.path.insert(0, '.')
from build_h5 import build_h5

build_h5(
    vm_csv='$SUB_DIR/blackbox_sub-Vm.csv',
    spikes_csv='$SUB_DIR/blackbox_sub-spikes.csv',
    net_con='$SUB_DIR/network_config.json',
    t_map='$SUB_DIR/trial_map.json',
    h5_file_path='$SUB_H5',
).build()
"
    echo "  SUB HDF5: $SUB_H5"

    mkdir -p "$METRICS_DIR"
    echo "[Step 3c] GT vs SUB (I/O + behaviour) metrics → $METRICS_DIR/ ..."
    python in_domain_gt_sub_metrics.py \
        --gt "$H5_FILE" \
        --sub "$SUB_H5" \
        --output "$METRICS_DIR" \
        --network-config "$GT_DIR/network_config.json"
    export XOR_SUB_H5_PATH="$ROOT/$SUB_H5"
    echo ""
else
    echo "[Step 3b/c] Skipping black-box SUB (--skip-blackbox-sub)."
    echo ""
fi

# ---- Step 4: Run full in_domain_metrics ----
echo "[Step 4] Running in-domain metrics (full notebook-style script)..."

export MPLBACKEND=Agg
mkdir -p "$METRICS_DIR"
mkdir -p output/plots

python in_domain_metrics.py \
    --gt "$H5_FILE" \
    --output "$METRICS_DIR" \
    2>&1 | tee "$METRICS_DIR/metrics_log.txt"

echo ""

# ---- Step 5: Launch Dashboard ----
if [ "$LAUNCH_DASHBOARD" = true ]; then
    echo "[Step 5] Launching dashboard from $METRICS_DIR/ ..."

    if [ -f "$DASHBOARD_FILE" ]; then
        cp -f "$DASHBOARD_FILE" "$METRICS_DIR/dashboard.py"
        echo "  Copied $DASHBOARD_FILE → $METRICS_DIR/"
    fi
    cp -f "$H5_FILE" "$METRICS_DIR/groundtruth.h5"
    if [ "$SKIP_BLACKBOX_SUB" = false ] && [ -f "$SUB_H5" ]; then
        cp -f "$SUB_H5" "$METRICS_DIR/substitute.h5"
    fi

    if [ "$USE_PINGGY" = true ]; then
        echo ""
        echo "  Starting Streamlit + Pinggy tunnel..."
        echo ""
 
        cd "$METRICS_DIR"
        streamlit run dashboard.py \
            --server.port "$DASHBOARD_PORT" \
            --server.headless true \
            --server.address localhost &
        STREAMLIT_PID=$!
        cd - > /dev/null
 
        sleep 3
 
        echo "  Streamlit running on port $DASHBOARD_PORT"
        echo ""
        echo "  Starting Pinggy tunnel..."
        echo "  A public URL will appear below — share it with your team."
        echo "  Press Ctrl+C to stop everything."
        echo ""
 
        trap "echo ''; echo 'Shutting down...'; kill $STREAMLIT_PID 2>/dev/null; exit 0" INT
 
        ssh -p 443 -R0:localhost:$DASHBOARD_PORT qr@free.pinggy.io
 
        kill $STREAMLIT_PID 2>/dev/null

	else
        echo ""
        echo "  To access from your local machine, run this in a separate terminal:"
        echo ""
        echo "    ssh -L $DASHBOARD_PORT:localhost:$DASHBOARD_PORT veena@pve.braingenix.org"
        echo ""
        echo "  Then open: http://localhost:$DASHBOARD_PORT"
        echo ""
        echo "  Or re-run with --pinggy for a public URL anyone can access."
        echo "  Press Ctrl+C to stop the dashboard."
        echo ""

        cd "$METRICS_DIR"
        streamlit run dashboard.py \
            --server.port "$DASHBOARD_PORT" \
            --server.headless true
    fi
else
    echo "[Step 5] Skipping dashboard."
fi

echo ""

echo "============================================="
echo " Pipeline complete!"
echo "============================================="
echo " Acquisition:  $OUTPUT_FOLDER"
echo " GT bundle:     $GT_DIR/"
echo " HDF5 (GT):     $H5_FILE"
if [ "$SKIP_BLACKBOX_SUB" = false ]; then
    echo " SUB bundle:    $SUB_DIR/"
    echo " HDF5 (SUB):    $SUB_H5"
fi
echo " Metrics/UI:    $METRICS_DIR/"
echo "============================================="
