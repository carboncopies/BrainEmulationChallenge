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
Parser.add_argument("-o", required=True, help="Path To Directories Where Images Will Be Saved")
Args = Parser.parse_args()


def AddSCCompartmnet(_Sim, _Shape):
    SCCompartmentConfig:object = NES.Models.Compartments.SC.Configuration
    SCCompartmentConfig.Name = "Compartment - Soma"
    SCCompartmentConfig.MembranePotential_mV = -60.0
    SCCompartmentConfig.SpikeThreshold_mV = -50.0
    SCCompartmentConfig.DecayTime_ms = 30.0
    SCCompartmentConfig.RestingPotential_mV = -60.0
    SCCompartmentConfig.AfterHyperpolarizationAmplitude_mV = -20.0
    SCCompartmentConfig.Shape = _Shape
    return _Sim.AddSCCompartment(SCCompartmentConfig)

def FindNeuronByName(_Neurons, _Name):
    for Neuron in _Neurons:
        if Neuron["Name"] == _Name:
            return Neuron
    print("Error! The Input Format is not valid, it referneces a nonexistant neuron!")
    return None

def Main(Args):

    # Get Arguments From Parser
    InputFilePath:str = Args.i
    OutputFilePath:str = Args.o
    UseRemoteNES:bool = Args.Remote

    # Get Input File Open
    print(" ---- WBE Challenge Visualization Tool\n")
    print(" -- Arg Config")
    print(f"    - Loading Submission From: '{InputFilePath}'")
    print(f"    - Using Remote NES (api.braingenix.org): '{UseRemoteNES}'")
    print("")

    # Now, Open File
    SimulationHandle:str = ""
    with open(InputFilePath, "r") as f:
        SimulationHandle = f.read()

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

    # Next, We Load This In NES
    print(" -- Loading NES Simulation")
    MySim = ClientInstance.LoadSimulation(SimulationHandle)

    print(" - Visualizing Simulation")


if __name__ == "__main__":
    Main(Args)