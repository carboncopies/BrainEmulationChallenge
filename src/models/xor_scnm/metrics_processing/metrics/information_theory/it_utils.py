#metrics/information_theory/it_utils

import math

def H(binary_list):
    n = len(binary_list)
    if n == 0:
        return 0.0
    
    p1 = sum(binary_list) / n
    p0 = 1 - p1
    
    entropy = 0.0
    if p0 > 0:
        entropy -= p0 * math.log2(p0)
    if p1 > 0:
        entropy -= p1 * math.log2(p1)
    
    return entropy

def joint_entropy_from_states(state_ids, n_states, n_samples):
    counts = np.bincount(state_ids, minlength=n_states)
    probs  = counts / n_samples
    probs  = probs[probs > 0]  
    
    return -np.sum(probs * np.log2(probs))

    