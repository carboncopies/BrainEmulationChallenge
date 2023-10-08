# Electrodes.py
# Randal A. Koene, 20230921

'''
Definitions of simulated electrodes.
'''

import numpy as np
#from .System import System

class Recording_Electrode:
	def __init__(self, specs:dict, system_ref):
		'''
		The characteristics in specs override default characteristics.
		Any that are not defined in specs remain at default values.
		'''
		self.specs = {
			'id': 'electrode_'+str(np.random.rand())[2:5], # Random generated default ID.
			'tip_position': (0, 0, 0),
			'end_position': (0, 0, 5.0),
			'sites': [ (0, 0, 0), ], # A single site at the tip.
			'noise_level': 0,
			'sensitivity_dampening': 2.0,
		}
		self.specs.update(specs)

		self.id = specs['id']
		self.tip_position = np.array(specs['tip_position'])
		self.end_position = np.array(specs['end_position'])
		self.sites = specs['sites']
		self.noise_level = specs['noise_level']
		self.system_ref = system_ref

		self.site_locations_xyz_um = [] # In system coordinate system.
		self.neuron_refs = []
		self.neuron_soma_to_site_distances_squared_um = [] # [ (d_s1n1, d_s1n2, ...), (d_s2n1, d_s2n2, ...), ...]

		self.t_recorded_ms = []	# [ t0, t1, ... ]
		self.E_mV = [] 			# [ [E1(t0), E1(t1), ...], [E2(t0), E2(t1), ...], ...]

		self.init_system_coord_site_locations()
		self.init_neuron_references_and_distances()
		self.init_records()

	def electrode_coords_to_system_coords(self, eloc_ratio:tuple)->np.array:
		# TODO: Fix this to properly use the width dimension of the electrode
		#       as well and produce a proper conversion.
		#       At present, this is using only the z-coord of eloc_ratio as
		#       a position along the center line of the vector between tip
		#       and end.
		'''
		1. Get a vector from tip to end.
		2. Multiply vector coordinates with the ratios given in eloc_ratio.
		3. Add the resulting vector to the tip position.
		'''
		tip_to_end = self.tip_position - self.end_position
		vec_to_add = tip_to_end * eloc_ratio[2]
		sysloc_um = self.tip_position + vec_to_add
		return sysloc_um

	def init_system_coord_site_locations(self):
		for site in self.sites:
			self.site_locations_xyz_um.append(self.electrode_coords_to_system_coords(site))

	def init_neuron_references_and_distances(self):
		# TODO: We could improve efficiency by filtering so that only neurons
		#       close enough are included.
		self.neuron_refs = self.system_ref.get_all_neurons()
		for i in range(len(self.site_locations_xyz_um)):
			site_distances_um = []
			for n in self.neuron_refs:
				soma_xyz_um = np.array(n.get_cell_center())
				dist = np.linalg.norm(soma_xyz_um-self.site_locations_xyz_um[i])
				site_distances_um.append(dist*dist)
			self.neuron_soma_to_site_distances_squared_um.append(site_distances_um)

	def init_records(self):
		for i in range(len(self.sites)):
			self.E_mV.append([])

	def add_noise(self)->float:
		r_pos = np.random.rand() # TODO: More efficient to cache a bunch.
		r = r_pos - 0.5
		noise_mV = r*self.noise_level
		return noise_mV

	def electric_field_potential(self, site_idx:int)->float:
		# TODO: We can do a lot to improve the realism of this calculation
		#       of the effect of overlapping electric fields.
		'''
		Calculate the electric field potential at the electrode site as
		a combination of the effects of nearby neurons.
		'''
		Ei_mV = 0
		site_distances_um = self.neuron_soma_to_site_distances_squared_um[site_idx]
		for n_i in range(len(self.neuron_refs)):
			Vm = self.neuron_refs[n_i].Vm_mV
			if site_distances_um[n_i] <= 1.0:
				Ein_mV = Vm
			else:
				Ein_mV = Vm / site_distances_um[n_i]
			Ei_mV += (Ein_mV/self.specs['sensitivity_dampening'])
		Ei_mV += self.add_noise()
		return Ei_mV

	def record(self, t_ms:float):
		self.t_recorded_ms.append(t_ms)
		for i in range(len(self.site_locations_xyz_um)):
			Ei_mV = self.electric_field_potential(i)
			self.E_mV[i].append(Ei_mV)

	def get_recording(self)->dict:
		data = {}
		data['E'] = self.E_mV
		return data
