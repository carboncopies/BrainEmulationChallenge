# pipeline.py

from pathlib import Path
import pandas as pd
import json

from metrics.helper_functions import load_metadata
from metrics import METRICS

def load_all(gt_h5_path, sub_h5_path, truth_table_path):
    
    gt_data    = pd.read_hdf(gt_h5_path,  "/data")
    gt_spikes  = pd.read_hdf(gt_h5_path,  "/spikes_raw")
    sub_data   = pd.read_hdf(sub_h5_path, "/data")
    sub_spikes = pd.read_hdf(sub_h5_path, "/spikes_raw")
    cfg        = pd.read_hdf(gt_h5_path,  "/network_config")
    tmap       = pd.read_hdf(gt_h5_path,  "/trial_map")
    meta       = load_metadata(gt_h5_path)
    
    with open(truth_table_path, "r") as f:
        net_config  = json.load(f)
    truth_table = net_config["truth_table"]
    
    return gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, truth_table, meta


if __name__ == "__main__":
    project_root     = Path(__file__).resolve().parent
    gt_h5            = project_root / "h5_output" / "groundtruth.h5"
    sub_h5           = project_root / "h5_output" / "groundtruth.h5" #Change this, when there is actual sub_data
    truth_table_path = project_root / "network_config.json"
    
    gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, truth_table, meta = load_all(
        gt_h5, sub_h5, truth_table_path
    )

    print(gt_data.shape)     
    print(gt_spikes.shape)    
    print(cfg.shape)          
    print(tmap.shape)         
    print(truth_table)        

    for metric in METRICS:
        print(f"Running: {metric['name']}")
        print('='*40)
        try:
            results = metric["run"](
                gt_data, sub_data, cfg, tmap, meta, truth_table
            )
            if metric["report"] is not None:
                metric["report"](*results)
        except Exception as e:
            print(f"[ERROR] {metric['name']} failed: {e}")