# AMPA_Receptor.py
# Randal A. Koene, 20230507

'''
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4748401/
'''

import matplotlib.pyplot as plt
from math import exp
import numpy as np

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