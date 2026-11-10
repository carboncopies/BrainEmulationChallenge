#!/usr/bin/env python3
"""Reservoir analysis from an offline viz dump (gen_autonm_labels.save_viz_data schema v1).

Builds per-class conductance matrices (summed g_peak_sum per ordered pre->post pair, nS),
cell types and soma positions. Neuron 'id' in the dump is the NES neuron index, i.e. the
same ID space that BatchSetPrePostStrength / SetSpecificAPTimes use.
"""
import json
import numpy as np

PRINCIPAL, INTERNEURON = 1, 2
AMPA, GABA, NMDA = 1, 2, 3

# Physiological per-receptor peak conductances used by the docs / Netmorph->LIFC conversion.
G_AMPA_PER_SYN_nS = 0.98
G_GABA_PER_SYN_nS = 0.80
G_NMDA_PER_SYN_nS = 0.55  # observed in the dump (0.55 nS per NMDA receptor)


class Reservoir:
    def __init__(self, dump_path):
        with open(dump_path) as f:
            d = json.load(f)
        self.path = dump_path
        self.neurons = d['neurons']
        self.N = len(self.neurons)
        self.types = np.array([n['soma_type'] for n in self.neurons], dtype=int)
        self.pos = np.array([[n['x'], n['y'], n['z']] for n in self.neurons], dtype=float)
        self.pyr = np.where(self.types == PRINCIPAL)[0]
        self.int = np.where(self.types == INTERNEURON)[0]
        N = self.N
        self.G = {AMPA: np.zeros((N, N)), GABA: np.zeros((N, N)), NMDA: np.zeros((N, N))}
        self.W = {AMPA: np.zeros((N, N)), GABA: np.zeros((N, N)), NMDA: np.zeros((N, N))}
        self.NR = {AMPA: np.zeros((N, N), dtype=int), GABA: np.zeros((N, N), dtype=int), NMDA: np.zeros((N, N), dtype=int)}
        for c in d['connections']:
            t = c['type']
            self.G[t][c['pre'], c['post']] += c['g_peak_sum']
            self.W[t][c['pre'], c['post']] = c['weight_sum']  # as-built weight (0.2 uniform)
            self.NR[t][c['pre'], c['post']] += c['num_receptors']

    # Convenience sub-matrices (rows = pre, cols = post), in nS at weight 1.0
    def pyr_pyr_ampa(self):
        return self.G[AMPA][np.ix_(self.pyr, self.pyr)]

    def pyr_pyr_nmda(self):
        return self.G[NMDA][np.ix_(self.pyr, self.pyr)]

    def pyr_int_ampa(self):
        return self.G[AMPA][np.ix_(self.pyr, self.int)]

    def int_pyr_gaba(self):
        return self.G[GABA][np.ix_(self.int, self.pyr)]

    def int_int_gaba(self):
        return self.G[GABA][np.ix_(self.int, self.int)]

    def summary(self):
        A = self.pyr_pyr_ampa()
        nP, nI = len(self.pyr), len(self.int)
        off = ~np.eye(nP, dtype=bool)
        present = A[off] > 0
        PI, IP, II = self.pyr_int_ampa(), self.int_pyr_gaba(), self.int_int_gaba()
        recv_gaba = IP.sum(axis=0)              # total GABA g_peak_sum onto each pyramidal
        recv_ampa_int = PI.sum(axis=0)          # total AMPA onto each interneuron
        per_rec = {}
        for t, name in ((AMPA, 'AMPA'), (GABA, 'GABA'), (NMDA, 'NMDA')):
            m = self.NR[t] > 0
            per_rec[name] = float(np.median(self.G[t][m] / self.NR[t][m])) if m.any() else None
        return {
            'dump': self.path,
            'neurons': self.N, 'pyramidal': nP, 'interneurons': nI,
            'pyr_pyr_ampa': {
                'ordered_pairs_possible': int(off.sum()),
                'pairs_present': int(present.sum()),
                'fraction_present': float(present.mean()),
                'mean_g_peak_sum_existing_nS': float(A[off][present].mean()),
                'max_g_peak_sum_nS': float(A.max()),
                'pairs_ge_6.86nS': int((A[off] >= 6.86).sum()),
                'pairs_ge_27.44nS': int((A[off] >= 27.44).sum()),
                'total_g_peak_sum_nS': float(A.sum()),
                'synapses_total': int(self.NR[AMPA][np.ix_(self.pyr, self.pyr)].sum()),
            },
            'pyr_int_ampa': {'pairs': int((PI > 0).sum()), 'total_nS': float(PI.sum()),
                             'max_pair_nS': float(PI.max()),
                             'interneurons_with_input': int((recv_ampa_int > 0).sum()),
                             'max_total_onto_one_int_nS': float(recv_ampa_int.max()),
                             'ints_ge_7.84nS': int((recv_ampa_int >= 7.84).sum())},
            'int_pyr_gaba': {'pairs': int((IP > 0).sum()), 'total_nS': float(IP.sum()),
                             'max_pair_nS': float(IP.max()),
                             'pyr_with_inhibition': int((recv_gaba > 0).sum()),
                             'max_total_onto_one_pyr_nS': float(recv_gaba.max()),
                             'mean_total_onto_pyr_nS': float(recv_gaba.mean()),
                             'pyr_ge_16nS': int((recv_gaba >= 16).sum()),
                             'pyr_ge_8nS': int((recv_gaba >= 8).sum())},
            'int_int_gaba': {'pairs': int((II > 0).sum()), 'total_nS': float(II.sum())},
            'g_per_receptor_median_nS': per_rec,
            'as_built_weight_unique': sorted(set(np.round(self.W[AMPA][self.W[AMPA] > 0], 3).tolist()
                                                 + np.round(self.W[GABA][self.W[GABA] > 0], 3).tolist())),
        }

    def save_matrices(self, path):
        np.savez_compressed(path, types=self.types, pos=self.pos, pyr=self.pyr, int=self.int,
                            G_AMPA=self.G[AMPA], G_GABA=self.G[GABA], G_NMDA=self.G[NMDA],
                            NR_AMPA=self.NR[AMPA], NR_GABA=self.NR[GABA], NR_NMDA=self.NR[NMDA])


if __name__ == '__main__':
    import sys
    r = Reservoir(sys.argv[1])
    print(json.dumps(r.summary(), indent=1))
