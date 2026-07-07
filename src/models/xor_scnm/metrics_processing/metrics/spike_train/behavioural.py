# metrics/spike_train/behavioural.py

import pandas as pd
from metrics.helper_functions import get_spike_cols, get_trials_by_pattern, load_metadata

def compute_confusion_matrix(data, pattern, label, trial_len, truth_table):
    """
    For a given pattern, loops over all 10 repetitions and checks
    whether E fired within the trial window. Classifies each trial
    as TP, FN, TN or FP based on the truth table.
    """
    trials = get_trials_by_pattern(data, pattern)
    TP, FN, TN, FP = 0, 0, 0, 0
    
    for t in trials:
        window = t[t["t_in_trial"] <= trial_len]
        fired  = window[label].sum() > 0
        want   = truth_table[f"XOR_{pattern}"]["expected_output"]
        have   = 1 if fired else 0

        if want == 1 and have == 1:   TP += 1
        elif want == 1 and have == 0: FN += 1
        elif want == 0 and have == 0: TN += 1
        else:                         FP += 1

    return TP, FN, TN, FP


def run(gt_data, sub_data, cfg, tmap, meta, truth_table):
    """
    Runs compute_confusion_matrix() for all 4 XOR patterns.
    patterns derived from tmap — not hardcoded.
    Returns a DataFrame with TP/FN/TN/FP and derived metrics per pattern.
    """  
    label      = get_spike_cols(cfg, gt_data, role="output")[0]
    trial_len  = int(meta["trial_len_ms"])
    patterns   = tmap["case"].unique().tolist()

    def all_patterns(data):
        rows = []
        for p in patterns:
            tp, fn, tn, fp = compute_confusion_matrix(
                data, p, label, trial_len, truth_table
            )
            den = tp + fn + tn + fp
            rows.append({
                "Pattern":     p,
                "TP": tp, "FN": fn, "TN": tn, "FP": fp,
                "Accuracy":    (tp + tn) / den if den else 0.0,
                "Sensitivity": tp / (tp + fn) if (tp + fn) else 0.0,
                "Specificity": tn / (tn + fp) if (tn + fp) else 0.0,
            })
        return pd.DataFrame(rows)

    gt_results  = all_patterns(gt_data)
    sub_results = all_patterns(sub_data)

    return gt_results, sub_results


def report(gt_results, sub_results):
    print("Behavioural Metrics")
    print("\nGround Truth:")
    print(gt_results.to_string(index=False))
    print("\nSubmission:")
    print(sub_results.to_string(index=False))