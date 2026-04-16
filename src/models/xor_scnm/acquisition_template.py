#!../../../venv/bin/python

# This template was created by Kayla Stafford by simplifying
# xor_scnm_acquisition_direct.py.
#
# The template is focused on functional testing for the development
# of functional metrics. No structural data is generated.
#
# To use, please copy the template to your own script and adapt
# as needed for your experimental stimulation trials.

import vbpcommon as vbp # keep
import argparse
import math
import json
import os
from datetime import datetime
import BrainGenix.NES as NES
import csv
from pathlib import Path

scriptversion='0.1.0'

# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-modelname", default="xor_scnm-tuned", type=str, help="Name of neuronal circuit model previously saved")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Parser.add_argument("-runtime_ms", default=5000, type=float, help="Runtime of functional experiment (ms)")
Parser.add_argument("-timeout_s", default=120.0, type=float, help="RunAndWait timeout (s)")
Args = Parser.parse_args()

def save_nes_recording_csv(recording_dict: dict, out_csv: str) -> None:
    rec = recording_dict.get("Recording", recording_dict)

    t_ms = rec.get("t_ms", [])
    neurons = rec.get("neurons", {})

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # If empty, still write header so you know it ran
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ms", "neuron_id", "field", "value"])

        if not t_ms or not neurons:
            return

        # neurons is like {"0": {"Vm_mV":[...], "Iinj_nA":[...], ...}, "1": {...}, ...}
        for neuron_id, signals in neurons.items():
            if not isinstance(signals, dict):
                continue

            for field, series in signals.items():
                if series is None:
                    continue

                # Ensure we can index series
                try:
                    n = min(len(t_ms), len(series))
                except TypeError:
                    continue

                for i in range(n):
                    w.writerow([t_ms[i], neuron_id, field, series[i]])

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'acquisition',
    scriptversion,
    _initIN = {
        'modelname': Args.modelname,
    },
    _initOUT = {
    })

### ========================================= ###
### Retrieve Model                            ###
### ========================================= ###

# Find I/O IDs corresponding with the modelname
DBconnectome = vbp.GetMostRecentDBEntryOUT(DBdata, 'connectome', False, Args.modelname, exit_on_error=True)
if 'IOIDs' not in DBconnectome:
    vbp.ErrorExit(DBdata, 'Experiments database error: Missing IOIDs in most recent entry for modelname '+str(Args.modelname))
XORInOutIdentifiers = DBconnectome['IOIDs']
print('Loaded XOR I/O neuron identifiers.')
print("Model for DB lookup:", Args.modelname)
print("IOIDs keys:", XORInOutIdentifiers.keys())
print("InA IDs:", XORInOutIdentifiers.get("InA"))
print("InB IDs:", XORInOutIdentifiers.get("InB"))


# Create Client Configuration for Local Simulation
print(" -- Creating Client Configuration For Local Simulation")
ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"


# Create Client Instance (Necessary)
print(" -- Creating Client Instance")
try:
    ClientInstance = NES.Client.Client(ClientCfg)
    if not ClientInstance.IsReady():
        vbp.ErrorExit(DBdata, 'NES.Client error: not ready')
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES.Client error: '+str(e))


# Create a New Simulation
print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "Netmorph-"+Args.modelname
SimulationCfg.Seed = 0
try:
    MySim = ClientInstance.CreateSimulation(SimulationCfg)
except Exception as e:
        vbp.ErrorExit(DBdata, 'NES error: Failed to create simulation '+str(e))


# Prepare front-end output folder
savefolder = 'output/'+datetime.now().strftime('%Y%m%d%H%M%S.%f')+'-acquisition'
vbp.AddOutputToDB(DBdata, 'output_folder', savefolder)

# Load previously saved neuronal circuit model
try:
    MySim.ModelLoad(Args.modelname)
    print("Loaded neuronal circuit model "+Args.modelname)
    print('')
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES error: model load failed '+str(e))

### ========================================= ###
### Dynamic Data Acquisition                  ###
### ========================================= ###
runtime_ms = float(Args.runtime_ms)
print(f"\nRunning functional data acquisition for {runtime_ms:.1f} ms...\n")

t_soma_fire_ms = []

def SpikeInputNeuronsAt(InputID: str, t_ms: float):
    for n in XORInOutIdentifiers[InputID]:
        t_soma_fire_ms.append((t_ms, n))


t_test_ms_odd = {
    'XOR_10': 100.0,
    'XOR_01': 200.0,
    'XOR_11': 300.0,
}

t_test_ms_even = {
    'XOR_11' : 100.0,
    'XOR_01' : 200.0,
    'XOR_10' : 300.0,
}

cycle_duration = 400.0
repetitions = 10
trial_map = []

for r in range(repetitions):
    t = r*cycle_duration
    if(r%2 == 0):
        #reordering every even trial
        # Add 1 1 XOR test case.
        print(t_test_ms_even.keys())
        SpikeInputNeuronsAt('InA', t_test_ms_even['XOR_11'] + t)
        SpikeInputNeuronsAt('InB', t_test_ms_even['XOR_11'] + t)
        # Add 0 1 XOR test case.
        SpikeInputNeuronsAt('InB', t_test_ms_even['XOR_01'] + t)
        # Add 1 0 XOR test case.
        SpikeInputNeuronsAt('InA', t_test_ms_even['XOR_10'] + t)

        #Mapping for even trials
        trial_map.append({'rep': r, 'case': 'XOR_00', 't_start': 0.0   + t, 't_end': 100.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_11', 't_start': 100.0 + t, 't_end': 200.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_01', 't_start': 200.0 + t, 't_end': 300.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_10', 't_start': 300.0 + t, 't_end': 400.0 + t})
    else:
        # The 0 0 case is not explicitly tested.
        # Add 1 0 XOR test case.
        SpikeInputNeuronsAt('InA', t_test_ms_odd['XOR_10'] + t)
        # Add 0 1 XOR test case.
        SpikeInputNeuronsAt('InB', t_test_ms_odd['XOR_01'] + t)
        # Add 1 1 XOR test case.
        SpikeInputNeuronsAt('InA', t_test_ms_odd['XOR_11'] + t)
        SpikeInputNeuronsAt('InB', t_test_ms_odd['XOR_11'] + t)

        #Mapping for odd trials
        trial_map.append({'rep': r, 'case': 'XOR_00', 't_start': 0.0   + t, 't_end': 100.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_10', 't_start': 100.0 + t, 't_end': 200.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_01', 't_start': 200.0 + t, 't_end': 300.0 + t})
        trial_map.append({'rep': r, 'case': 'XOR_11', 't_start': 300.0 + t, 't_end': 400.0 + t})

Path(savefolder).mkdir(parents=True, exist_ok=True)
with open(f"{savefolder}/trial_map.json", "w") as f:
    json.dump(trial_map, f, indent=2)

# The 0 0 case is not explicitly tested.
# Add 1 0 XOR test case.
#SpikeInputNeuronsAt('InA', t_test_ms['XOR_10'])
# Add 0 1 XOR test case.
#SpikeInputNeuronsAt('InB', t_test_ms['XOR_01'])
# Add 1 1 XOR test case.
#SpikeInputNeuronsAt('InA', t_test_ms['XOR_11'])
#SpikeInputNeuronsAt('InB', t_test_ms['XOR_11'])
#print('Directed somatic firing: ' + str(t_soma_fire_ms))

try:
    MySim.SetSpecificAPTimes(TimeNeuronPairs=t_soma_fire_ms)
except:
    vbp.ErrorExit(DBdata, 'NES error: Failed to set specific spike times')

# ---- Recording ----
t_max_ms=-1 # record for the entire runtime
vbp.AddInputToDB(DBdata, 'Ephys', {
    'runtime_ms': runtime_ms,
    't_soma_fire_ms': t_soma_fire_ms,
    't_record_max_ms': t_max_ms,
})

try:
    MySim.RecordAll(_MaxRecordTime_ms=t_max_ms)
except Exception as e:
    vbp.ErrorToDB(DBdata, 'NES error: Failed to set RecordAll '+str(e))

# ---- Run ----
try:
    MySim.RunAndWait(Runtime_ms=runtime_ms, timeout_s=float(Args.timeout_s))
except Exception as e:
    vbp.ErrorToDB(DBdata, "NES error: RunAndWait failed: " + str(e))

# Collect God-mode recording of neural activity
recording_dict = None
try:
    recording_dict = MySim.GetRecording()
    csv_path = f"{savefolder}/groundtruth-Vm.csv"
    save_nes_recording_csv(recording_dict, csv_path)
    print("Saved recording CSV:", csv_path)
    vbp.AddOutputToDB(DBdata, "recording_csv", csv_path)
except Exception as e:
    vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve recorded activity '+str(e))

# Save spike times to a second CSV
MySim.SetLIFCPreciseSpikeTimes(True)
try:
    spike_resp = MySim.GetSpikeTimes()
    spike_dict = spike_resp.get("SpikeTimes", {})

    spike_csv_path = f"{savefolder}/groundtruth-spikes.csv"

    with open(spike_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["neuron_id", "spike_time_ms"])

        for neuron_id, data in spike_dict.items():
            for t in data.get("tSpike_ms", []):
                writer.writerow([int(neuron_id), t])

    print("Saved spike CSV:", spike_csv_path)
    vbp.AddOutputToDB(DBdata, "spike_csv", spike_csv_path)

except Exception as e:
    vbp.ErrorToDB(DBdata, "NES error: Failed to retrieve spike times " + str(e))

# Update experiments database file with results
vbp.UpdateExpsDB(DBdata)
