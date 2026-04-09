# Using XOR Simple Compartmental Netmorph scripts

1. Run `./xor_scnm_groundtruth_reservoir.py -modelfile nesvbp-xor-res-sep-targets`
   to produce a model with realistic neurites and save it on the server with the
   default model name `xor_scnm`.

2. Run `./xor_scnm_groundtruth_connectome.py` to tune and prune the reservoir into
   a connectome that is able to support the spiking XOR I/O function. This is
   saved on the server with the default model name `xor_scnm-tuned`.

3. Run `./xor_scnm_acquisition_direct.py` to run test activity on the model and
   acquire data from the virtual tissue.

## Using the virtual Python environment

The BrainEmulationChallenge repository comes with `Tools/Setup.sh` and `Tools/Update.sh`
scripts that assume you are using a virtual environment to set up necessary Python
modules.

The `Run.sh` script provided for the xor_scnm example includes activation of the
virtual environment (`source venv/bin/activate`).

If you are running the scripts described above independently you may need to
activate the virtual environment explicitly first. The `venv` folder is located
at the root of the repository (BrainEmulationChallenge/venv). So, to activate
from the `xor_scnm` folder:

```
source ../../../venv/bin/activate
```

## Default dynamics

The XOR Simple Compartmental (xor_scnm) example uses Netmorph to grow the
structure of the model and uses the default parameter values for SC neuron
dynamics as specified for NES-embedded Netmorph.

These are specified in the BrainGenix-NES repository, in file
Source/Core/Netmorph/NetmorphManagerThread.cpp, as follows:

```
const std::map<synapse_type, float> conductances_nS = {
    { syntype_AMPAR, 40.0 },
    { syntype_NMDAR, 60.0 },
    { syntype_GABAR, -40.0 },
    { syntype_candidate, 0.0 },
    { syntype_GluR, 40.0 },
    { syntype_iGluR, 40.0 },
    { syntype_mGluR, 40.0 },
};

struct DynamicPars {
    float neuron_Vm_mV = -60.0;
    float neuron_Vrest_mV = -60.0;
    float neuron_Vact_mV = -50.0;
    float neuron_Vahp_mV = -20.0;
    float neuron_tau_AHP_ms = 30.0;
    float neuron_IPSP = 870.0; // nA
};

struct PSPTiming {
    float neuron_tau_PSPr = 5.0;
    float neuron_tau_PSPd = 25.0;
};
```

Use the PythonClient BrainGenix API function Simulation.EditSCNeuron() to
change dynamic parameters.
