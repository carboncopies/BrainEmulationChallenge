# Calcium_Imaging.py
# Randal A. Koene, 20230921

'''
Definitions of simulated calcium imaging.
'''

#from .System import System

class Calcium_Imaging:
	def __init__(self, specs:dict, system_ref):
		self.id = specs['id']
		self.fluorescing_neurons = specs['fluorescing_neurons']
		self.calcium_indicator = specs['calcium_indicator']
		self.indicator_rise_ms = specs['indicator_rise_ms']
		self.indicator_interval_ms = specs['indicator_interval_ms']
		self.microscope_lensfront_position_um = specs['microscope_lensfront_position_um']
		self.microscope_rear_position_um = specs['microscope_rear_position_um']
		self.system_ref = system_ref

		self.t_recorded_ms = []
		self.images = []

	def record(self, t_ms:float):
		self.t_recorded_ms.append(t_ms)
		# TODO: Generate actual images for the fluorescence.
		self.images.append(None)

	def get_recording(self)->dict:
		data = {}
		data[self.calcium_indicator] = self.images
		return data
