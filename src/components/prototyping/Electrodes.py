# Electrodes.py
# Randal A. Koene, 20230921

'''
Definitions of simulated electrodes.
'''

class Recording_Electrode:
	def __init__(self, specs:dict):
		self.id = specs['id']
		self.tip_position = specs['tip_position']
		self.sites = specs['sites']
