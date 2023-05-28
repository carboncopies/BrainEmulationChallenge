#!/usr/bin/env python3
# syn_transmission.py
# Randal A. Koene, 20230507

'''
Basic models of synaptic transmission.
Compare with: Rothman, J.S. and Silver, R.A. (2016),
"Data-Driven Modeling of Synaptic Transmission and Integration",
Prog.Mol.Biol.Transl.Sci.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4748401/
'''

import numpy as np

from prototyping.SynTr_Quantal_Release import SynTr_Quantal_Release
from prototyping.AMPA_Receptor import AMPA_Receptor
from prototyping.NMDA_Receptor import NMDA_Receptor

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
