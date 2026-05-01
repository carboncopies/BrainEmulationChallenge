#!../../../venv/bin/python

# This script was creaed by copying sub1_acquisition.py.
#
# This script creates a model that diverges slightly from the ground-truth.
# Features:
# - Structure is modified by effectively deleting neuron(s), by setting connections to 0.
#
# Note that the modified model is not saved. Each time this script is run
# we use the API to reload the GT model and we apply modifications to turn
# it into a divergent SUB.
# (Using the API to save the modified model may be useful if we need to
# rerun it frequently.)

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
Parser.add_argument("-runtime_ms", default=500, type=float, help="Runtime of functional experiment (ms)")
Parser.add_argument("-timeout_s", default=120.0, type=float, help="RunAndWait timeout (s)")
Parser.add_argument("-groundtruth", action='store_true', help="Run as ground-truth for comparative output")
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
### Modify Model to create divergent SUB      ###
### ========================================= ###

if not Args.groundtruth:

    # Pick the neurons to isolate and thereby effectively eliminate
    isolate = [ 9 ]

    # Fetch abstract connectome to identify full list of neurons
    try:
        response = MySim.GetAbstractConnectome(Sparse=True)
    except:
        vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')

    # Here, we'll make do with the 'Types' list to identify the neuron IDs
    if 'Types' not in response:
        print("Error: Missing 'Types' list.")
        exit(1)
    num_neurons = len(response['Types'])

    def connection_exists(pre:int, post:int, PrePostNumReceptors:list)->bool:
        for connection in PrePostNumReceptors:
            if connection[0]==pre and connection[1]==post and connection[2]>0:
                return True
        return False

    PrePostNumReceptors = response['PrePostNumReceptors']

    # New effective conductances are set to 0 for each pre-post neuron
    # pair specified. Specify in both directions to sever effective
    # connection regardless of direction of causal signal path.
    # We have to be careful to use information collected about the
    # connectome, because the modification API request fails if you
    # attempt to change connections that do not exist.
    PreSynList = []
    PostSynList = []
    all_neurons = [ idx for idx in range(num_neurons) ]
    for isolate_idx in isolate:
        for i in range(num_neurons):
            if connection_exists(isolate_idx, i, PrePostNumReceptors):
                PreSynList.append( isolate_idx )
                PostSynList.append( i )
            if connection_exists(i, isolate_idx, PrePostNumReceptors):
                PreSynList.append( i )
                PostSynList.append( isolate_idx)

    ConductanceList = [ 0.0 for i in range(len(PreSynList)) ]

    print('Isolating: '+str(isolate))

    for i in range(len(PreSynList)):
        print('(%d -> %d = %d)' % (PreSynList[i], PostSynList[i], ConductanceList[i]), end=" ")
    print('')

    try:
        setresponse = MySim.BatchSetPrePostStrength(PreSynList, PostSynList, ConductanceList)
        print("\nModified model into divergent submitted emulation by effectively removing neuron(s).")
    except:
        vbp.ErrorExit(DBdata, 'NES error: Failed to set connection strengths in simulation')
    if 'StatusCode' not in setresponse:
        print('Error: Batch setting connections failed, no status code')
        exit(1)
    if setresponse['StatusCode'] != 0:
        print('Error: Batch setting returned error code')
        exit(1)

    # Double-check if isolated neurons are now isolated
    try:
        response = MySim.GetAbstractConnectome(Sparse=True, NonZero=True)
    except:
        vbp.ErrorExit(DBdata, 'NES error: failed to receive model connectome')
    PrePostNumReceptors = response['PrePostNumReceptors']
    print('PrePostNumReceptors: '+str(PrePostNumReceptors))

### ========================================= ###
### Dynamic Data Acquisition                  ###
### ========================================= ###
runtime_ms = float(Args.runtime_ms)
print(f"\nRunning functional data acquisition for {runtime_ms:.1f} ms...\n")

t_soma_fire_ms = []

def SpikeInputNeuronsAt(InputID: str, t_ms: float):
    for n in XORInOutIdentifiers[InputID]:
        t_soma_fire_ms.append((t_ms, n))


t_test_ms = {
    'XOR_10': 100.0,
    'XOR_01': 200.0,
    'XOR_11': 300.0,
}
# The 0 0 case is not explicitly tested.
# Add 1 0 XOR test case.
SpikeInputNeuronsAt('InA', t_test_ms['XOR_10'])
# Add 0 1 XOR test case.
SpikeInputNeuronsAt('InB', t_test_ms['XOR_01'])
# Add 1 1 XOR test case.
SpikeInputNeuronsAt('InA', t_test_ms['XOR_11'])
SpikeInputNeuronsAt('InB', t_test_ms['XOR_11'])
print('Directed somatic firing: ' + str(t_soma_fire_ms))

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
    if Args.groundtruth:
        csv_path = f"{savefolder}/groundtruth-Vm.csv"
    else:
        csv_path = f"{savefolder}/sub2-Vm.csv"
    save_nes_recording_csv(recording_dict, csv_path)
    print("Saved recording CSV:", csv_path)
    vbp.AddOutputToDB(DBdata, "recording_csv", csv_path)
except Exception as e:
    vbp.ErrorToDB(DBdata, 'NES error: Failed to retrieve recorded activity '+str(e))

# Save spike times to a second CSV
MySim.SetLIFCPreciseSpikeTimes(True) # ??? Why is this here... these are not LIFC neurons
try:
    spike_resp = MySim.GetSpikeTimes()
    spike_dict = spike_resp.get("SpikeTimes", {})

    if Args.groundtruth:
        spike_csv_path = f"{savefolder}/groundtruth-spikes.csv"
    else:
        spike_csv_path = f"{savefolder}/sub2-spikes.csv"

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
