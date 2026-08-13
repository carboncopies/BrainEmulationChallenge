#!../../../venv/bin/python
# check_connectome.py
# Quick diagnostic: load the already-saved "mushroombody" model and
# test both GetConnectome() and GetAbstractConnectome(Sparse=True)
# with real exception detail printed, instead of the bare except:
# that swallowed the error in drosophila_resevoir.py. No regrow
# needed -- this just loads the model already saved on the server.

import argparse
import vbpcommon as vbp
from BrainGenix.BG_API import NES

Parser = argparse.ArgumentParser()
Parser.add_argument("-Host", default="localhost", type=str)
Parser.add_argument("-Port", default=8000, type=int)
Parser.add_argument("-UseHTTPS", default=False, type=bool)
Parser.add_argument("-modelname", default="mushroombody", type=str)
Args = Parser.parse_args()

ClientCfg = NES.Client.Configuration()
ClientCfg.Mode = NES.Client.Modes.Remote
ClientCfg.Host = Args.Host
ClientCfg.Port = Args.Port
ClientCfg.UseHTTPS = Args.UseHTTPS
ClientCfg.AuthenticationMethod = NES.Client.Authentication.Password
ClientCfg.Username = "Admonishing"
ClientCfg.Password = "Instruction"

print(" -- Creating Client Instance")
ClientInstance = NES.Client.Client(ClientCfg)
if not ClientInstance.IsReady():
    print("Client not ready.")
    exit(1)

print(" -- Creating Simulation")
SimulationCfg = NES.Simulation.Configuration()
SimulationCfg.Name = "Netmorph-"+Args.modelname
SimulationCfg.Seed = 0
MySim = ClientInstance.CreateSimulation(SimulationCfg)

print(" -- Loading model: "+Args.modelname)
try:
    MySim.ModelLoad(Args.modelname)
    print(" -- Model loaded successfully.")
except Exception as e:
    print(" -- ModelLoad FAILED:", repr(e))
    exit(1)

print("\n=== Trying GetConnectome() ===")
try:
    result = MySim.GetConnectome()
    print(" -- SUCCESS. Type:", type(result))
    print(" -- Keys/preview:", str(result)[:500])
except Exception as e:
    print(" -- FAILED:", repr(e))

print("\n=== Trying GetAbstractConnectome(Sparse=True) ===")
try:
    result = MySim.GetAbstractConnectome(Sparse=True)
    print(" -- SUCCESS. Type:", type(result))
    print(" -- Keys/preview:", str(result)[:500])
except Exception as e:
    print(" -- FAILED:", repr(e))

print("\n=== Trying vbp.PlotAndStoreConnections() ===")
import os
print(" -- Current working directory:", os.getcwd())
print(" -- Does 'output' dir exist?:", os.path.isdir('output'))
FIGSPECS={'figsize': (6,6), 'linewidth': 0.5, 'figext': 'pdf'}
try:
    connections_dict = MySim.GetConnectome()
    ok = vbp.PlotAndStoreConnections(connections_dict, 'output', 'test_weights', FIGSPECS)
    print(" -- PlotAndStoreConnections returned:", ok)
except Exception as e:
    print(" -- FAILED:", repr(e))
    import traceback
    traceback.print_exc()

print("\n -- Done.")
