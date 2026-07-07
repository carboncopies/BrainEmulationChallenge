#metrics/information_theory/entropy

import numpy as np
from metrics.information_theory.it_utils import H
from metrics.helper_functions import get_spiking_neurons, get_trials_by_pattern

import pandas as pd
from metrics.helper_functions import get_spiking_neurons
from metrics.information_theory.it_utils import H

def run(gt_data, sub_data, cfg, tmap, meta, truth_table):
    patterns = tmap["case"].unique().tolist()
    neurons  = get_spiking_neurons(cfg, gt_data)
    gt_rows  = []
    sub_rows = []
    
    for neuron in neurons:
        gt_row  = {"neuron": neuron}
        sub_row = {"neuron": neuron}
        
        for p in patterns:
            # GT
            gt_pattern_rows      = gt_data[gt_data["case"] == p]
            gt_spikes            = gt_pattern_rows[f"{neuron}_spike"].tolist()
            gt_row[f"H_{p}"]     = H(gt_spikes)
            
            # SUB
            sub_pattern_rows     = sub_data[sub_data["case"] == p]
            sub_spikes           = sub_pattern_rows[f"{neuron}_spike"].tolist()
            sub_row[f"H_{p}"]    = H(sub_spikes)
        
        gt_rows.append(gt_row)
        sub_rows.append(sub_row)
    
    gt_table  = pd.DataFrame(gt_rows)
    sub_table = pd.DataFrame(sub_rows)
    
    return gt_table, sub_table


def report(gt_table, sub_table):
    print("Entropy per Neuron per Pattern")
    print("\nGround Truth:")
    print(gt_table.to_string(index=False))
    print("\nSubmission:")
    print(sub_table.to_string(index=False))
    print("\nDifference (GT - SUB):")
    diff = gt_table.copy()
    diff.iloc[:, 1:] = gt_table.iloc[:, 1:] - sub_table.iloc[:, 1:]
    print(diff.to_string(index=False))