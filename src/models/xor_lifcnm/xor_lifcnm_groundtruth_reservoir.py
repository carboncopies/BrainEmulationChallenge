#!../../../venv/bin/python
# xor_lifcnm_groundtruth_reservoir.py
# Randal A. Koene, 20250804

# This script is STEP 1 in the creation of realistic
# ground-truth virtual tissue containing an intended
# cognitive function.
#
# The BrainGenix API is used to direct NES to run embedded
# Netmorph on Netmorph script to grow a reservoir of
# connections between pyramidal cell and interneuron
# regions.
#
# The ModelSave API function is called to ensure that the resulting
# NES Simulation model is stored in a rapid binary format on the server.

scriptversion='0.1.0'

#import numpy as np
#from datetime import datetime
from time import sleep
#import json
import base64
import argparse
#import os

import vbpcommon as vbp
from BrainGenix.BG_API import NES


# Handle Arguments for Host, Port, etc
Parser = argparse.ArgumentParser(description="BrainGenix-API Simple Python Test Script")
Parser.add_argument("-Host", default="localhost", type=str, help="Host to connect to")
Parser.add_argument("-Port", default=8000, type=int, help="Port number to connect to")
Parser.add_argument("-UseHTTPS", default=False, type=bool, help="Enable or disable HTTPS")
Parser.add_argument("-modelfile", type=str, help="File to read model instructions from")
Parser.add_argument("-modelname", default="xor_scnm", type=str, help="Name of neuronal circuit model to save")
Parser.add_argument("-growdays", type=int, help="Number of days Netmorph growth")
Parser.add_argument("-DoOBJ", default=False, type=bool, help="Netmorph should produce OBJ output")
Parser.add_argument("-DoBlend", default=False, type=bool, help="Netmorph should produce Blender output")
Parser.add_argument("-BlendExec", default="/home/rkoene/blender-4.1.1-linux-x64/blender", type=str, help="Path to Blender executable")
Parser.add_argument("-BevelDepth", default=0.1, type=float, help="Blender neurite bevel depth")
Parser.add_argument("-ExpsDB", default="./ExpsDB.json", type=str, help="Path to experiments database JSON file")
Args = Parser.parse_args()

if Args.DoBlend:
    Args.DoOBJ = True

# Initialize data collection for entry in DB file
DBdata = vbp.InitExpDB(
    Args.ExpsDB,
    'reservoir',
    scriptversion,
    _initIN = {
        'modelfile': Args.modelfile,
        'growdays_override': str(Args.growdays),
    },
    _initOUT = {
        'modelname': Args.modelname,
    })


# Load Netmorph model file
modelcontent = 'kjhskdjfhkjhs'

if Args.modelfile:
    try:
        with open(Args.modelfile, 'r') as f:
            modelcontent = f.read()
    except Exception as e:
        vbp.ErrorExit(DBdata, 'modelfile error: '+str(e))
else:
    vbp.ErrorExit(DBdata, 'missing modelfile')


# Modify Netmorph model content based on overrides
NETMORPH_OBJ = '''
outattr_make_full_OBJ=true;
outattr_OBJ_bevdepth_axon=%.1f;
outattr_OBJ_bevdepth_dendrite=%.1f;
'''

NETMORPH_BLEND = '''
outattr_make_full_blend=true;
blender_exec_path=%s;
'''

GROWDAYS = '''
days=%d;
'''

if Args.DoOBJ:
    modelcontent += NETMORPH_OBJ % (Args.BevelDepth, Args.BevelDepth)
if Args.DoBlend:
    modelcontent += NETMORPH_BLEND % Args.BlendExec
if Args.growdays:
    modelcontent += GROWDAYS % Args.growdays


# Create Client Configuration For Local Simulation
print(" -- Creating Client Configuration For Local Simulation")
ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"


# Create Client Instance
print(" -- Creating Client Instance")
try:
    ClientInstance = NES.Client.Client(ClientCfg)
    if not ClientInstance.IsReady():
        vbp.ErrorExit(DBdata, 'NES.Client error: not ready')
except Exception as e:
    vbp.ErrorExit(DBdata, 'NES.Client error: '+str(e))


# Create A New Simulation
print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "Netmorph-"+Args.modelname
SimulationCfg.Seed = 0
try:
    MySim = ClientInstance.CreateSimulation(SimulationCfg)
except:
    vbp.ErrorExit(DBdata, 'NES error: Failed to create simulation')


# Run Netmorph
RunResponse = MySim.Netmorph_RunAndWait(modelcontent, _NeuronClass='LIFC')
if not RunResponse["Success"]:
    vbp.ErrorExit(DBdata, 'NES.Netmorph error: Netmorph reservoir build failed with status response:'+str(RunResponse["NetmorphStatus"]))

vbp.AddOutputToDB(DBdata, 'NetmorphOutputDirectory', str(RunResponse["NetmorphOutputDirectory"]))
print(" -- Netmorph output files directory is "+str(RunResponse["NetmorphOutputDirectory"]))

# Save model at the NES server
try:
    MySim.ModelSave(Args.modelname)
    print(" -- Neuronal Circuit Model saved as "+Args.modelname)
except:
    vbp.ErrorExit(DBdata, 'NES error: Model save failed')

# Retrieve gzipped Blender file if one was requested
if Args.DoBlend:
    try:
        print(" -- Getting Gzipped Blender file to netmorph-net.blend.gz")
        FileBytes = MySim.Netmorph_GetFile('net.obj.blend.gz')
        try:
            blendgzfile = Args.modelname+'-netmorph-net.blend.gz'
            with open(blendgzfile, 'wb') as f:
                f.write(base64.decodebytes(FileBytes))
            vbp.AddOutputToDB(DBdata, 'blendgz', blendgzfile)
        except:
            vbp.ErrorToDB(DBdata, 'File error: Unable to save gzipped Blender file to '+blendgzfile)
    except:
        vbp.ErrorToDB(DBdata, 'NES.Netmorph error: Failed to get gzipped Blender data')

# Update experiments database file with results
vbp.UpdateExpsDB(DBdata)

print(" -- Done.")
