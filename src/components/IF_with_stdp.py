import numpy as np
import matplotlib.pyplot as plt
import time

start_time = time.time()

# Simulation parameters
dt = 1.0  # ms
#T = 950
T = 4000
t_samples = np.arange(0, T, dt)
n_steps = len(t_samples)

burst_drive = False # default: False
compact_burst_driver = True # default: True
compact_driver_spikes = 10
long_driver_spikes = 200

Cm_option = True # default: True
use_exponential_Euler = True # default: True

quantal_trigger = False # input just enough to trigger a spike

include_inhibition = True # Otherwise, no input from IntIn
if burst_drive:
    include_inhibition = False

long_regular_input = True # Otherwise a single input from PyrIn and one from IntIn
simulate_recurrent_inhibition = True # but from only a single interneuron!

with_explicit_voltage_gating = True # default: True
with_adp = True # Applies to pyramidal neurons
with_stdp = True # Applies to AMPA receptors onto pyramidal neurons
clipping_AHP_and_ADP = True # default: True
with_dynamic_threshold_floor = True # default: True
with_fatigue_threshold = True # default: False

classical_IF = False # default: False
if classical_IF:
    use_exponential_Euler = False

# reset-after works fairly well right now
# reset-onset is just about as good
# no-reset now means remember Vm before AP, which looks usable
spike_option = 'no-reset' # 'reset-onset', 'reset-after', 'no-reset'

class Netmorph_Syn:
    def __init__(self, n_from, n_to, receptor, PSD_area_um2, g_rec_peak, tau_rise, tau_decay, hilloc_distance, velocity, syn_delay, voltage_gated):
        self.n_from = n_from
        self.n_to = n_to
        self.receptor = receptor
        self.quantity = int(PSD_area_um2 / 0.0086)
        self.voltage_gated = voltage_gated
        self.g_rec_peak = g_rec_peak # nS (nano Siemens)
        if self.voltage_gated:
            # Adjusted to achieve desired g_peak with voltage-gated Mg2++ block modulation
            self.g_rec_peak *= 5.0
        self.tau_rise = tau_rise
        self.tau_decay = tau_decay
        self.hilloc_distance = hilloc_distance # um
        self.velocity = velocity # m/s
        self.synaptic_delay = syn_delay # ms
        self.onset_delay = self.synaptic_delay + ((self.hilloc_distance*1e-6)/self.velocity)


def compute_normalization(tau_rise, tau_decay):
    if tau_rise == tau_decay:
        raise ValueError("tau_rise must be different from tau_decay for normalization.")
    t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * np.log(tau_decay / tau_rise)
    norm = np.exp(-t_peak / tau_decay) - np.exp(-t_peak / tau_rise)
    return norm

def g_norm(t, spike_times, tau_rise, tau_decay, norm, onset_delay, spike_dt_delta=1000, history_delta=0.001):
    """
    Compute total synaptic conductance at time t from all spikes.
    The history_delta enables a reduction of computational load by
    breaking out of the sum when the contributions become remote
    and inconsequential. Defaults to 0.001. Only applies when
    spike_dt > spike_dt_delta, so that the short-circuit is not
    triggered during onset of a current. Defaults to 1000 ms.
    Set history_delta=0 and spike_dt_delta=inf to deactivate this.

    Also, we could use something like precalculating kernels for
    all contributors with dt bins and then a convolution, which
    would ultimately save expensive calculations.
    """
    t -= onset_delay
    history_delta *= norm
    gnorm = 0
    for ts in reversed(spike_times):
        spike_dt = t - ts
        if spike_dt >= 0:
            g_norm_contribution = np.exp(-spike_dt / tau_decay) - np.exp(-spike_dt / tau_rise)
            if spike_dt>spike_dt_delta and g_norm_contribution < history_delta:
                return gnorm / norm
            gnorm += g_norm_contribution
    return gnorm / norm

class PreSyn:
    def __init__(self,
        receptor,
        source,
        tau_rise,
        tau_decay,
        E,
        g_peak,
        weight,
        onset_delay,
        STDP_type, # one of 'Hebbian', 'Anti-Hebbian', or 'None'
        A_pos,
        A_neg,
        tau_pos,
        tau_neg,
        voltage_gated
        ):
        self.source = source # neuron reference
        self.receptor = receptor # receptor type string

        self.tau_rise = tau_rise # ms
        self.tau_decay = tau_decay # ms
        self.E = E # mV
        self.g_peak = g_peak # Also considered g_peak_max (weight=1.0) for cumulative effect of multiple high-frequency PSPs
        self.weight = weight
        self.onset_delay = onset_delay # ms
        self.voltage_gated = voltage_gated
        self.g = 0.0

        self.STDP_type = STDP_type
        self.A_pos = A_pos
        self.A_neg = A_neg
        self.tau_pos = tau_pos
        self.tau_neg = tau_neg

        self.norm = compute_normalization(self.tau_rise, self.tau_decay) # Pre-calculate normalization
        print('g_peak_%s: %s' % (self.receptor, str(self.g_peak)))
        print('norm_%s: %s' % (self.receptor, str(self.norm)))

        self.g_k = np.zeros(n_steps) # In the C++ implementation, we probably don't record these

    # Effect of voltage-gated Mg2+ block.
    def B_NMDA(self, V, Mg=1.0):
        gamma = 0.33  # per mM
        beta = 0.062  # per mV
        return 1 / (1 + gamma * Mg * np.exp(-beta * V))

    def update(self, i, t, Vm):
        syn_times = self.source.t_postspikes
        if self.voltage_gated:
            self.g = min(self.g_peak, self.B_NMDA(Vm) * self.weight * self.g_peak * g_norm(t, syn_times, self.tau_rise, self.tau_decay, self.norm, self.onset_delay))
        else:
            self.g = min(self.g_peak, self.weight * self.g_peak * g_norm(t, syn_times, self.tau_rise, self.tau_decay, self.norm, self.onset_delay))
        self.g_k[i] = self.g

    def stdp_update(self, t):
        """
        Computes the synaptic weight change using an exponential STDP rule.
        Returns:
        - dw: float or np.ndarray
            Change in synaptic weight(s).
        """
        if len(self.source.t_postspikes)>0:
            t_pre = self.source.t_postspikes[-1]
        if self.STDP_type == 'None':
            return 0
        if self.STDP_type == 'Anti-Hebbian':
            dt_spikes = t_pre - t
        else:
            dt_spikes = t - t_pre
        if dt_spikes > 0:
            dw = self.A_pos * np.exp(-dt_spikes / self.tau_pos)
        else:
            dw = -self.A_neg * np.exp(dt_spikes / self.tau_neg)
        self.weight += dw
        if self.weight > 1.0:
            self.weight = 1.0
        if self.weight < 0.0:
            self.weight = 0.0
        return dw


class IF_neuron:
    def __init__(self, neuron_id, force_spikes, presyn):

        self.id = neuron_id

        self.force_spikes = force_spikes

        # Connections
        self.presyn = presyn # references to presynaptic neurons

        # Neuron parameters
        self.V_rest = -70  # mV
        self.V_th = -50    # spike threshold mV (base value, see threshold adaptation)
        self.V_reset = -55 # -65  # mV after spike
        self.R_m = 100/1000 # in GΩ, 100-300 MΩ pyramidal
        self.C_m = 100 # 100-300 pF pyramidal
        self.tau_m = self.R_m*self.C_m # ms
        print('tau_m = %f ms' % self.tau_m)
        self.g_L = 1/self.R_m # nS
        print('g_L = %f nS' % self.g_L)
        self.refractory_period = 2  # ms
        self.V_spike_depol = 30 # mV - voltage at which to depict spike
        self.reset_done = True # Only used for 'reset-after'

        # Fast after-hyperpolarization
        self.E_AHP = -90 # mV reversal potential (used for both slow and fast AHP)
        self.tau_rise_fAHP, self.tau_decay_fAHP = 2.5, 30 # 1-5 ms, 20-50 ms typical in pyramidal neurons
        self.g_peak_fAHP = 3.0  # 1-5 nS
        self.g_peak_fAHP_max = 5 # 3-6 nS in pyramidal neurons
        self.Kd_fAHP = 1.5 # 1.5-3 nS half-activation constant for sigmoidal AHP saturation model
        self.g_fAHP = 0.0

        # Slow after-hyperpolarization
        self.tau_rise_sAHP, self.tau_decay_sAHP = 30, 300 # 20-50 ms, 150-1000 ms typical in pyramidal neurons
        self.g_peak_sAHP = 1.0 # 0.5-3 nS (was 0.5)
        self.g_peak_sAHP_max = 2.0 # 0.5-2.5 nS in pyramidal neurons (was 0.5)
        self.Kd_sAHP = 0.3 # 0.3-1 nS half-activation constant for sigmoidal AHP saturation model
        self.g_sAHP = 0.0

        if clipping_AHP_and_ADP:
            self.AHP_saturation_model = 'clip' # 'clip' or sigmoidal saturation model
        else:
            self.AHP_saturation_model = 'sigmoidal'

        # Hard-cap fatigue threshold
        self.fatigue = 0.0 # grows with spiking, decays slowly
        self.fatigue_threshold = 300 # number of spikes in a burst
        self.tau_fatigue_recovery = 1000 # ms

        # After-depolarization
        self.E_ADP = -20 # mV reversal potential
        self.tau_rise_ADP, self.tau_decay_ADP = 20, 200
        if with_adp:
            self.g_peak_ADP = 0.3  # nS
        else:
            self.g_peak_ADP = 0.0
        self.ADP_saturation_multiplier = 2.0 # typically between 2-3 times
        self.g_peak_ADP_max = self.g_peak_ADP*self.ADP_saturation_multiplier
        self.tau_recovery_ADP = 300 # for resource availability mode, 200-600 ms for slow ADP recovery times
        self.ADP_depletion = 0.3 # 0.2-0.4 per spike, ADP resource availability model
        self.a_ADP = 1.0
        self.g_ADP = 0.0

        if clipping_AHP_and_ADP:
            self.ADP_saturation_model = 'clip' # 'clip' or resource availability model
        else:
            self.ADP_saturation_model = 'resource'

        # Parameters used for adaptive threshold modeling of sodium inactivation
        self.h_spike = 1.0
        self.dh_spike = 0.2
        self.tau_h = 50 # 50 - 200 ms
        self.dV_th = 10 # mV

        self.V_th_floor = self.V_th # Dynamic threshold floor
        self.delta_floor_per_spike = 1.0 # mV
        self.tau_floor_decay = 500 # ms

        # Initialize variables
        self.Vm = self.V_rest
        self.last_spike_idx = -np.inf
        self.t_last_spike = -1000
        self.t_postspikes = []

        # Recordings
        self.samples = {
            'fAHP': np.zeros(n_steps), # In C++, we probably will not record this.
            'sAHP': np.zeros(n_steps), # In C++, we probably will not record this.
            'ADP': np.zeros(n_steps), # In C++, we probably will not record this.
            'Vm': np.zeros(n_steps),
            'dV': np.zeros(n_steps), # In C++, we probably will not record this.
            'V_th_adaptive': np.zeros(n_steps), # In C++, we probably will not record this.
        }
        self.spike_train = np.zeros(n_steps, dtype=bool) # Also referenced during calculations

        # Pre-calculate normalizations
        self.norm_fAHP = compute_normalization(self.tau_rise_fAHP, self.tau_decay_fAHP)
        self.norm_sAHP = compute_normalization(self.tau_rise_sAHP, self.tau_decay_sAHP)
        self.norm_ADP = compute_normalization(self.tau_rise_ADP, self.tau_decay_ADP)
        print('norm_fAHP: '+str(self.norm_fAHP))
        print('norm_sAHP: '+str(self.norm_sAHP))
        print('norm_ADP: '+str(self.norm_ADP))


    def set_presyn(self, presyn):
        self.presyn = presyn

    def spike(self, i, t):
        # Spike logging
        self.spike_train[i] = True
        self.last_spike_idx = i
        self.t_last_spike = t
        self.t_postspikes.append(self.t_last_spike)

        # Membrane potential reset
        if classical_IF:
            self.Vm = self.V_reset
        else:
            if spike_option == 'no-reset':
                self.V_reset = self.Vm # Remember value before AP (this might be weird)
            self.Vm = self.V_spike_depol
        self.reset_done = False # only used for 'reset-after' and 'no-reset'

        # Threshold effects
        # a. nonlinear hard-cap
        if with_fatigue_threshold:
            self.fatigue += 1
        # b. Adaptive threshold models sodium channel inactivation
        self.h_spike -= self.dh_spike # *** What happens if this is allowed to go below 0?
        # c. Dynamic threshold floor
        if with_dynamic_threshold_floor:
            self.V_th_floor += self.delta_floor_per_spike

        # ADP saturation
        if self.ADP_saturation_model != 'clip': # ADP resource availability model
            self.a_ADP -= self.ADP_depletion

        # STDP
        if with_stdp:
            for p in self.presyn:
                p.stdp_update(t)

    def check_spiking(self, i, t, V_th_adaptive):
        if len(self.force_spikes) > 0:
            if t >= self.force_spikes[0]:
                self.spike(i, self.force_spikes[0])
                self.force_spikes.pop(0)
                return

        if with_fatigue_threshold and (self.fatigue > self.fatigue_threshold):
            return

        if self.Vm >= V_th_adaptive:
            self.spike(i, t)

    def update_conductances(self, i, t):

        # Update PSP conductances.

        for p in self.presyn:
            p.update(i, t, self.Vm)

        # Update fAHP, sAHP, ADP conductances.

        g_fAHP_linear = self.g_peak_fAHP * g_norm(t, self.t_postspikes, self.tau_rise_fAHP, self.tau_decay_fAHP, self.norm_fAHP, 0)
        if self.AHP_saturation_model == 'clip':
            self.g_fAHP = min(g_fAHP_linear, self.g_peak_fAHP_max)
        else:
            self.g_fAHP = self.g_peak_fAHP_max * (g_fAHP_linear / (g_fAHP_linear + self.Kd_fAHP))

        g_sAHP_linear = self.g_peak_sAHP * g_norm(t, self.t_postspikes, self.tau_rise_sAHP, self.tau_decay_sAHP, self.norm_sAHP, 0)
        if self.AHP_saturation_model == 'clip':
            self.g_sAHP = min(g_sAHP_linear, self.g_peak_sAHP_max)
        else:
            self.g_sAHP = self.g_peak_sAHP_max * (g_sAHP_linear / (g_sAHP_linear + self.Kd_sAHP))

        g_ADP_linear = self.g_peak_ADP * g_norm(t, self.t_postspikes, self.tau_rise_ADP, self.tau_decay_ADP, self.norm_ADP, 0)
        if self.ADP_saturation_model == 'clip':
            self.g_ADP = min(g_ADP_linear, self.g_peak_ADP_max)
        else:
            self.a_ADP = self.a_ADP + (1 - self.a_ADP) * dt / self.tau_recovery_ADP
            self.a_ADP = max(0.0, min(1.0, self.a_ADP)) # clamp [0,1]
            self.g_ADP = self.a_ADP * g_ADP_linear

    def update_currents(self, i):
        I = (
            self.g_fAHP * (self.Vm - self.E_AHP) +
            self.g_sAHP * (self.Vm - self.E_AHP) +
            self.g_ADP * (self.Vm - self.E_ADP)
        )

        for p in self.presyn:
            I += p.g * (self.Vm - p.E)

        return I

    def update_membrane_potential_forward_Euler(self, I):
        dV = (-(self.Vm - self.V_rest) + self.R_m * (-I)) * dt / self.tau_m
        self.samples['dV'][i] = dV
        self.Vm = self.Vm + dV
        return dV

    def update_membrane_potential_exponential_Euler_Rm(self, i):
        # (Exponential Euler tau_m/Rm:) Membrane potential update.
        tau_eff = self.tau_m / (1 + self.R_m * (self.g_fAHP + self.g_sAHP + self.g_ADP + sum([p.g for p in self.presyn])))
        # V_inf is in mV, because these are all nS*mV / nS
        V_inf = (self.g_fAHP * self.E_AHP + self.g_sAHP * self.E_AHP + self.g_ADP * self.E_ADP + sum([p.g * p.E for p in self.presyn]) + (1 / self.R_m) * self.V_rest) / \
            (self.g_fAHP + self.g_sAHP + self.g_ADP + sum([p.g for p in self.presyn]) + (1 / self.R_m))
        self.Vm = V_inf + (self.Vm - V_inf) * np.exp(-dt / tau_eff)

    def update_membrane_potential_exponential_Euler_Cm(self, i):
        # (Exponential Euler tau_eff/Cm:) Membrane potential update.
        g_total = self.g_L + self.g_fAHP + self.g_sAHP + self.g_ADP + sum([p.g for p in self.presyn]) # nS
        E_total = (self.g_L * self.V_rest
            + self.g_fAHP * self.E_AHP
            + self.g_sAHP * self.E_AHP
            + self.g_ADP * self.E_ADP
            + sum([p.g * p.E for p in self.presyn])
            ) / g_total # mV
        tau_eff = self.C_m / g_total # pF/nS=ms (or pF*GΩ=ms)
        self.Vm = E_total + (self.Vm - E_total) * np.exp(-dt / tau_eff)

    def update_adaptive_threshold(self):
        self.h_spike += dt * (1 - self.h_spike)/self.tau_h
        if with_dynamic_threshold_floor:
            self.V_th_floor -= dt * (self.V_th_floor - self.V_th) / self.tau_floor_decay
        V_th_adaptive = max(
            self.V_th + self.dV_th * (1 - self.h_spike),
            self.V_th_floor
        )
        self.samples['V_th_adaptive'][i] = V_th_adaptive
        return V_th_adaptive

    def update_with_classical_reset_clamp(self, i, t):
        I = self.update_currents(i)

        if t < (self.t_last_spike+self.refractory_period):
            self.Vm = self.V_reset
            return

        dV = self.update_membrane_potential_forward_Euler(I)

        V_th_adaptive = self.update_adaptive_threshold()

        # Check possible spiking:
        self.check_spiking(i, t, V_th_adaptive)

    def update_with_reset_options(self, i, t):
        # (Option:) Spike onset drives membrane potential below threshold.

        if spike_option == 'reset-onset':
            if (self.last_spike_idx+1) == i:
                self.Vm = self.V_reset

        if use_exponential_Euler:
            if not Cm_option:

                self.update_membrane_potential_exponential_Euler_Rm(i)

            else:

                self.update_membrane_potential_exponential_Euler_Cm(i)

            dV = 0 # just for the 'reset-after' option

        else:
            I = self.update_currents(i)

            dV = self.update_membrane_potential_forward_Euler(I)

        V_th_adaptive = self.update_adaptive_threshold()

        if t >= (self.t_last_spike+self.refractory_period):

            # (Option:) Drive membrane potential below threshold after absolute refractory period.

            if spike_option != 'reset-onset' and not self.reset_done:
                self.Vm = self.V_reset + dV # *** not specifically adapted to exponential Euler
                self.reset_done = True

            # Check possible spiking:
            self.check_spiking(i, t, V_th_adaptive)

    def update(self, i, t):
        # Hard-cap nonlinear spiking fatigue threshold.
        if with_fatigue_threshold:
            self.fatigue -= dt / self.tau_fatigue_recovery
            self.fatigue = max(self.fatigue, 0.0)

        self.update_conductances(i, t)

        if classical_IF:
            self.update_with_classical_reset_clamp(i, t)
        else:
            self.update_with_reset_options(i, t)

    def record(self, i):
        self.samples['Vm'][i] = self.Vm
        self.samples['fAHP'][i] = self.g_fAHP
        self.samples['sAHP'][i] = self.g_sAHP
        self.samples['ADP'][i] = self.g_ADP


initial_weights_and_Erev = {
    'AMPA': [ 0.5, 0 ],
    'NMDA': [ 0.5, 0 ],
    'GABA': [ 0.5, -70 ],
}
if quantal_trigger:
    initial_weights = { # postsyn: { presyn: weight }
        'PyrOut': { 'PyrIn': 0.3, 'IntIn': 0.3 }
    }

receptor_STDP = {
    'AMPA': [ 0.01, 0.01, 20.0, 20.0, 'Hebbian' ],
    'NMDA': [ 0,0,0,0, 'None'],
    'GABA': [ 0,0,0,0, 'None'], # This circuit does not include (Anti-Hebbian) GABA updates.
}

# Neurons as per Netmorph data
neurons = {}
#PyrIn = IF_neuron(neuron_id='PyrIn', force_spikes=[100, 200, 300, 400], presyn=[])

if burst_drive:
    if compact_burst_driver:
        t_in = np.array([(t+1)*5 for t in range(compact_driver_spikes)])
    else:
        t_in = np.array([(t+1)*10 for t in range(long_driver_spikes)])
else:
    if long_regular_input:
        t_in = np.array([(t+1)*100 for t in range(int(0.75*T/100))])
    else:
        t_in = np.array([100])

PyrIn = IF_neuron(neuron_id='PyrIn', force_spikes=t_in.tolist(), presyn=[])
neurons[PyrIn.id] = PyrIn

if include_inhibition:
    if simulate_recurrent_inhibition:
        IntIn = IF_neuron(neuron_id='IntIn', force_spikes=(t_in+3).tolist(), presyn=[])
    else:
        IntIn = IF_neuron(neuron_id='IntIn', force_spikes=(t_in+150).tolist(), presyn=[])
else:
    IntIn = IF_neuron(neuron_id='IntIn', force_spikes=[], presyn=[])
IntIn.g_peak_sAHP = 0.0 # no slow AHP for interneurons
IntIn.g_peak_ADP = 0.0 # no ADP for interneurons
neurons[IntIn.id] = IntIn

PyrOut = IF_neuron(neuron_id='PyrOut', force_spikes=[], presyn=[])
neurons[PyrOut.id] = PyrOut

# Synapses by receptor type as per Netmorph data
# Making plenty of synapses, so that we can reach the typical 10-50 coactive synapses needed to drive from rest to firing.
if with_explicit_voltage_gating:
    NMDA_g_rec_peak = 50e-3 # 50 pS intended peak at average open receptor gated fraction
else:
    NMDA_g_rec_peak = 50e-3/2 # Adjusted to account for the absence of voltage-gated modulation
nmsyn_PyrIn_PyrOut_AMPA = [Netmorph_Syn(PyrIn, PyrOut, 'AMPA', 0.83*60*0.0086, 20e-3, tau_rise=0.5, tau_decay=3, hilloc_distance=100, velocity=1, syn_delay=1.0, voltage_gated=False) for i in range(21)]
nmsyn_PyrIn_PyrOut_NMDA = [Netmorph_Syn(PyrIn, PyrOut, 'NMDA', 0.17*60*0.0086, NMDA_g_rec_peak, tau_rise=2, tau_decay=100, hilloc_distance=100, velocity=1, syn_delay=1.0, voltage_gated=with_explicit_voltage_gating) for i in range(21)]
nmsyn_IntIn_PyrOut_AMPA = [Netmorph_Syn(IntIn, PyrOut, 'GABA', 10*0.0086, 80e-3, tau_rise=0.5, tau_decay=10, hilloc_distance=100, velocity=1, syn_delay=1.0, voltage_gated=False) for i in range(21)] # maybe g_peak here should be 30e-3 instead of 80e-3
nmsyn = nmsyn_PyrIn_PyrOut_AMPA + nmsyn_PyrIn_PyrOut_NMDA + nmsyn_IntIn_PyrOut_AMPA


# We have to reformat this as follows:
# 1. Find all the Netmorph synapses that target the same neuron.
# 2. Collect them by receptor type.
# 3. Subdivide by source neuron.
# 4. Within each receptor and subdivision, determine total g_peak and median onset delay
# 5. Create PreSyn objects for each neuron

# Steps 1-3
nmsyn_by_neuron = {}
# E.g
# {
#       'PyrOut': {
#                   'AMPA': {
#                             'PyrIn': [ Netmorph_Syn(), Netmorph_Syn() ]
#                           },
#                   'GABA': {
#                             'IntIn': [ Netmorph_Syn() ]
#                           }
#                 }   
# }
for n_id in neurons:
    n_nmsyn = {} # collected by receptor type
    for s in nmsyn:
        target = s.n_to
        if target == neurons[n_id]:
            if s.receptor not in n_nmsyn:
                n_nmsyn[s.receptor] = {}
            if s.n_from.id not in n_nmsyn[s.receptor]:
                n_nmsyn[s.receptor][s.n_from.id] = []
            n_nmsyn[s.receptor][s.n_from.id].append(s)
    nmsyn_by_neuron[n_id] = n_nmsyn

# Steps 4-5
presyn_by_neuron = {} # collected by neuron by receptor type and by source
for n_id in neurons:
    n_nmsyn = nmsyn_by_neuron[n_id]
    for receptor in n_nmsyn:
        for source_id in n_nmsyn[receptor]:
            receptor_onset_delay = []
            receptor_tau_rise = []
            receptor_tau_decay = []
            total_g_peak = 0
            voltage_gated = False
            for s in n_nmsyn[receptor][source_id]:
                g_peak = s.quantity * s.g_rec_peak
                total_g_peak += g_peak
                if s.voltage_gated:
                    voltage_gated = True
                receptor_onset_delay.append(s.onset_delay)
                receptor_tau_rise.append(s.tau_rise)
                receptor_tau_decay.append(s.tau_decay)
            median_onset_delay = np.median(np.array(receptor_onset_delay))
            median_tau_rise = np.median(np.array(receptor_tau_rise))
            median_tau_decay = np.median(np.array(receptor_tau_decay))
            if n_id not in presyn_by_neuron:
                presyn_by_neuron[n_id] = []
            if quantal_trigger:
                weight = initial_weights[n_id][source_id]
            else:
                weight = initial_weights_and_Erev[receptor][0]
            presyn_by_neuron[n_id].append(PreSyn(
                receptor,
                neurons[source_id],
                tau_rise=median_tau_rise,
                tau_decay=median_tau_decay,
                E=initial_weights_and_Erev[receptor][1],
                g_peak=total_g_peak,
                weight=weight,
                onset_delay=median_onset_delay,
                STDP_type=receptor_STDP[receptor][4],
                A_pos=receptor_STDP[receptor][0],
                A_neg=receptor_STDP[receptor][1],
                tau_pos=receptor_STDP[receptor][2],
                tau_neg=receptor_STDP[receptor][3],
                voltage_gated=voltage_gated
                ))
            if n_id == 'PyrOut' and receptor == 'AMPA' and source_id == 'PyrIn':
                SynRef = presyn_by_neuron[n_id][-1]

# When not building this from Netmorph, but simply by using AddLIFCReceptor
# the composition of abstract functional receptor data is as follows for
# each unique combination of Pre-Post-ReceptorType:
#
#   g_peak = sum(g_peak_i)
#   tau_rise = median(tau_rise_i)
#   tau_decay = median(tau_decay_i)
#   weight = sum(weight_i*g_peak_i)/g_peak
#   onset_delay = median(onset_delay_i)

# Now, we can set up the accumulated connections for each neuron

for n_id in presyn_by_neuron:
    neurons[n_id].set_presyn(presyn_by_neuron[n_id])

print('Number of PyrIn Forced spikes: %d' % len(PyrIn.force_spikes))
print('Number of IntIn Forced spikes: %d' % len(IntIn.force_spikes))

# Simulation loop
t = 0
synref_w = np.zeros(n_steps)
for i in range(0, n_steps): # 1 is the necessary start here, because we need to use V[0] as V[i-1] in update

    PyrIn.update(i, t)
    PyrIn.record(i)

    IntIn.update(i, t)
    IntIn.record(i)

    PyrOut.update(i, t)
    PyrOut.record(i)

    synref_w[i] = SynRef.weight

    t += dt

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Simulation time: {elapsed_time:.4f} seconds")

# Plotting
fig, axs = plt.subplots(5, 1, figsize=(12, 12), sharex=True) # was 2 and (12, 7)

axs[0].plot(t_samples, PyrOut.samples['Vm'], label="PyrOut Membrane Voltage (mV)")
if not use_exponential_Euler:
    axs[0].plot(t_samples, PyrOut.samples['dV'], label="PyrOut dV (mV)")
axs[0].scatter(t_samples[PyrOut.spike_train], PyrOut.samples['Vm'][PyrOut.spike_train], color='red', label='Spikes', zorder=5)
axs[0].plot(t_samples, PyrOut.samples['V_th_adaptive'], color='gray', linestyle='--', label="Adaptive Threshold (mV)")
axs[0].set_ylabel("Voltage (mV)")
axs[0].legend()
axs[0].grid(True)

for p in PyrOut.presyn:
    axs[1].plot(t_samples, p.g_k, label='g_'+p.receptor, alpha=0.8)

axs[1].plot(t_samples, PyrOut.samples['fAHP'], label="g_fAHP", linestyle='--', alpha=0.8)
axs[1].plot(t_samples, PyrOut.samples['sAHP'], label="g_sAHP", linestyle='--', alpha=0.8)
axs[1].plot(t_samples, PyrOut.samples['ADP'], label="g_ADP", linestyle='--', alpha=0.8)
axs[1].set_ylabel("Conductance (nS)")
axs[1].set_xlabel("Time (ms)")
axs[1].legend()
axs[1].grid(True)

axs[2].plot(t_samples, synref_w, label="PyrIn to PyrOut Weight")
axs[2].set_ylabel("Weight")
axs[2].legend()
axs[2].grid(True)

axs[3].plot(t_samples, PyrIn.samples['Vm'], label="PyrIn Membrane Voltage (mV)")
axs[3].axhline(PyrIn.V_th, color='gray', linestyle='--', label='Threshold')
axs[3].set_ylabel("Voltage (mV)")
axs[3].legend()
axs[3].grid(True)

axs[4].plot(t_samples, IntIn.samples['Vm'], label="IntIn Membrane Voltage (mV)")
axs[4].axhline(IntIn.V_th, color='gray', linestyle='--', label='Threshold')
axs[4].set_ylabel("Voltage (mV)")
axs[4].legend()
axs[4].grid(True)

plt.suptitle("IF Neuron: Membrane Response with Normalized Synaptic Kernels")
plt.tight_layout()
plt.show()
