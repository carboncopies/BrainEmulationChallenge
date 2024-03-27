#!/usr/bin/env python3
# xor_sc_emulation.py
# Randal A. Koene, 20240326

'''
The XOR SimpleCompartmental example uses branching axons in a representation of a
meaningful logic circuit to produce expected functional output.

This file implements a validation procedure for the resulting emulation.

VBP process step 03: emulation validation
WBE topic-level III: evolving similarity / performance metrics
'''

scriptversion='0.0.1'

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from time import sleep
import argparse
import math
import json

import vbpcommon
import os
from BrainGenix.BG_API import Credentials, SimClient
from NES_interfaces.KGTRecords import plot_recorded

from NES_interfaces.Metrics_N1 import Metrics_N1

import BrainGenix.NES as NES
import BrainGenix
from BrainGenix.Tools.StackStitcher import StackStitcher, CaImagingStackStitcher

Parser = argparse.ArgumentParser(description="vbp script")
Parser.add_argument("-RenderVisualization", action='store_true', help="Enable or disable visualization")
Parser.add_argument("-RenderEM", action='store_true', help="Enable or disable em stack rendering")
Parser.add_argument("-RenderCA", action='store_true', help="Enable or disable Calcium imaging rendering")
Parser.add_argument('-Electrodes', action='store_true', help="Place electrodes")
Parser.add_argument("-Local", action='store_true', help="Render remotely or on localhost")
Parser.add_argument("-Remote", action='store_true', help="Run on remote NES server")
Args = Parser.parse_args()

#default:
api_is_local=True
if Args.Remote:
    api_is_local=False
if Args.Local:
    api_is_local=True

TotalElectrodes:int = 0;
TotalCARenders:int = 0;
TotalEMRenders:int = 0;

runtime_ms=500.0
savefolder = 'output/'+str(datetime.now()).replace(":", "_")+'-validation'
figspecs = {
    'figsize': (6,6),
    'linewidth': 0.5,
    'figext': 'pdf',
}

# 1. Init NES connection

credentials = Credentials(user='Admonishing', passwd='Instruction')
client = SimClient(credentials, api_is_local)

# 2. Load ground-truth network

# 2.1 Request Loading
simulation_sys_name=None
with open(".SimulationHandle", "r") as f:
    simulation_sys_name = f.read()

print(f"Retrieving simulation with handle '{simulation_sys_name}'")

# loadingtaskID = bg_api.BGNES_load(timestampedname=sys_name)

# print('Started Loading Task (%s) for Saved Simulation %s' % (str(loadingtaskID), str(sys_name)))

# # 2.2 Await Loading and set Simulation ID

# while True:
#     sleep(0.005)
#     response_list = bg_api.BGNES_get_manager_task_status(taskID=loadingtaskID)
#     if not isinstance(response_list, list):
#         print('Bad response format. Expected list of NESRequest responses.')
#         exit(1)
#     task_status_response = response_list[0]
#     if task_status_response['StatusCode'] != 0:
#         print('Checking task status failed, status code: '+str(task_status_response['StatusCode']))
#         exit(1)
#     if "TaskStatus" not in task_status_response:
#         print('No TaskStatus received.')
#         exit(1)
#     task_status = task_status_response['TaskStatus']
#     if task_status > 1:
#         print('Loading Task failed.')
#         exit(1)
#     if task_status == 0:
#         break

# print('Loading task completed successfully.')
# if "SimulationID" not in task_status_response:
#     print('Missing SimulationID.')
#     exit(1)
# SimulationID = task_status_response["SimulationID"]
# bg_api.Simulation.Sim.ID = SimulationID

# print('New ID of loaded Simulation: '+str(SimulationID))

simulation_sys_path='./'+simulation_sys_name+'-simulation'
client.Instance.DownloadSimulation(_SaveHandle=simulation_sys_name, _FilePath=simulation_sys_path)

# 3. Load emulation network

# 3.1 Request Loading
emulation_sys_name=None
with open(".EmulationHandle", "r") as f:
    emulation_sys_name = f.read()

print(f"Retrieving emulation with handle '{emulation_sys_name}'")

# loadingtaskID = bg_api.BGNES_load(timestampedname=sys_name)

# print('Started Loading Task (%s) for Saved Emulation %s' % (str(loadingtaskID), str(sys_name)))

# # 3.2 Await Loading and set Emulation ID

# while True:
#     sleep(0.005)
#     response_list = bg_api.BGNES_get_manager_task_status(taskID=loadingtaskID)
#     if not isinstance(response_list, list):
#         print('Bad response format. Expected list of NESRequest responses.')
#         exit(1)
#     task_status_response = response_list[0]
#     if task_status_response['StatusCode'] != 0:
#         print('Checking task status failed, status code: '+str(task_status_response['StatusCode']))
#         exit(1)
#     if "TaskStatus" not in task_status_response:
#         print('No TaskStatus received.')
#         exit(1)
#     task_status = task_status_response['TaskStatus']
#     if task_status > 1:
#         print('Loading Task failed.')
#         exit(1)
#     if task_status == 0:
#         break

# print('Loading task completed successfully.')
# if "SimulationID" not in task_status_response:
#     print('Missing SimulationID.')
#     exit(1)
# SimulationID = task_status_response["SimulationID"]
# bg_api.Simulation.Sim.ID = SimulationID

# print('New ID of loaded Emulation: '+str(SimulationID))

emulation_sys_path='./'+emulation_sys_name+'-simulation'
client.Instance.DownloadSimulation(_SaveHandle=emulation_sys_name, _FilePath=emulation_sys_path)

# -- 4. Retrieve ground-truth simulation data to get structure

RPCpath = {
	'compartment': 'Simulation/Compartments/SC/Create',
	'neuron': 'Simulation/Neuron/SC/Create',
	'receptor': 'Simulation/Receptor/Create',
}

# A simplified System class used just for validation.
class System:
	def __init__(self, retrieved_file:list):
		self.compartments = self.find_compartments(retrieved_file)
		self.neurons = self.find_neurons(retrieved_file)
		self.receptors = self.find_receptors(retrieved_file)

	def find_compartments(self, retrieved_file:list):
		RPC = RPCpath['compartment']
		compartments = []
		for NESrequest in retrieved_file:
			if RPC in NESrequest:
				compartments.append( NESrequest )
		return compartments

	def find_neurons(self, retrieved_file:list):
		RPC = RPCpath['neuron']
		neurons = []
		for NESrequest in retrieved_file:
			if RPC in NESrequest:
				neurons.append( NESrequest )
		return neurons

	def get_compartment(self, compartment_id:int)->dict:
		if compartment_id >= len(self.compartments):
			return None
		return self.compartments[compartment_id]

	def find_receptors(self, retrieved_file:list):
		RPC = RPCpath['receptor']
		receptors = []
		for NESrequest in retrieved_file:
			if RPC in NESrequest:
				receptors.append( NESrequest )
		return receptors

	def get_neuron_by_compartment(self, compartment_id:int)->int:
		RPC = RPCpath['neuron']
		for i in range(len(self.neurons)):
			if compartment_id in self.neurons[i][RPC]['SomaIDs']:
				return i
			if compartment_id in self.neurons[i][RPC]['DendriteIDs']:
				return i
			if compartment_id in self.neurons[i][RPC]['AxonIDs']:
				return i
		return None

	def get_receptor_neurons(self, receptor_id:int)->tuple:
		RPC = RPCpath['receptor']
		if receptor_id >= len(self.receptors):
			return None
		#src_compartment = self.get_compartment(self.receptors[receptor_id][RPC]['SourceCompartmentID'])
		#dst_compartment = self.get_compartment(self.receptors[receptor_id][RPC]['DestinationCompartmentID'])
		src_compartment = self.receptors[receptor_id][RPC]['SourceCompartmentID']
		dst_compartment = self.receptors[receptor_id][RPC]['DestinationCompartmentID']
		src_neuron = self.get_neuron_by_compartment(src_compartment)
		dst_neuron = self.get_neuron_by_compartment(dst_compartment)
		return (src_neuron, dst_neuron)

	def get_connectivity(self)->list:
		RPC = RPCpath['receptor']
		connectivity = []
		for i in range(len(self.receptors)):
			weight = self.receptors[i][RPC]['Conductance_nS']
			connectivity.append( list(self.get_receptor_neurons(i)) + [ weight ] )
		return connectivity

	def get_all_neurons(self)->list:
		return self.neurons

# Let's assume that retrieval gives it back as a string of NES requests.

with open(simulation_sys_path+'.NES', 'r') as f:
	retrieved_file = json.load(f)

print('Number of requests found in retrieved savefile: '+str(len(retrieved_file)))

groundtruth = System(retrieved_file)

print('Number of neurons in ground-truth: '+str(len(groundtruth.neurons)))
print('Number of receptors in ground-truth: '+str(len(groundtruth.receptors)))

print('Connectivity in ground-truth:'+str(groundtruth.get_connectivity()))

# -- 5. Retrieve emuation data to get structure

with open(emulation_sys_path+'.NES', 'r') as f:
	retrieved_file = json.load(f)

print('Number of requests found in retrieved savefile: '+str(len(retrieved_file)))

emulation = System(retrieved_file)

print('Number of neurons in circuit emulation: '+str(len(emulation.neurons)))
print('Number of receptors in circuit emulation: '+str(len(emulation.receptors)))

print('Connectivity in circuit emulation:'+str(emulation.get_connectivity()))

# -- 6. Run structure comparison with Metrics N1

metric_n1 = Metrics_N1(emulation, groundtruth)
metric_n1.validate()
