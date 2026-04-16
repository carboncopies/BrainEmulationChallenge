

import pandas as pd
import h5py
import json
import os
from pathlib import Path

class build_h5:

    def __init__(self,vm_csv,spikes_csv,net_con,t_map ,h5_file_path):
        self.vm_csv = vm_csv
        self.spikes_csv = spikes_csv
        self.net_con = net_con
        self.h5_file_path = h5_file_path
        self.t_map = t_map

        os.makedirs(os.path.dirname(self.h5_file_path), exist_ok=True)

    def process_network_config(self):

        try:
            with open(self.net_con,'r') as f:
                data = json.load(f)

            neurons = data["neurons"]
            df = pd.DataFrame.from_dict(neurons, orient='index')
            df.index.name = 'neuron_id'
            df.index = df.index.astype(int)   # consistent with CSVs
            df = df.reset_index()  

 
            print("Processing Network Config done...")
            return df
        
        except Exception as e:
            print(f"Error! Conversion failed due to {e}!")

    def process_trial_map(self):

        try:
            with open(self.t_map,'r') as f:
                data = json.load(f)

            df = pd.DataFrame(data)
            df['case'] = df['case'].str.replace('XOR_', '', regex=False)
            df['input_ch1'] = df['case'].isin(['10', '11']).astype(int)
            df['input_ch2'] = df['case'].isin(['01', '11']).astype(int)
            df['trial_id'] = df.index 
            print("Processing trial map done...")
            return df

        except Exception as e:
             print(f"Error! Conversion failed due to {e}!")


    def process_vm_csv(self):
        try:
            df = pd.read_csv(self.vm_csv)
            df = df[df["field"] == "Vm_mV"]
            df_pivoted = df.pivot(index = "t_ms", columns="neuron_id", values = "value")
            df_pivoted.columns = [f"neuron_{col}_vm" for col in df_pivoted.columns]

            print("Processing Vm csv done...")
            return df_pivoted
        
        except FileNotFoundError:
            print("Error! The file does not exist, please check the file directory!")
        except Exception as e:
            print(f"Error! Conversion failed due to {e}!")
            

    def build_spike_columns(self,vm_df):
        
        df = pd.read_csv(self.spikes_csv)
        neuron_cols = [f'neuron_{i}_spike' for i in range(35)]
        df["neuron_id"] = df["neuron_id"].astype(int)

        for col in neuron_cols:
            vm_df[col] = 0 

        for _, row in df.iterrows():
            neuron_id = int(row["neuron_id"])
            spike_time_ms  = row["spike_time_ms"]
            col_name = f"neuron_{neuron_id}_spike"
            idx_pos = vm_df.index.get_indexer([spike_time_ms], method="nearest")[0]
            nearest_t = vm_df.index[idx_pos]
            vm_df.loc[nearest_t, col_name] = 1

        
        return vm_df
    
    def rename_columns(self, vm_df, cfg_df):

        rename_dict = {}
        for _, row in cfg_df.iterrows():
            neuron_id = int(row["neuron_id"])
            label     = row["label"]

            old_vm    = f"neuron_{neuron_id}_vm"
            old_spike = f"neuron_{neuron_id}_spike"
            new_vm    = f"{label}_vm"
            new_spike = f"{label}_spike"

            rename_dict[old_vm]    = new_vm
            rename_dict[old_spike] = new_spike

        vm_df = vm_df.rename(columns=rename_dict)
        print("Renaming columns done...")
        return vm_df
    

    def add_trial_context(self,vm_df, trial_df):       

        vm_df = vm_df.reset_index()
        max_t = trial_df["t_end"].max()
        vm_df = vm_df[vm_df["t_ms"] < max_t].copy()
        bins = trial_df["t_start"].tolist() + [trial_df["t_end"].iloc[-1]]
        labels = trial_df["trial_id"].tolist()
        vm_df["trial_id"] = pd.cut(vm_df["t_ms"], bins=bins, labels=labels, right=False)
        vm_df["trial_id"] = vm_df["trial_id"].astype(int)
        vm_df = vm_df.merge(trial_df, on="trial_id", how="left")
        vm_df["t_in_trial"] = vm_df["t_ms"] - vm_df["t_start"]
        vm_df = vm_df.drop(columns=["t_start", "t_end"])
        context_cols = ["t_ms", "trial_id", "t_in_trial", "rep", "case", "input_ch1", "input_ch2"]
        neuron_cols = [c for c in vm_df.columns if c not in context_cols]
        vm_df = vm_df[context_cols + neuron_cols]
        
        print("Adding trial context done...")
        return vm_df
    
    def build_spikes_raw(self,cfg_df,trial_df):
        
        spikes_df = pd.read_csv(self.spikes_csv)
        spikes_df["neuron_id"] = spikes_df["neuron_id"].astype(int)
        spikes_df = spikes_df.merge(cfg_df, on = "neuron_id", how = "left")
        bins = trial_df["t_start"].tolist() + [trial_df["t_end"].iloc[-1]]
        labels = trial_df["trial_id"].tolist()
        spikes_df["trial_id"] = pd.cut(spikes_df["spike_time_ms"], bins=bins, labels=labels, right=False)
        spikes_df = spikes_df.dropna(subset=["trial_id"])
        spikes_df["trial_id"] = spikes_df["trial_id"].astype(int)
        spikes_df = spikes_df.merge(trial_df, on="trial_id", how="left")
        spikes_df["t_in_trial"] = spikes_df["spike_time_ms"] - spikes_df["t_start"]
        spikes_df = spikes_df.drop(columns=["t_start"])
        spikes_df["trial_id"] = spikes_df["trial_id"].astype(int)
        spikes_df = spikes_df.rename(columns={'case': 'pattern'})

        return spikes_df
    
    def compute_metadata(self, data_df, cfg_df, trial_df, spikes_df):
            
        metadata = {
        "fs_hz": 1000.0 / (data_df["t_ms"].iloc[1] - data_df["t_ms"].iloc[0]),
        "t_total_ms":   trial_df["t_end"].iloc[-1],
        "n_trials":     len(trial_df),
        "trial_len_ms": trial_df["t_end"].iloc[0] - trial_df["t_start"].iloc[0],
        "n_neurons_total":    len(cfg_df),
        "n_neurons_spiking":  spikes_df["neuron_id"].nunique(),
        }

        return metadata
    
    def build(self):

        if os.path.exists(self.h5_file_path):
            print(f"HDF5 file already exists: {self.h5_file_path}")
            print("Delete the file manually if you want to rebuild.")
            return
        
        cfg_df    = self.process_network_config()
        trial_df  = self.process_trial_map()
        vm_df     = self.process_vm_csv()
        vm_df     = self.build_spike_columns(vm_df)
        vm_df     = self.rename_columns(vm_df, cfg_df)
        data_df   = self.add_trial_context(vm_df, trial_df)
        spikes_df = self.build_spikes_raw(cfg_df, trial_df)
        metadata  = self.compute_metadata(data_df, cfg_df, trial_df, spikes_df)


        cfg_df.to_hdf(self.h5_file_path,   key="/network_config", mode="w", format="table")
        trial_df.to_hdf(self.h5_file_path, key="/trial_map",      mode="a", format="table")
        data_df.to_hdf(self.h5_file_path,  key="/data",           mode="a", format="table")
        spikes_df.to_hdf(self.h5_file_path,key="/spikes_raw",     mode="a", format="table")


        with h5py.File(self.h5_file_path, "a") as f:
            grp = f.require_group("metadata")
            for key, value in metadata.items():
                grp.attrs[key] = value

        print("HDF5 build complete! Yayayayaya!!")
        

if __name__ == "__main__":
    current_dir   = os.getcwd()
    input_dir = os.path.join(current_dir, "output")
    acq_folders = sorted(
        [f for f in os.listdir(output_dir) if f.endswith('-acquisition')],
        reverse=True
    )
    if not acq_folders:
        print("ERROR: No acquisition folders found in output/")
        exit(1)
    folder_dir    = os.path.join(current_dir, "output", acq_folders[0])
    print(f"Using: {folder_dir}")
    output_folder = os.path.join(current_dir, "output", "GT_h5")

    converter = build_h5(
        vm_csv       = os.path.join(folder_dir, "groundtruth-Vm.csv"),
        spikes_csv   = os.path.join(folder_dir, "groundtruth-spikes.csv"),
        net_con      = os.path.join(folder_dir, "network_config.json"),
        t_map        = os.path.join(folder_dir, "trial_map.json"),
        h5_file_path = os.path.join(output_folder, "groundtruth.h5")
    )

    converter.build()

# =============================================================================
# DATA TRANSFORMATION PIPELINE
# =============================================================================
#
# RAW FILES                   METHODS                        OUTPUT
# --------------------------------------------------------------------------
#
# network_config.json
#   {                         process_network_config()
#     "neurons": {                                           cfg_df
#       "27": {label,  ----> flat DataFrame, 35 rows  ----> neuron_id | label | role | input_channel
#              role},         index cast to int              27        | PyrIn_A | input | 1
#       ...                                                  4         | E       | output | null
#     }                                                      0         | neuron_0 | extended_network | null
#   }                                                        ...
#
# --------------------------------------------------------------------------
#
# trial_map.json
#   [{rep, case,              process_trial_map()
#     t_start, t_end},  ----> strip XOR_ prefix        ----> trial_df
#    ...]                     derive input_ch1/ch2           trial_id | rep | case | t_start | t_end | input_ch1 | input_ch2
#                             add trial_id = index           0        | 0   | 00   | 0.0     | 100.0 | 0         | 0
#                                                            1        | 0   | 11   | 100.0   | 200.0 | 1         | 1
#                                                            ...40 rows
#
# --------------------------------------------------------------------------
#
# groundtruth-Vm.csv
#   t_ms | neuron_id            process_vm_csv()
#        | field    |  ------> filter field == Vm_mV    ----> vm_df (t_ms as index)
#        | value               pivot: neuron_id -> cols       t_ms | neuron_0_vm | ... | neuron_34_vm
#                              rename: neuron_{id}_vm          0.0 |   -60.0     | ... |   -60.0
#                              5000 rows (incl. cooldown)      1.0 |   -60.0     | ... |   -60.0
#                                                              ...
#
#                              build_spike_columns(vm_df)
# groundtruth-spikes.csv                                  ----> vm_df (t_ms as index)
#   neuron_id |  -----------> init 35 spike cols = 0          t_ms | neuron_0_vm | ... | neuron_0_spike | ... | neuron_27_spike
#   spike_time_ms             snap spike_time_ms to            0.0 |   -60.0     | ... |       0        | ... |       0
#                             nearest t_ms in vm_df           100.0 |   -60.0     | ... |       0        | ... |       1
#                             set that row = 1                 ...
#                             non-spiking neurons stay 0
#
#                              rename_columns(vm_df, cfg_df)
#                 cfg_df ---> build rename dict              ----> vm_df (t_ms as index)
#                             neuron_27_vm  -> PyrIn_A_vm         t_ms | neuron_0_vm | E_vm | PyrIn_A_vm | ... | E_spike | PyrIn_A_spike | ...
#                             neuron_27_spike -> PyrIn_A_spike     0.0 |   -60.0     |-60.0 |  -60.0     | ... |    0    |       0       | ...
#                             neuron_0_vm   -> neuron_0_vm        ...
#                             (extended network unchanged)
#
#                              add_trial_context(vm_df, trial_df)
#               trial_df --> reset index (t_ms -> col)     ----> data_df
#                            clip t_ms >= 4000.0 (cooldown)      t_ms | trial_id | t_in_trial | rep | case | input_ch1 | input_ch2 | [70 neuron cols]
#                            pd.cut() -> assigns trial_id          0.0 |    0     |    0.0     |  0  |  00  |     0     |     0     | -60.0 ... 0 ...
#                            merge with trial_df                  100.0 |    1     |    0.0     |  0  |  11  |     1     |     1     | -60.0 ... 1 ...
#                            t_in_trial = t_ms - t_start          ...4000 rows, 77 cols
#                            reorder: context cols first
#
# --------------------------------------------------------------------------
#
# groundtruth-spikes.csv
#   neuron_id |               build_spikes_raw(cfg_df, trial_df)
#   spike_time_ms  -------> merge with cfg_df -> add label  ----> spikes_df
#                            pd.cut() -> assign trial_id         neuron_id | label | spike_time_ms | trial_id | t_in_trial | rep | pattern
#                 cfg_df     drop cooldown spikes (NaN)           13 | Int_B   | 309.0 |    3     |    9.0     |  0  |  10
#               trial_df --> merge with trial_df                  27 | PyrIn_A | 100.0 |    1     |    0.0     |  0  |  11
#                            t_in_trial = spike_time_ms           ...one row per spike event, float precision preserved
#                                         - t_start
#
# --------------------------------------------------------------------------
#
# data_df + cfg_df            compute_metadata()
# trial_df + spikes_df  ----> harvest scalar facts          ----> metadata dict
#                             fs_hz from t_ms spacing             fs_hz          = 1000.0
#                             t_total from trial_df               t_total_ms     = 4000.0
#                             counts from each df                 n_trials       = 40
#                                                                 trial_len_ms   = 100.0
#                                                                 n_neurons_total   = 35
#                                                                 n_neurons_spiking = 8
#
# --------------------------------------------------------------------------
#
# ALL OUTPUTS                  build()
#                 ----------> orchestrates all steps above  ----> groundtruth.h5
#                             writes in correct order             |
#                             cfg_df    mode="w" (first)          +-- /network_config  (35 rows)
#                             trial_df  mode="a"                  +-- /trial_map       (40 rows)
#                             data_df   mode="a"                  +-- /data            (4000 rows, 77 cols)
#                             spikes_df mode="a"                  +-- /spikes_raw      (one row per spike)
#                             metadata  via h5py attrs            +-- /metadata        (scalar attrs)
#
# --------------------------------------------------------------------------
#
# NOTES:
#   - trial_map.json and network_config.json are shared between GT and SUB runs
#   - only Vm.csv and spikes.csv differ between GT and SUB
#   - has_spikes is NOT stored in config, derived at runtime from spikes.csv
#   - extended_network neurons have spike cols = 0 (not NaN)
#   - cooldown period (4000-5000ms) is clipped in add_trial_context()
#   - spike times are snapped to nearest ms in build_spike_columns()
#     but kept as float in build_spikes_raw() for precision-sensitive metrics
#
# =============================================================================




    

