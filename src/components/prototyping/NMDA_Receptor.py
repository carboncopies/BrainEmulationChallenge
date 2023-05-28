# NMDA_Receptor.py
# Randal A. Koene, 20230507

'''
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4748401/
'''

from math import exp

from prototyping.AMPA_Receptor import AMPA_Receptor

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
			V_halfblocked_init:float=20.0,	# Voltage at which half the NMDAR channels are blocked.
			k_init:float=2.0,				# Slope factor that determines steepness of voltage dependence around V_halfblocked.
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

		self.phi_V = self.phi_V_Bolzmann

	def set_phi_V_type(self, phi_V_type:str):
		if phi_V_type=='Bolzmann':
			self.phi_V = self.phi_V_Bolzmann
		elif phi_V_type=='Woodhull_1':
			self.phi_V = self.phi_V_Woodhull_1
		elif phi_V_type=='Woodhull_2':
			self.phi_V = self.phi_V_Woodhull_2

	def phi_V_Bolzmann(self)->float:
		'''
		Modeled with a Bolzmann function.
		Easy to use, but not directly related to physical aspects of Mg2+ blocking mechanism.
		'''
		return 1.0 / ( 1.0 + exp(-(self.Vm - self.V_halfblocked)/self.k_init) )

	def Phi(self,
			T:float,	# Absolute temperature.
			z=2,		# Valenve of blocking ion (+2 for Mg2+).
		)->float:
		R = 8.31446261815324	# Gas constant (in J/(K*mol)).
		F = 96 485.3321			# Faraday constant (in s*A/mol).
		return z*F / (R*T)

	def k_binding_rate(self,
			Mg2plus_0:float,	# Mg2+ concentration outside membrane.
			K_binding:float,	# Binding constant.
			delta:float,		# Fraction of membrane voltage that Mg2+ experiences at the blocking site.
			V:float,			# Voltage.
			T:float,			# Absolute temperature.
		)->float:
		return Mg2plus_0*K_binding*exp(-delta*self.Phi(T)*V/2)

	def k_unbinding_rate(self,
			K_unbinding:float,	# Unbinding constant.
			delta:float,		# Fraction of membrane voltage that Mg2+ experiences at the blocking site.
			V:float,			# Voltage.
			T:float,			# Absolute temperature.
		)->float:
		return K_unbinding*exp(delta*self.Phi(T)*V/2)

	def phi_V_Woodhull_1(self,
			Mg2plus_0:float,	# Mg2+ concentration outside membrane.
			K_binding:float,	# Binding constant.
			K_unbinding:float,	# Unbinding constant.
			delta:float,		# Fraction of membrane voltage that Mg2+ experiences at the blocking site.
			V:float,			# Voltage.
			T:float,			# Absolute temperature.
		)->float:
		'''
		Modeled with a two-state Woodhull formalism derived from a kinetic model of
		extracellular Mg2+ block. An ion channel is blocked when an ion species (here, Mg2+)
		is bound to a binding site inside the channel, open when the ion species is unbound.
		'''
		k_binding = self.k_binding_rate(Mg2plus_0, K_binding, delta, V, T)
		k_unbinding = self.k_unbinding_rate(K_unbinding, delta, V, T)
		return 1.0 / (1.0 + (k_binding / k_unbinding))

	def phi_V_Woodhull_2(self,
			Mg2plus_0:float,			# Mg2+ concentration outside membrane.
			K_dissociation_0mV:float,	# Dissociation constant at 0 mV, equal to K_unbinding/K_binding.
			delta:float,				# Fraction of membrane voltage that Mg2+ experiences at the blocking site.
			V:float,					# Voltage.
			T:float,					# Absolute temperature.
		)->float:
		'''
		Modeled with a two-state Woodhull formalism derived from a kinetic model of
		extracellular Mg2+ block. An ion channel is blocked when an ion species (here, Mg2+)
		is bound to a binding site inside the channel, open when the ion species is unbound.
		K_dissociation_0mV quantifies the strength or affinity of Mg2+ binding and delta
		quantifies the location of the Mg2+ binding site within the channel.
		'''
		K_d = K_dissociation_0mV*exp(delta*self.Phi(T)*V) # K_d is a dissociation constant.
		return 1.0 / (1.0 + (Mg2plus_0 / K_d))

	def Isyn(self)->float:
		'''
		Strong voltage dependence.
		'''
		return self.phi_V()*self.postsyn_current_I()
