#!/bin/bash
 
# =============================================================================
# run_pipeline.sh
# Automates: acquisition → build HDF5 → run metrics
#
# Usage:
#   ./run_pipeline.sh --full-rebuild --pinggy           # full pipeline
#   ./run_pipeline.sh --skip-acquisition        # reuse existing raw data
#   ./run_pipeline.sh --gt-folder output/*-acquisition --sub-folder output/*-acquisition
#   ./run_pipeline.sh --no-dashboard            # skip dashboard launch
#   ./run_pipeline.sh --pinggy                  # expose dashboard via pinggy 
# =============================================================================
#
# set -e  # Exit on any error
#
# ---- Defaults ----

mkdir -p output

NETWORK_CONFIG="network_config.json"
SKIP_ACQUISITION=false
FULL_REBUILD=false
GT_FOLDER=""
SUB_FOLDER=""
DASHBOARD_FILE="dashboard.py"
LAUNCH_DASHBOARD=true
USE_PINGGY=false
DASHBOARD_PORT=8501

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--network-config) NETWORK_CONFIG="$2";    shift 2;;
        --skip-acquisition)  SKIP_ACQUISITION=false; shift;;
        --full-rebuild)      FULL_REBUILD=true;      shift;;
        --gt-folder)         GT_FOLDER="$2";         shift 2;;
        --sub-folder)        SUB_FOLDER="$2";         shift 2;;
	-d|--dashboard)      DASHBOARD_FILE="$2";    shift 2;;
	--no-dashboard)      LAUNCH_DASHBOARD=false; shift;;
	--pinggy)            USE_PINGGY=true;        shift;;
	--port)              DASHBOARD_PORT="$2";    shift 2;;
        -h|--help)
            echo "Usage: ./run_pipeline.sh [options]"
            echo "  -n, --network-config PATH Path to network_config.json"
            echo "  --skip-acquisition        Skip step 1"
            echo "  --full-rebuild            Build the full pipeline"
	    echo "  --gt-folder PATH          Existing GT acquisition folder"
	    echo "  --sub-folder PATH         Existing SUB acquisition folder"
	    echo "  -d, --dashboard PATH      Path to dashboard.py"
	    echo "  --no-dashboard            Skip launching the Streamlit dashboard"
	    echo "  --pinggy                  Expose dashboard via Pinggy tunnel"
	    echo "  --port PORT               Dashboard port (default: 8501)"
            exit 0;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

echo "============================================="
echo " Brain Emulation Challenge Pipeline"
echo "============================================="
echo ""

# ---- Helper: find latest acquisition folder containing a sentinel file----

find_latest_with() {
    local sentinel="$1"
    for d in $(ls -dt output/*-acquisition 2>/dev/null); do
        if [ -f "$d/$sentinel" ]; then
            echo "$d"
            return 0
        fi
    done
    return 1
}

# ---- Step 1: Acquisition ----

if [ "$SKIP_ACQUISITION" = false ]; then
    if [ "$FULL_REBUILD" = true ]; then
        echo "[Step 1/4] Full rebuild: growing network + tuning + acquisition..."
        ./Run_flat.sh -x r
    else
        echo "[Step 1/4] Running acquisition only (model already built)..."
        ./Run_flat.sh -x a
    fi
 
    GT_FOLDER=$(find_latest_with "groundtruth-spikes.csv")
    SUB_FOLDER=$(find_latest_with "sub-spikes.csv")
    echo "  GT  folder: $GT_FOLDER"
    echo "  SUB folder: $SUB_FOLDER"
else
    if [ -z "$GT_FOLDER" ]; then
        GT_FOLDER=$(find_latest_with "groundtruth-spikes.csv")
    fi
    if [ -z "$SUB_FOLDER" ]; then
        SUB_FOLDER=$(find_latest_with "sub-spikes.csv")
    fi
    echo "[Step 1/4] Skipping acquisition."
    echo "  Using GT  folder: $GT_FOLDER"
    echo "  Using SUB folder: $SUB_FOLDER"
fi
 
if [ -z "$GT_FOLDER" ]; then
    echo "ERROR: No GT acquisition folder found (need groundtruth-spikes.csv in output/*-acquisition)"
    exit 1
fi
if [ -z "$SUB_FOLDER" ]; then
    echo "ERROR: No SUB acquisition folder found (need sub-spikes.csv in output/*-acquisition)"
    exit 1
fi
 
# Verify required files exist in each folder
for f in groundtruth-Vm.csv groundtruth-spikes.csv trial_map.json; do
    if [ ! -f "$GT_FOLDER/$f" ]; then
        echo "ERROR: Missing $f in $GT_FOLDER"
        exit 1
    fi
done
for f in sub-Vm.csv sub-spikes.csv trial_map.json; do
    if [ ! -f "$SUB_FOLDER/$f" ]; then
        echo "ERROR: Missing $f in $SUB_FOLDER"
        exit 1
    fi
done
echo "  Output files verified in both folders."
echo ""

# ---- Step 2: Copy network config into raw folder ----

echo "[Step 2/4] Adding network_config.json..."

if [ ! -f "$GT_FOLDER/network_config.json" ]; then
    if [ -f "$NETWORK_CONFIG" ]; then
        cp "$NETWORK_CONFIG" "$GT_FOLDER/network_config.json"
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

GT_H5_FOLDER="output/GT_h5"
SUB_H5_FOLDER="output/SUB_h5"
mkdir -p "$GT_H5_FOLDER" "$SUB_H5_FOLDER"

GT_H5="$GT_H5_FOLDER/groundtruth.h5"
SUB_H5="$SUB_H5_FOLDER/sub.h5"

if [ -f "$GT_H5" ];  then echo "  Removing old $GT_H5";  rm "$GT_H5";  fi
if [ -f "$SUB_H5" ]; then echo "  Removing old $SUB_H5"; rm "$SUB_H5"; fi
 
# SUB reuses GT's network_config.json (same network, modified neuron params)
NET_CONFIG_PATH="$GT_FOLDER/network_config.json"
 
echo "  Building GT H5..."
python -c "
import sys
sys.path.insert(0, '.')
from build_h5 import build_h5
 
converter = build_h5(
    vm_csv='$GT_FOLDER/groundtruth-Vm.csv',
    spikes_csv='$GT_FOLDER/groundtruth-spikes.csv',
    net_con='$NET_CONFIG_PATH',
    t_map='$GT_FOLDER/trial_map.json',
    h5_file_path='$GT_H5',
)
converter.build()
"
 
echo "  Building SUB H5..."
python -c "
import sys
sys.path.insert(0, '.')
from build_h5 import build_h5
 
converter = build_h5(
    vm_csv='$SUB_FOLDER/sub-Vm.csv',
    spikes_csv='$SUB_FOLDER/sub-spikes.csv',
    net_con='$NET_CONFIG_PATH',
    t_map='$SUB_FOLDER/trial_map.json',
    h5_file_path='$SUB_H5',
)
converter.build()
"
 
echo "  GT  → $GT_H5"
echo "  SUB → $SUB_H5"
echo ""

# ---- Step 4: Run metrics ----

echo "[Step 4/4] Running in-domain metrics..."

export MPLBACKEND=Agg

METRICS_FOLDER="output/metrics"
mkdir -p "$METRICS_FOLDER"

python in_domain_metrics.py \
    --gt  "$GT_H5" \
    --sub "$SUB_H5" \
    --output "$METRICS_FOLDER" \
    2>&1 | tee "$METRICS_FOLDER/metrics_log.txt"
 
echo ""

# ---- Step 5: Launch Dashboard ----

if [ "$LAUNCH_DASHBOARD" = true ]; then
    echo "[Step 5/5] Launching dashboard..."

    if [! -f "$DASHBOARD_FILE" ]; then
        echo "ERROR: Dashboard file not found at $DASHBOARD_FILE"
	exit 1
    fi

    if [ "$USE_PINGGY" = true ]; then
        # ---- Pinggy tunnel: creates a public URL ----
        echo ""
        echo "  Starting Streamlit + Pinggy tunnel..."
        echo ""
 
        # Start Streamlit in background
        streamlit run dashboard.py \
            --server.port "$DASHBOARD_PORT" \
            --server.headless true \
            --server.address localhost &
        STREAMLIT_PID=$!
        cd - > /dev/null
 
        # Wait for Streamlit to start
        sleep 3
 
        echo "  Streamlit running on port $DASHBOARD_PORT"
        echo ""
        echo "  Starting Pinggy tunnel..."
        echo "  A public URL will appear below — share it with your team."
        echo "  Press Ctrl+C to stop everything."
        echo ""
 
        # Clean up both processes on Ctrl+C
        trap "echo ''; echo 'Shutting down...'; kill $STREAMLIT_PID 2>/dev/null; exit 0" INT
 
        # Start Pinggy tunnel (press Enter if asked for password)
        ssh -p 443 -R0:localhost:$DASHBOARD_PORT qr@free.pinggy.io
 
        # Clean up if Pinggy exits on its own
        kill $STREAMLIT_PID 2>/dev/null

	else
        # ---- Local only ----
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

        streamlit run dashboard.py \
            --server.port "$DASHBOARD_PORT" \
            --server.headless true
    fi
else
    echo "[Step 5/5] Skipping dashboard."
fi

echo ""

echo "============================================="
echo " Pipeline complete!"
echo "============================================="
echo " GT folder:   $GT_FOLDER"
echo " SUB folder:  $SUB_FOLDER"
echo " GT H5:       $GT_H5"
echo " SUB H5:      $SUB_H5"
echo " Metrics:     $METRICS_FOLDER"
echo "============================================="
