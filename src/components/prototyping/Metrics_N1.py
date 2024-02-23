#!/usr/bin/env python3
# Metrics_N1.py
# Randal A. Koene, 20231102

'''
Methods with which to apply validation metrics for the
success criterion:
N-1 Reconstruction of neuronal circuits through system identification
and tuning of properties is sufficiently accurate.
'''

from .System import System
import numpy as np
import networkx as nx
import netrd


class Metrics_N1:
    def __init__(self, emulation:System, kgt:System):
        self.emulation = emulation
        self.kgt = kgt

    def build_connectivity_matrix(self, system):
        all_neurons = system.get_all_neurons()

        # Create a dictionary to map neuron IDs to matrix indices
        neuron_id_to_index = {neuron.id: index for index, neuron in enumerate(all_neurons)}

        # Initialize the connectivity matrix with zeros
        num_neurons = len(all_neurons)
        connectivity_matrix = [[0.0] * num_neurons for _ in range(num_neurons)]

        # Update the matrix based on connections
        for neuron in all_neurons:
            neuron_index = neuron_id_to_index[neuron.id]

            for receptor, weight in neuron.receptors:
                receptor_index = neuron_id_to_index[receptor.id]
                connectivity_matrix[neuron_index][receptor_index] = weight

        return connectivity_matrix

    def validate_accurate_system_identification(self):
        print('Validating accurate system identification...')
        # TODO: Given that this is first of all intended to be used
        #       in the standardized WBE challenge, where the KGT
        #       is (at least initially) in-silico, it is possible to
        #       explicitly compare relevant aspects of circuit
        #       architecture identification, e.g. number of neurons,
        #       connectivity matrix (with possible transposes),
        #       types of neurons, their morphology, synapses, ion
        #       channels.

        emulation_num_neurons = len(self.emulation.get_all_neurons())
        kgt_num_neurons = len(self.kgt.get_all_neurons())

        num_neurons_difference = abs(emulation_num_neurons - kgt_num_neurons)
        percentage_difference = (num_neurons_difference / kgt_num_neurons) * 100

        # get connectivity matrix
        connectivity_matrix_kgt = self.build_connectivity_matrix(self.kgt)
        connectivity_matrix_emulation = self.build_connectivity_matrix(self.emulation)

        # # do jaccard similarity calculation never mind this is for one graph and the nodes inside it
        # set_kgt = set(np.argwhere(connectivity_matrix_kgt == 1))
        # set_emulation = set(np.argwhere(connectivity_matrix_emulation == 1))
        # intersection = len(set_kgt.intersection(set_emulation))
        # union = len(set_kgt.union(set_emulation))

        # jaccard_result = intersection / union

        # G_KGT = nx.DiGraph(connectivity_matrix_kgt)
        # G_Emulation = nx.DiGraph(connectivity_matrix_emulation)

        # Create a directed graph
        G_KGT = nx.DiGraph()

        # Add nodes to the graph
        num_nodes = len(connectivity_matrix_kgt)
        G_KGT.add_nodes_from(range(num_nodes))

        # Add edges to the graph based on the non-zero entries in the connectivity matrix
        for i in range(num_nodes):
            for j in range(num_nodes):
                weight = connectivity_matrix_kgt[i][j]
                if weight != 0.0:
                    G_KGT.add_edge(i, j, weight=weight)

        G_Emulation = nx.DiGraph()

        # Add nodes to the graph
        num_nodes = len(connectivity_matrix_emulation)
        G_Emulation.add_nodes_from(range(num_nodes))

        # Add edges to the graph based on the non-zero entries in the connectivity matrix
        for i in range(num_nodes):
            for j in range(num_nodes):
                weight = connectivity_matrix_emulation[i][j]
                if weight != 0.0:
                    G_Emulation.add_edge(i, j, weight=weight)


        edit_distance_result = nx.graph_edit_distance(G_KGT, G_Emulation)

        # NetRD library metrics

        # dist_obj = QuantumJSD()
        # quantumJSD_obj = netrd.distance.QuantumJSD()
        # # distance = dist_obj.dist(G1, G2)
        # quantumJSD_result = quantumJSD_obj.dist(G_KGT, G_Emulation)

        # deltacon_obj = netrd.distance.DeltaCon()
        # deltcacon_result = deltacon_obj.dist(G_KGT, G_Emulation)

        jaccard_obj = netrd.distance.JaccardDistance()
        jaccard_result = jaccard_obj.dist(G_KGT, G_Emulation)

        if G_KGT.number_of_nodes() == G_Emulation.number_of_nodes():
            quantumJSD_obj = netrd.distance.QuantumJSD()
            quantumJSD_result = quantumJSD_obj.dist(G_KGT, G_Emulation)
            print(f"QuantumJSD: {quantumJSD_result}")



        #when nodes are the same vs when nodes are different


        print(f"Emulation Num Neurons: {emulation_num_neurons}")
        print(f"KGT Num Neurons: {kgt_num_neurons}")
        print(f"Absolute Difference: {num_neurons_difference}")
        print(f"Percentage Difference: {percentage_difference}")
        print(f"Edit Distance: {edit_distance_result}")
        print(f"Jaccard: {jaccard_result}")





    def validate_accurate_tuning(self):
        print('Validating accurate tuning...')

    def validate(self):
        self.validate_accurate_system_identification()
        self.validate_accurate_tuning()

if __name__ == '__main__':

    print('Test demonstration of N-1 metric.')

    kgt = None
    emulation = kgt

    metrics = Metrics_N1(emulation, kgt)
    metrics.validate()

    print('Done')
