#Helper Functions

import h5py

def get_neurons(cfg, role=None, input_channel=None):
    #     role="output"                 - ["E"]
    #     role="input"                  - ["PyrIn_A","PyrIn_B1","PyrIn_B2"]
    #     role=["input","interneuron",
    #           "intermediate","output"]- all 8 active neurons
    #     role="all"                    - all 35 labels
    #     input_channel=2               - ["PyrIn_B1","PyrIn_B2"]
    result = cfg
    if role!= None and role!= "all":
        if isinstance(role, list):
            result = result[result["role"].isin(role)]
        else:
            result = result[result["role"] == role]

    if input_channel!= None:
        result = result[result["input_channel"] == input_channel]

    return result["label"].tolist()
        
def get_spiking_neurons(cfg, data, label = None):
    #     checks _spike cols in data at runtime
    #     returns labels where spike col sum > 0
    spiking = []

    if label == None:
        for _ in cfg["label"]:
            if data[f"{_}_spike"].sum()>0:
                spiking.append(_)
    else:
        if data[label].sum() > 0:
            spiking.append(label)
       
    return spiking
        
def get_spike_cols(cfg, data, role =None):
   #     calls get_spiking_neurons()
   #     returns ["{label}_spike", ...] for spiking neurons
   columns = []
   
   if role == None:
        for label in get_spiking_neurons(cfg,data):
            columns.append(f"{label}_spike")
    
   else:
        for label in get_neurons(cfg, role=role):
            columns.append(f"{label}_spike")
    
   return columns

def get_vm_cols(cfg, scope="all"):
    #     scope="all"    - all 35 _vm column names
    #     scope="active" - 8 active neurons _vm column names
    roles = []
    if(scope == "active"):
        for _,row in cfg.iterrows():
            if row["role"] != "extended_network":
                roles.append(f"{row['label']}_vm")
    else:
        for _,row in cfg.iterrows():
            roles.append(f"{row['label']}_vm")
    return roles

def get_trial(data, trial_id):
    return data[data["trial_id"] == trial_id]

def get_trials_by_pattern(data, pattern):
    #     returns list of DataFrames where case == pattern
    #     10 DataFrames per pattern (one per rep)
    result = []
    unique = data["rep"].unique()
    for u in unique:
        filtered = data[(data["case"] == pattern) & (data["rep"] == u)]
        result.append(filtered)

    return result

def load_metadata(h5_path):
    #     reads /metadata attrs via h5py
    #     returns plain dict:
    #       {"fs_hz": 1000.0, "t_total_ms": 4000.0, "n_trials": 40,
    #        "trial_len_ms": 100.0, "n_neurons_total": 35, "n_neurons_spiking": 8}
    with h5py.File(h5_path,"r") as f:
        metadata = dict(f["/metadata"].attrs)
    
    return metadata