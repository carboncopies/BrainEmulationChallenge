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
    NeuronsByID:dict = {}
    AxonsByID:dict = {}
    DendritesByID:dict = {}
    for i in range(len(Neurons)):
        
        print(f'        - Creating Neuron {i}/{len(Neurons)}')
        
        Neuron = Neurons[i]

        SphereCfg = NES.Shapes.Sphere.Configuration()
        SphereCfg.Name = "Soma"
        SphereCfg.Radius_um = Neuron["SomaRadius_um"]
        SphereCfg.Center_um = Neuron["Position_um"]
        Soma = MySim.AddSphere(SphereCfg)

        # Create Axons
        AxonCompartments:list = []
        for Connection in Connections:
            if (Connection["From"] == Neuron["Name"]):

                CylinderConfig:object = NES.Shapes.Cylinder.Configuration
                CylinderConfig.Name = "Axon Compartment"
                CylinderConfig.Point1Radius_um = 2.0
                CylinderConfig.Point1Position_um = Neuron["Position_um"]
                CylinderConfig.Point2Radius_um = 2.0
                CylinderConfig.Point2Position_um = FindNeuronByName(Neurons, Connection["To"])["Position_um"]
                Cylinder = MySim.AddCylinder(CylinderConfig)

                AxonCompartments.append(AddSCCompartmnet(MySim, Cylinder))

        # Create Dendrites
        DendriteCompartments:list = []
        for Connection in Connections:
            if (Connection["To"] == Neuron["Name"]):

                CylinderConfig:object = NES.Shapes.Cylinder.Configuration
                CylinderConfig.Name = "Dendrite Compartment"
                CylinderConfig.Point1Radius_um = 2.0
                CylinderConfig.Point1Position_um = Neuron["Position_um"]
                CylinderConfig.Point2Radius_um = 2.0
                CylinderConfig.Point2Position_um = FindNeuronByName(Neurons, Connection["From"])["Position_um"]
                Cylinder = MySim.AddCylinder(CylinderConfig)

                DendriteCompartments.append(AddSCCompartmnet(MySim, Cylinder))

        SomaCompartment = AddSCCompartmnet(MySim, Soma)

        AxonIDs:list = []
        for Axon in AxonCompartments:
            AxonIDs.append(Axon.ID)

        DendriteIDs:list = []
        for Dendrite in DendriteCompartments:
            DendriteIDs.append(Dendrite.ID)

        SCNeuronConfig:object = NES.Models.Neurons.SC.Configuration
        SCNeuronConfig.Name = "SCNeuron"
        SCNeuronConfig.SomaIDs = [Soma.ID]
        SCNeuronConfig.AxonIDs = AxonIDs
        SCNeuronConfig.DendriteIDs = DendriteIDs
        SCNeuronConfig.MembranePotential_mV = -60.0
        SCNeuronConfig.RestingPotential_mV = -60.0
        SCNeuronConfig.SpikeThreshold_mV = -50.0
        SCNeuronConfig.DecayTime_ms = 30.0
        SCNeuronConfig.AfterHyperpolarizationAmplitude_mV = -20.0
        SCNeuronConfig.PostsynapticPotentialRiseTime_ms = 5.0
        SCNeuronConfig.PostsynapticPotentialDecayTime_ms = 25.0
        SCNeuronConfig.PostsynapticPotentialAmplitude_nA = 870.0
        SCNeuron = MySim.AddSCNeuron(SCNeuronConfig)

        NeuronsByID.update({Neuron["Name"]: SCNeuron})
        AxonsByID.update({Neuron["Name"]: AxonIDs})
        DendritesByID.update({Neuron["Name"]: DendriteIDs})

    # Make Receptors
    print("    - Creating Receptors")
    AMPA_conductance = 40.0 # nS
    GABA_conductance = -40.0 # nS
    for Connection in Connections:

        BoxConfig = NES.Shapes.Box.Configuration
        BoxConfig.Name = "Box"
        BoxConfig.CenterPosition_um = FindNeuronByName(Neurons, Connection["To"])["Position_um"]
        BoxConfig.Dimensions_um = [0.5,0.5,0.5]
        BoxConfig.Rotation_rad = [0,0,0]
        Box = MySim.AddBox(BoxConfig)

        ReceptorConfig = NES.Models.Connections.Receptor.Configuration
        ReceptorConfig.Name = "Receptor"
        ReceptorConfig.SourceCompartment = AxonsByID[Connection["From"]][0]
        ReceptorConfig.DestinationCompartment = DendritesByID[Connection["To"]][0]
        if (Connection["Type"] == "AMPA"):
            Conductance = AMPA_conductance
        else:
            Conducatance = GABA_conductance
        ReceptorConductance = Conductance / Connection["Weight"]

        ReceptorConfig.Conductance_nS = ReceptorConductance
        ReceptorConfig.TimeConstantRise_ms = 5.0
        ReceptorConfig.TimeConstantDecay_ms = 25.0
        ReceptorConfig.ReceptorMorphology = Box.ID
        Receptor = MySim.AddReceptor(ReceptorConfig)

    print("    - Done, Saving Handle")
    Handle = ClientInstance.SaveSimulation(MySim)

    print(f"     - Saved Handle As '{Handle}'")
    with open(OutputFilePath, "w") as f:
        f.write(Handle)

if __name__ == "__main__":
    Main(Args)