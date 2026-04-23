#!../../../venv/bin/python

# This is a demonstration of how to inspect aspects of the models
# generated in a batch of samples by loading, inspecting, deleting simulations.

import argparse

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


# ===== Start of program steps
if __name__ == '__main__':

    Args = get_Args()

    # Load information about completed batch runs.
    batchrun = BatchRun(
        host=Args.Host,
        port=Args.Port,
        usehttps=Args.UseHTTPS,
        numsamples=None,
        extraprepfunc=None,
        extraprepdata=None)

    print('Number of completed samples: %d' % len(batchrun.batchinfo))

    for sample in batchrun.batchinfo.values():
        saved_model_name = sample['modelname']

        # Create A New Simulation
        print(" -- Creating Simulation")
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
            print("Loaded neuronal circuit model "+saved_model_name)
        except:
            print('NES error: model load failed')
            exit(1)

        # Get cell positions to verify model structure
        try:
            cell_positions = MySim.GetSomaPositions()
        except:
            print('NES error: failed to receive model cell positions')
            exit(1)

        print(str(cell_positions))

        # Free memory
        try:
            MySim.DeleteResidentByID(Pause_s=0.1)
        except:
            print('NES error: unable to delete resident simulation')
            exit(1)

    print('Done.')
    exit(0)
