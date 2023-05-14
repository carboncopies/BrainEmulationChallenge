# NMDA_Receptor.py
# Randal A. Koene, 20230507

'''
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
'''

from math import exp

from AMPA_Receptor import AMPA_Receptor

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