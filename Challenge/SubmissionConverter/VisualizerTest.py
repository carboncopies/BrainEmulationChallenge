#!/bin/python3

import argparse
import math

import BrainGenix
import BrainGenix.NES as NES


# Define Arguments To Parse
Parser = argparse.ArgumentParser(description="Submission Conversion Format For The Standardized WBE Challenge")
Parser.add_argument("-Remote", action='store_true', help="Build Converted Model On Remote NES Server Rather Than Localhost")
Parser.add_argument("-i", required=True, help="Path To Input Filename")
Parser.add_argument("-o", required=True, help="Path To Directories Where Images Will Be Saved")
Parser.add_argument("--CameraDistance", default=50, help="Distance in micrometers from the world origin to rotate the camera around")
Parser.add_argument("--CameraHeight", default=50, help="Sets the height of the camera on the z axis from the world origin")
Parser.add_argument("--NumSteps", default=10, help="Sets the number of steps to orbit around the sample with")
Parser.add_argument("--Width", default=2048, help="Sets the width in pixels of the output images")
Parser.add_argument("--Height", default=2048, help="Sets the height in pixels of the output images")
Parser.add_argument("--FOV", default=2048, help="Sets the FOV of the camera")
Parser.add_argument("--BatchDownload", default=2, help="Sets the number of images to download simultaneously")
Args = Parser.parse_args()



def PointsInCircum(r, n=100):
    return [(math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r) for x in range(0,n+1)]


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
    VisualizerJob = BrainGenix.NES.Visualizer.Configuration()
    VisualizerJob.ImageWidth_px = Args.Width
    VisualizerJob.ImageHeight_px = Args.Height


    # Render In Circle Around Sim
    Radius = Args.CameraDistance
    Steps = Args.NumSteps
    ZHeight = Args.CameraHeight

    for Point in PointsInCircum(Radius, Steps):

        VisualizerJob.CameraFOVList_deg.append(Args.FOV)
        VisualizerJob.CameraPositionList_um.append([Point[0], Point[1], ZHeight])
        VisualizerJob.CameraLookAtPositionList_um.append([0, 0, ZHeight])

    Visualizer = MySim.SetupVisualizer()
    Visualizer.GenerateVisualization(VisualizerJob)


    Visualizer.SaveImages(f"{OutputFilePath}/", Args.BatchDownload)

if __name__ == "__main__":
    Main(Args)