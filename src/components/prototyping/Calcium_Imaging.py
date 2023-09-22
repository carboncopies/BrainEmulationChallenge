# Calcium_Imaging.py
# Randal A. Koene, 20230921

'''
Definitions of simulated calcium imaging.
'''

class Calcium_Imaging:
	def __init__(self, specs:dict):
		self.id = specs['id']
		self.fluorescing_neurons = specs['fluorescing_neurons']
		self.calcium_indicator = specs['calcium_indicator']
		self.indicator_rise_ms = specs['indicator_rise_ms']
		self.indicator_interval_ms = specs['indicator_interval_ms']
		self.microscope_lensfront_position_um = specs['microscope_lensfront_position_um']
		self.microscope_rear_position_um = specs['microscope_rear_position_um']
