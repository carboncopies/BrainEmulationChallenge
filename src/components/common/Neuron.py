# Neuron.py
# Randal A. Koene, 20230621

'''
Definitions of neuron types.
'''

class Neuron:
    def __init__(self, id:str):
        self.id = id
        self.t_directstim_ms = []

