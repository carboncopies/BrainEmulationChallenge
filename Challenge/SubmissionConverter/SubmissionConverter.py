#!/bin/python3

import argparse
import json
import datetime

import BrainGenix
import BrainGenix.NES as NES


# Define Arguments To Parse
Parser = argparse.ArgumentParser(description="Submission Conversion Format For The Standardized WBE Challenge")
Parser.add_argument("-Remote", action='store_true', help="Build Converted Model On Remote NES Server Rather Than Localhost")
Parser.add_argument("-i", required=True, help="Path To Input Filename")
Parser.add_argument("-o", required=True, help="Path To File Where Handle Will Be Saved")
Args = Parser.parse_args()


def Main(Args):

    # Get Arguments From Parser
    InputFilePath:str = Args.i
    OutputFilePath:str = Args.o
    UseRemoteNES:bool = Args.Remote

    # Get Input File Open
    print(" ---- WBE Challenge Conversion Tool\n")
    print(" -- Arg Config")
    print(f"    - Loading Submission From: '{InputFilePath}'")
    print(f"    - Writing Converted NES Handle To: '{OutputFilePath}'")
    print(f"    - Using Remote NES (api.braingenix.org): '{UseRemoteNES}'")
    print("")

    # Now, Open File
    SubmissionJSON:dict = None
    with open(InputFilePath, "r") as f:
        SubmissionJSON = json.loads(f.read())

    Neurons:list = SubmissionJSON["Neurons"]
    Connections:list = SubmissionJSON["Connections"]

    # Now, Print Some Metadata Here
    print(" -- Submission Info")
    print(f"    - Dataset Model: {SubmissionJSON['Model']}")
    print(f"    - Submission Authors: {SubmissionJSON['SubmissionAuthors']}")
    print(f"    - Submission Version: {SubmissionJSON['SubmissionFormatVersion']}")
    print(f"    - Total Neurons: {len(Neurons)}")
    print(f"    - Total Synapses: {len(Neurons)}")
    
    
    # Next, We Build This In NES
    print(" -- Building NES Simulation")

    ClientCfg = NES.Client.Configuration()
    ClientCfg.Mode = NES.Client.Modes.Remote
    if (UseRemoteNES):
        ClientCfg.Host = "api.braingenix.org"
        ClientCfg.Port = 443
        ClientCfg.UseHTTPS = True
    else:
        ClientCfg.Host = "localhost"
        ClientCfg.Port = 8000
        ClientCfg.UseHTTPS = False
    ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
    ClientCfg.Username = "Admonishing"
    ClientCfg.Password = "Instruction"

    print(f"    - Creating Client Instance")
    ClientInstance = NES.Client.Client(ClientCfg)


    print(f"    - Creating Simulation")
    SimulationCfg = NES.Simulation.Configuration()
    SimulationCfg.Name = f"Submission_{datetime.datetime.now().strftime('%d-%m-%Y_%Hh%Mm%S')}_{SubmissionJSON['Model']}"
    SimulationCfg.Seed = 0
    MySim = ClientInstance.CreateSimulation(SimulationCfg)

    # Now, Build The Neurons
    print(f"    - Creating Neurons")
    Spheres = []
    for Neuron in Neurons:
        
        SphereCfg = NES.Shapes.Sphere.Configuration()
        SphereCfg.Name = "Soma"
        SphereCfg.Radius_um = Neuron["SomaRadius_um"]
        SphereCfg.Center_um = Neuron["Position_um"]
        Spheres.append(MySim.AddSphere(SphereCfg))

    


if __name__ == "__main__":
    Main(Args)