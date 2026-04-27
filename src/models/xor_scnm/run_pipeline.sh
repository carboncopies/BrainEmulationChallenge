#!/bin/bash
 
# =============================================================================
# run_pipeline.sh
# Automates: acquisition → build HDF5 → run metrics
#
# Usage:
#   ./run_pipeline.sh --full-rebuild --pinggy           # full pipeline
#   ./run_pipeline.sh --skip-acquisition        # reuse existing raw data
#   ./run_pipeline.sh --output-folder output/20260412121829.917106-acquisition
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
OUTPUT_FOLDER=""
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
        --output-folder)     OUTPUT_FOLDER="$2";     shift 2;;
	-d|--dashboard)      DASHBOARD_FILE="$2";    shift 2;;
	--no-dashboard)      LAUNCH_DASHBOARD=false; shift;;
	--pinggy)            USE_PINGGY=true;        shift;;
	--port)              DASHBOARD_PORT="$2";    shift 2;;
        -h|--help)
            echo "Usage: ./run_pipeline.sh [options]"
            echo "  -n, --network-config PATH Path to network_config.json"
            echo "  --skip-acquisition        Skip step 1"
            echo "  --full-rebuild            Build the full pipeline"
            echo "  --output-folder PATH      Path to existing output data folder"
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

# ---- Step 5: Launch Dashboard ----
if [ "$LAUNCH_DASHBOARD" = true ]; then
    echo "[Step 5/5] Launching dashboard..."

    # Copy dashboard.py to the metrics folder if not already there

    if [ -f "$DASHBOARD_FILE" ] && [ ! -f "$METRICS_FOLDER/dashboard.py" ]; then
        cp "$DASHBOARD_FILE" "$METRICS_FOLDER/dashboard.py"
        echo "  Copied $DASHBOARD_FILE → $METRICS_FOLDER/"
    fi

    if [ "$USE_PINGGY" = true ]; then
        # ---- Pinggy tunnel: creates a public URL ----
        echo ""
        echo "  Starting Streamlit + Pinggy tunnel..."
        echo ""
 
        # Start Streamlit in background
        cd "$METRICS_FOLDER"
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

        cd "$METRICS_FOLDER"
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
echo " output data:    $OUTPUT_FOLDER"
echo " HDF5:        $H5_FILE"
echo " Metrics:     $METRICS_FOLDER"
echo "============================================="
