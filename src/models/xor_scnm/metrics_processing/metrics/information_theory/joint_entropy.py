#metrics/ information_theory/joint_entropy


def run(gt_data, sub_data, cfg, tmap, meta, truth_table):
        """
    Computes joint entropy of the spiking network state for GT and SUB.

    Joint entropy H(X1, X2, ..., Xn) measures the unpredictability of the
    entire network state simultaneously — treating all spiking neurons as a
    single joint random variable at each timestep.

    Each timestep produces a binary state vector (one bit per spiking neuron).
    This vector is converted to an integer state ID, counted across all
    timesteps, and used to estimate the joint probability distribution.

    Returns
    gt_J : float
        Joint entropy of GT network in bits.
    sub_J : float
        Joint entropy of SUB network in bits.

    Variables (GT side — SUB is identical but uses sub_data):
    gt_neurons : list[str]
        Labels of neurons that actually spiked in gt_data. Derived at
        runtime — not read from config — so it reflects actual activity.
    n_spiking_gt : int
        Number of spiking neurons in GT. Determines state space size.
    n_states_gt : int
        Total possible joint states = 2^n_spiking_gt.
        E.g. 8 neurons → 256 possible states (00000000 to 11111111).
    n_samples_gt : int
        Number of timesteps in gt_data. Used as denominator for probability
        estimation inside joint_entropy_from_states().
    spike_cols_gt : list[str]
        Spike column names for GT spiking neurons e.g. ["E_spike", "Int_A_spike"].
        Used to extract the binary spike matrix from gt_data.
    gt_matrix : np.ndarray, shape (n_samples_gt, n_spiking_gt)
        Binary matrix — each row is the network spike state at one timestep.
        Row i contains 0/1 for each spiking neuron at timestep i.
    powers_gt : np.ndarray, shape (n_spiking_gt,)
        Powers of 2 in descending order: [2^(n-1), 2^(n-2), ..., 2, 1].
        Used to convert each binary row to a unique decimal integer.
        E.g. for 8 neurons: [128, 64, 32, 16, 8, 4, 2, 1].
    state_ids_gt : np.ndarray, shape (n_samples_gt,)
        Integer state ID for each timestep — result of gt_matrix @ powers_gt.
        Each value is between 0 and n_states_gt - 1.
        E.g. [0, 1, 0, 1, 1, 0, 0, 1] → 89.
    gt_J : float
        Joint entropy computed from state_ids_gt via joint_entropy_from_states().
    """
    spike_cols_gt = [f"{n}_spike" for n in gt_neurons]
    spike_cols_sub = [f"{n}_spike" for n in sub_neurons]


    gt_neurons  = get_spiking_neurons(cfg, gt_data)
    sub_neurons = get_spiking_neurons(cfg,sub_data)

    n_spiking_gt = len(gt_neurons)
    n_spiking_sub = len(sub_neurons)

    n_states_gt = 2 ** n_spiking_gt
    n_states_sub  = 2 ** n_spiking_sub


    n_samples_gt  = len(gt_data)
    n_samples_sub = len(sub_data)

    n_samples_min = min(n_samples_gt, n_samples_sub)

    if n_samples < 10 * n_states_gt:
        print(f"Joint entropy may be unreliable: {n_samples} samples for {n_states} possible states. \n
        Bias correction strongly recommended.")
    else:
        gt_matrix  = gt_data[spike_cols].to_numpy()
        sub_matrix = sub_data[spike_cols].to_numpy()

        powers_gt = 2 ** np.arange(n_spiking_gt - 1, -1, -1)
        powers_sub = 2 ** np.arange(n_spiking_sub - 1, -1, -1)

        state_ids_gt = gt_matrix @ powers_gt
        state_ids_sub = sub_matrix @ powers_sub

        gt_J = joint_entropy_from_states(gt_states,  n_states, n_samples)
        sub_J = joint_entropy_from_states(sub_states, n_states, n_samples)

        return gt_J, sub_J

def report(gt_J, sub_J):
    print("Joint Entropy: ")
    print(f" GT  : {gt_J:.4f} bits")
    print(f" SUB : {sub_J:.4f} bits")
    print(f" Diff: {gt_J - sub_J:.4f} bits")




