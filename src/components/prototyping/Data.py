# Data.py
# Randal A. Koene, 20231007

'''
Data handling.
'''

import json
from json import JSONEncoder
import numpy as np
import pickle
import gzip

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return { 'nparray': obj.tolist() }
        return JSONEncoder.default(self, obj)

def recreate_nparrays(data:dict)->dict:
	# Detect if the data is { 'nparray': [...] }, if so then convert:
	if len(data)==1:
		for key in data:
			if isinstance(key, str):
				if key=='nparray':
					return np.asarray(data[key])
	# Recursively check any dict in this dict:
	for key in data:
		if isinstance(data[key], dict):
			data[key] = recreate_nparrays(data[key])
	# Other data remains untouched.
	return data

def save_acq_data(data:dict, file:str):
	if file[-3:]=='.gz':
		pkl_data = pickle.dumps(data)
		gzpkl_data = gzip.compress(pkl_data)
		with open(file, 'wb') as f:
			f.write(gzpkl_data)
		return
	# with open(file, 'w') as f:
	# 	json.dump(data, f, cls=NumpyArrayEncoder)
	with open(file, 'wb') as f:
		pickle.dump(data, f)

def load_acq_data(file:str)->dict:
	if file[-3:]=='.gz':
		with open(file, 'rb') as f:
			gzpkl_data = f.read()
		pkl_data = gzip.decompress(gzpkl_data)
		data = pickle.loads(pkl_data)
		return data
	# with open(file, 'r') as f:
	# 	dict_data = json.load(f)
	# return recreate_nparrays(dict_data)
	with open(file, 'rb') as f:
		data = pickle.load(f)
	return data
