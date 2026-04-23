#!../../../venv/bin/python

# This is a demonstration of how to inspect aspects of the models
# generated in a batch of samples by loading, inspecting, deleting simulations.

import argparse
import tqdm

import vbpcommon as vbp
from BrainGenix.BG_API import NES
from BrainGenix.Tools.BatchRun import BatchRun, LoadNetmorphConfiguration, ConnectClient

# Handle Arguments for Host, Port, etc
def get_Args():
    Parser = argparse.ArgumentParser(description="Batch inspection script")
    Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
    Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
    Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
    return Parser.parse_args()

# Status bar helper functions
def prepare_statusbar():
    StatusBar = tqdm.tqdm("Progress", total=1)
    StatusBar.leave = True
    StatusBar.bar_format = "{desc}{percentage:3.0f}%|{bar}| [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    StatusBar.colour = "green"
    return StatusBar

def update_statusbar(StatusBar, batchinfo:dict, numdone:int):
    grand_total = len(batchinfo)

    StatusBar.total = 100
    if grand_total <= 0:
        StatusBar.n = 100
    else:
        StatusBar.n = 100.0*numdone/grand_total
    StatusBar.refresh()

def close_statusbar(StatusBar, batchinfo:dict):
    update_statusbar(StatusBar, batchinfo, len(batchinfo))
    StatusBar.close()

# ===== Start of program steps
if __name__ == '__main__':

    Args = get_Args()

    # Load information about completed batch runs.
    batchrun = BatchRun(
        host=Args.Host,
        port=Args.Port,
        usehttps=Args.UseHTTPS)

    print('Number of completed samples: %d' % len(batchrun.batchinfo))

    statusbar = prepare_statusbar()
    num_neurons = []
    numdone = 0
    for sample in batchrun.batchinfo.values():
        saved_model_name = sample['modelname']

        # Create A New Simulation
        #print(" -- Creating Simulation")
        SimulationCfg = NES.Simulation.Configuration()
        SimulationCfg.Name = "Sample-"+saved_model_name
        SimulationCfg.Seed = 0
        try:
            MySim = batchrun.ClientInstance.CreateSimulation(SimulationCfg)
        except:
            print('NES error: Failed to create simulation')
            exit(1)

        # Load previously generated model
        try:
            MySim.ModelLoad(saved_model_name)
            #print("Loaded neuronal circuit model "+saved_model_name)
        except:
            print('NES error: model load failed')
            exit(1)

        # Get cell positions to verify model structure
        try:
            cell_positions = MySim.GetSomaPositions()
        except:
            print('NES error: failed to receive model cell positions')
            exit(1)

        soma_centers = cell_positions['SomaCenters']

        num_neurons.append(len(soma_centers))

        # Free memory
        try:
            MySim.DeleteResidentByID(Pause_s=0.1)
        except:
            print('NES error: unable to delete resident simulation')
            exit(1)

        numdone += 1
        update_statusbar(statusbar, batchrun.batchinfo, numdone)

    close_statusbar(statusbar, batchrun.batchinfo)

    print('Number of neurons in each sample:\n'+str(num_neurons))

    print('Done.')
    exit(0)
