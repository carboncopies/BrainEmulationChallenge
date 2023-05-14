#!/usr/bin/env python3
# syn_transmission.py
# Randal A. Koene, 20230507

'''
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
'''

import matplotlib.pyplot as plt
from math import exp
import numpy as np
import json

class SynTr_Quantal_Release:
	def __init__(self, N_T_init:int=10, P_init:float=0.5):
		'''
		In CNS, the number of vesicles ready to fuse with membrane in the presence of Ca2+ and
		cause quantal release is typically between 10-100. For cerebellar MF-GC connections,
		the number is 5-10, 1 vesicle per synaptic contact.
		The release probability is characteristically 0.5.
		'''
		self.N_T:int = N_T_init # total number of quanta available for release
		self.P:float = P_init # release probability

	def quantal_content_m(self)->float:
		return self.N_T*self.P


class NES_AMPA_Receptor:
	'''
	Use this class as a convenient stand-in that carries out actual instantiation
	and all method calls through the NES API.
	'''
	def __init__(self,
			ID='0',
			Gsyn_pS_init:float=0,
			Esyn_mV_init:float=0,
			Vm_mV_init:float=0,
			Isyn_pA_init:float=0,
			tau_d_ms_init:float=2.0,
			tau_r_ms_init:float=0.2,
			tau_d2_ms_init:float=3.0,
			tau_d3_ms_init:float=4.0,
			d1_init:float=0.5,
			d2_init:float=0.3,
			d3_init:float=0.2,
			x_init:float=1.5,
			g_peak_pS_init:float=39,
			a_norm_init:float=1.0,
		)->None:
		API_call(
				'NES/AMPAR/init',
				json.dumps(
						'ID': ID,
						'Gsyn_pS_init': Gsyn_pS_init,
						'Esyn_mV_init': Esyn_mV_init,
						'Vm_mV_init': Vm_mV_init,
						'Isyn_pA_init': Isyn_pA_init,
						'tau_d_ms_init': tau_d_ms_init,
						'tau_r_ms_init': tau_r_ms_init,
						'tau_d2_ms_init': tau_d2_ms_init,
						'tau_d3_ms_init': tau_d3_ms_init,
						'd1_init': d1_init,
						'd2_init': d2_init,
						'd3_init': d3_init,
						'x_init': x_init,
						'g_peak_pS_init': g_peak_pS_init,
						'a_norm_init': a_norm_init,
					),
			)
	def set_psp_type(self, psp_type:str):
		API_call(
				'NES/AMPAR/set_psp_type',
				json.dumps(
						'ID': ID,
						'psp_type': psp_type, # 'dblexp' or 'mxh'
					)
			)
	# PROPOSAL 1: Waiting for a response can be a blocking await function as
	# shown here.
	# PROPOSAL 2: Waiting can be done in the background by making this an
	# async function and using 'await API_response()'.
	def np_Gsyn_t_pS_dbl(self, t_ms:np.ndarray)->np.ndarray:
		API_call(
				'NES/AMPAR/np_Gsyn_t_pS_dbl',
				json.dumps(
						'ID': ID,
						't_ms': t_ms,
					)
			)
		resp = await_API_response('NES/AMPAR/np_Gsyn_t_pS_dbl', ID)
		if resp is None:
			raise Exception(get_API_error())
		if 'error' in resp:
			raise Exception(resp['error'])
		return resp['Gsyn_t_pS']
	# PROPOSAL 3: Instead of waiting, the API_call() function could be supplied
	# with a callback function reference, which is placed into a hash map and
	# called when a matching response is received (or timeout happens).
	def np_Gsyn_t_pS_dbl_withcallback(self, t_ms:np.ndarray)->bool:
		API_call(
				'NES/AMPAR/np_Gsyn_t_pS_dbl',
				json.dumps(
						'ID': ID,
						't_ms': t_ms,
					)
				callback=self.np_Gsyn_t_pS_dbl_handle
			)
		return True
	def np_Gsyn_t_pS_mxh(self, t_ms:np.ndarray)->np.ndarray:
		API_call(
				'NES/AMPAR/np_Gsyn_t_pS_mxh',
				json.dumps(
						'ID': ID,
						't_ms': t_ms,
					)
			)
		resp = await_API_response('NES/AMPAR/np_Gsyn_t_pS_mxh', ID)
		if resp is None:
			raise Exception(get_API_error())
		if 'error' in resp:
			raise Exception(resp['error'])
		return resp['Gsyn_t_pS']
	def np_Gsyn_t_pS_mxh_withcallback(self, t_ms:np.ndarray)->bool:
		API_call(
				'NES/AMPAR/np_Gsyn_t_pS_mxh',
				json.dumps(
						'ID': ID,
						't_ms': t_ms,
					)
				callback=self.np_Gsyn_t_pS_mxh_handle
			)
		return True


class AMPA_Receptor:
	'''
	This is a (slow) Python demo version of the object instantiation and methods
	for a model AMPA receptor. This can be used for development purposes and for
	reference when building the NES implementation.
	'''
	def __init__(self,
			ID='0',
			Gsyn_pS_init:float=0,
			Esyn_mV_init:float=0,
			Vm_mV_init:float=0,
			Isyn_pA_init:float=0,
			tau_d_ms_init:float=2.0,
			tau_r_ms_init:float=0.2,
			tau_d2_ms_init:float=3.0,
			tau_d3_ms_init:float=4.0,
			d1_init:float=0.5,
			d2_init:float=0.3,
			d3_init:float=0.2,
			x_init:float=1.5,
			g_peak_pS_init:float=39,
			a_norm_init:float=1.0,
		)->None:
		self.ID = ID
		self.Gsyn_pS = Gsyn_pS_init # AMPAR conductance
		self.Esyn_mV = Esyn_mV_init # AMPAR reversal potential
		self.Vm_mV = Vm_mV_init 	# Membrane potential
		self.Isyn_pA = Isyn_pA_init # Synaptic membrane current

		self.tau_d_ms = tau_d_ms_init # Receptor conductance decay time constant (typical: 0.3-2.0 ms)
		self.tau_r_ms = tau_r_ms_init # Receptor conductance rise time constant (typical: 0.2 ms)
		self.tau_d2_ms = tau_d2_ms_init
		self.tau_d3_ms = tau_d3_ms_init
		self.d1 = d1_init
		self.d2 = d2_init
		self.d3 = d3_init
		self.x = x_init

		self.g_peak_pS = g_peak_pS_init # Receptor peak conductance
		self.a_norm = a_norm_init # normalizing scale factor so that peak Gsyn_t_pS == g_peak_pS

		self.a_norms = []
		self.g_diffs = []

		self.np_Gsyn_t_pS = self.np_Gsyn_t_pS_dbl

	def set_psp_type(self, psp_type:str):
		if psp_type=='dblexp':
			self.np_Gsyn_t_pS = self.np_Gsyn_t_pS_dbl
		elif psp_type=='mxh':
			self.np_Gsyn_t_pS = self.np_Gsyn_t_pS_mxh

	def postsyn_current_I(self)->float:
		self.Isyn_pA = self.Gsyn_pS*(self.Vm_mV - self.Esyn_mV)
		return self.Isyn_pA

	def conductance(self)->float:
		self.Gsyn_pS = Isyn_pA / (Vm_mV - Esyn_mV)
		return self.Gsyn_pS

	# t_ms is the time since the presynaptic action potential
	def Gsyn_t_pS_decay_zerorisetime(self, t_ms:float)->float:
		'''
		Modeled with a simple exponential.
		'''
		if t_ms < 0:
			Gsyn_pS_t = 0
		else:
			Gsyn_pS_t = self.g_peak_pS*exp(-t_ms/self.tau_d_ms)
		self.Gsyn_pS = Gsyn_pS_t
		return Gsyn_pS_t

	def Gsyn_t_pS_rise_decay(self, t_ms:float)->float:
		'''
		Modeled with an alpha function.
		'''
		if t_ms < 0:
			Gsyn_pS_t = 0
		else:
			t_ratio = t_ms/self.tau_r_ms
			Gsyn_pS_t = self.g_peak_pS*t_ratio*exp(1.0-t_ratio)
		self.Gsyn_pS = Gsyn_pS_t
		return Gsyn_pS_t

	def Gsyn_t_pS(self, t_ms:float)->float:
		'''
		Modeled with a double exponential.
		'''
		if t_ms < 0:
			Gsyn_pS_t = 0
		else:
			Gsyn_pS_t = self.g_peak_pS*( -exp(-t_ms/self.tau_r_ms) + exp(-t_ms/self.tau_d_ms) ) / self.a_norm
		self.Gsyn_pS = Gsyn_pS_t
		return Gsyn_pS_t

	def np_Gsyn_t_pS_dbl(self, t_ms:np.ndarray)->np.ndarray:
		'''
		Modeled with a double exponential.
		'''
		f = t_ms>=0.0
		t_ms = f*t_ms
		Gsyn_pS_t = self.g_peak_pS*( -np.exp(-t_ms/self.tau_r_ms) + np.exp(-t_ms/self.tau_d_ms) ) / self.a_norm
		self.Gsyn_pS = Gsyn_pS_t
		return Gsyn_pS_t

	def np_Gsyn_t_pS_mxh(self, t_ms:np.ndarray)->np.ndarray:
		'''
		Modeled with a multiexponential function with m^xh formalism to fit
		more complex waveforms.
		'''
		f = t_ms>=0.0
		t_ms = f*t_ms
		Gsyn_pS_t = self.g_peak_pS*np.power( (1.0 - np.exp(-t_ms/self.tau_r_ms)), self.x)*( self.d1*np.exp(-t_ms/self.tau_d_ms) + self.d2*np.exp(-t_ms/self.tau_d2_ms) + self.d3*np.exp(-t_ms/self.tau_d3_ms) ) / self.a_norm
		self.Gsyn_pS = Gsyn_pS_t
		return Gsyn_pS_t


	def plot_it(self, x:list, ys:list, titles:list, nrows=1, ncols=1):
		fig, axs = plt.subplots(nrows=nrows, ncols=ncols)
		for i in range(len(ys)):
			if ncols==1:
				axs.plot(x, ys[i])
				axs.set_title(titles[i])
			else:
				axs[i].plot(x, ys[i])
				axs[i].set_title(titles[i])
		plt.show()

	def numerical_find_a_norm(self, plot_it=False, print_it=False)->float:
		'''
		For analytical solution see Roth & van Rossum (2009).
		'''
		t_ms = np.linspace(0, 100, 10000)
		a_norm_bottom = 0.0
		a_norm_top = 2.0
		self.a_norm = 1.0
		self.a_norms = []
		self.g_diffs = []
		for i in range(100):
			self.a_norms.append(self.a_norm)
			Gsyn_t = self.np_Gsyn_t_pS(t_ms)
			g_diff = Gsyn_t.max() - self.g_peak_pS
			self.g_diffs.append(g_diff)
			if print_it: print('g_diff=%s, a_norm=%s' % (str(g_diff), str(self.a_norm)))
			if abs(g_diff) < 0.1:
				if plot_it: self.plot_it(list(range(i+1)), [ self.g_diffs, self.a_norms ], [ 'g_diff', 'a_norm' ], ncols=2)
				return self.a_norm
			if g_diff > 0:
				a_norm_bottom = self.a_norm
				self.a_norm = (a_norm_top+self.a_norm)/2.0
			else:
				a_norm_top = self.a_norm
				self.a_norm = (a_norm_bottom+self.a_norm)/2.0
		print('100 iterations, g_diff still too large: '+str(g_diff))
		if plot_it: self.plot_it(list(range(100)), [ self.g_diffs, self.a_norms ], [ 'g_diff', 'a_norm' ], ncols=2)
		return self.a_norm

class NMDA_Receptor(AMPA_Receptor):
	def __init__(self,
			ID='0',
			Gsyn_pS_init:float=0,
			Esyn_mV_init:float=0,
			Vm_mV_init:float=0,
			Isyn_pA_init:float=0,
			tau_d_ms_init:float=50.0, # Typically 30-70 ms, sometimes as long as 500 ms.
			tau_r_ms_init:float=10.0, # Typically 10 ms.
			tau_d2_ms_init:float=70.0,
			tau_d3_ms_init:float=300.0,
			d1_init:float=0.5,
			d2_init:float=0.3,
			d3_init:float=0.2,
			x_init:float=1.5,
			g_peak_pS_init:float=39,
			a_norm_init:float=1.0,
			V_halfblocked_init:float=20.0,
			k_init:float=2.0,
		)->None:
		super().__init__(
				ID,
				Gsyn_pS_init,
				Esyn_mV_init,
				Vm_mV_init,
				Isyn_pA_init,
				tau_d_ms_init,
				tau_r_ms_init,
				tau_d2_ms_init,
				tau_d3_ms_init,
				d1_init,
				d2_init,
				d3_init,
				x_init,
				g_peak_pS_init,
				a_norm_init,
			)
		self.V_halfblocked = V_halfblocked_init
		self.k = k_init

	def phi_V(self)->float:
		'''
		Modeled with a Bolzmann function.
		'''
		return 1.0 / ( 1.0 + exp(-(self.Vm - self.V_halfblocked)/self.k_init) )

	def Isyn(self)->float:
		'''
		Strong voltage dependence.
		'''
		return self.phi_V()*self.postsyn_current_I()



if __name__ == '__main__':
	print('Instantiating quantal release...')
	sqr = SynTr_Quantal_Release(10, 0.5)
	print('Instantiating AMPA receptor...')
	ampar = AMPA_Receptor()
	print('Finding a_norm for AMPAR Double-Exponential...')
	ampar.numerical_find_a_norm(plot_it=True)
	print('Plotting Double-Exponential and Multi-Exponential (with a_norm for Double-Exponential)...')
	t_ms = np.linspace(0, 20, 1000)
	Gampar_dbl = ampar.np_Gsyn_t_pS_dbl(t_ms)
	Gampar_mxh = ampar.np_Gsyn_t_pS_mxh(t_ms)
	ampar.plot_it(t_ms, [ Gampar_dbl, Gampar_mxh ], [ '', 'Double- and Multi-Exponential', ])
	print('Finding a_norm for NMDAR Double-Exponential...')
	nmdar = NMDA_Receptor()
	nmdar.numerical_find_a_norm()
	print('Plotting AMPAR and NMDAR Double-Exponential...')
	t_ms = np.linspace(0, 100, 1000)
	Gampar_dbl = ampar.np_Gsyn_t_pS_dbl(t_ms)
	Gnmdar_dbl = nmdar.np_Gsyn_t_pS_dbl(t_ms)
	nmdar.plot_it(t_ms, [ Gampar_dbl, Gnmdar_dbl ], [ '', 'AMPAR and NMDAR Double-Exponential', ])

	exit(0)