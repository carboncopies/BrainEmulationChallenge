# IFneuron.py
#
# This is a simplified extract of BS_Neuron.py.
# It is intended to be copy-pasted into short Python scripts
# such as those used in the Data Science internship on
# functional validation metrics.
# Use this to build small test examples of networks producing
# the sort of clean/noisy activity data that might be expected
# from either our ground-truth example systems or attempted
# emulations thereof.

# To use the IFneuron class below:
#
# - Make as many instances of IFneuron objects as there are neurons, each with a unique id.
# - Set up connections between neurons (see below).
# - Set up the stimulation protocol for the experiment (see below).
# - Run the experiment at a sensible update step size, e.g. 1 ms per step
#   by calling IFneuron.update(). Note the parameters. You have to
#   include the time (t_ms) of this step in the experiment, and you
#   need to indicate if the updated membrane potential should be
#   recorded.
#   Note that spike times are automatically collected in IFneuron.t_act_ms.
#   If membrane potential is being recorded then the times of recordings
#   are stored in IFneuron.t_recorded_ms and the corresponding membrane
#   potentials in IFneuron.Vm_recorded.
#
# ==> Setting up connections between neurons:
#
# The IFneuron.receptors list will contain tuples of the form:
#
#   (neuron_ref, weight)
#
# Where neuron_ref is a reference to an IFneuron object and
# weight is a connection weighting such as 1.0.
# The neuron_ref is a source of synaptic input, i.e. the
# receptors list is listing all of the neurons from which the
# current neuron object will be receiving input.
#
# ==> Setting up the stimulation protocol:
#
# Direct stimulation assumes that each specific neuron can receive
# input that will force it to fire (spike) at precise times
# during the simulation. (E.g. as via patch-clamping.)
#
# The stimulation times are contained in the list at IFneuron.t_directstim_ms.
# You can set that variable or use the IFneuron.attach_direct_stim
# function to do so.

import numpy as np
import scipy.stats as stats

def dblexp(amp:float, tau_rise:float, tau_decay:float, tdiff:float)->float:
    if tdiff<0: return 0
    return amp*( -np.exp(-tdiff/tau_rise) + np.exp(-tdiff/tau_decay) )

class IFneuron:
    '''
    A simple integrate-and-fire neuron.
    '''
    def __init__(self, id:str):
        self.id = id
        self.t_directstim_ms = []
        self.Vm_mV = -60.0      # Membrane potential
        self.Vrest_mV = -60.0   # Resting membrane potential
        self.Vact_mV = -50.0    # Action potential firing threshold

        self.Vahp_mV = -20.0
        self.tau_AHP_ms = 30.0

        self.tau_PSPr = 5.0     # All receptors are identical
        self.tau_PSPd = 25.0
        self.vPSP = 20.0

        self.tau_spont_mean_stdev_ms = (0, 0) # 0 means no spontaneous activity
        self.t_spont_next = -1
        self.dt_spont_dist = None

        self.receptors = []

        self.t_ms = 0
        self._has_spiked = False
        self.in_absref = False
        self.t_act_ms = []
        self._dt_act_ms = None

        self.t_recorded_ms = []
        self.Vm_recorded = []

    def attach_direct_stim(self, t_ms:float):
        self.t_directstim_ms.append(t_ms)

    def set_spontaneous_activity(self, mean_stdev:tuple):
        self.tau_spont_mean_stdev_ms = mean_stdev
        mu = self.tau_spont_mean_stdev_ms[0]
        sigma = self.tau_spont_mean_stdev_ms[1]
        a, b = 0, 2*mu
        self.dt_spont_dist = stats.truncnorm((a - mu) / sigma, (b - mu) / sigma, loc=mu, scale=sigma)

    def record(self, t_ms:float):
        self.t_recorded_ms.append(t_ms)
        self.Vm_recorded.append(self.Vm_mV)

    def has_spiked(self)->bool:
        self._has_spiked = len(self.t_act_ms)>0
        return self._has_spiked

    def dt_act_ms(self, t_ms:float)->float:
        if self._has_spiked:
            self._dt_act_ms = t_ms - self.t_act_ms[-1]
            return self._dt_act_ms
        return 99999999.9

    def vSpike_t(self, t_ms:float)->float:
        if not self._has_spiked: return 0.0
        self.in_absref = self._dt_act_ms<=1.0
        if self.in_absref: return 60.0 # Within absolute refractory period.
        return 0.0

    def vAHP_t(self, t_ms:float)->float:
        if not self._has_spiked: return 0.0
        if self.in_absref: return 0.0
        return self.Vahp_mV * np.exp(-self._dt_act_ms/self.tau_AHP_ms)

    def vPSP_t(self, t_ms:float)->float:
        vPSPt = 0.0
        for receptor in self.receptors:
            src_cell = receptor[0]
            weight = receptor[1]
            if src_cell.has_spiked():
                dtPSP = src_cell.dt_act_ms(t_ms)
                vPSPt += dblexp(weight*self.vPSP, self.tau_PSPr, self.tau_PSPd, dtPSP)
        return vPSPt

    def update_Vm(self, t_ms:float, recording:bool):
        '''
        Vm = Vrest + vSpike(t) + vAHP(t) + vPSP(t)
        Compare Vm with Vact.
        '''
        # 1. Prepare data used by vSpike_t and vAHP_t:
        if self.has_spiked(): self.dt_act_ms(t_ms)
        # 2. Calculate contributions:
        vSpike_t = self.vSpike_t(t_ms)
        vAHP_t = self.vAHP_t(t_ms)
        vPSP_t = self.vPSP_t(t_ms)
        # 3. Calculate membrane potential:
        self.Vm_mV = self.Vrest_mV + vSpike_t + vAHP_t + vPSP_t
        if self.FIFO is not None:
            self.FIFO = np.roll(self.FIFO,1) # Rolls to the right, [0] available to be replaced.
            self.FIFO[0] = self.Vm_mV-self.Vrest_mV
        if recording: self.record(t_ms)

    def detect_threshold(self, t_ms:float):
        '''
        Compare Vm with Vact.
        '''
        if self.in_absref: return
        if self.Vm_mV >= self.Vact_mV:
            self.t_act_ms.append(t_ms)

    def spontaneous_activity(self, t_ms:float):
        '''
        Possible spontaneous activity.
        '''
        if self.in_absref: return
        if self.tau_spont_mean_stdev_ms[0] == 0: return
        if t_ms >= self.t_spont_next:
            if self.t_spont_next >= 0:
                self.t_act_ms.append(t_ms)
            dt_spont = self.dt_spont_dist.rvs(1)[0]
            self.t_spont_next = t_ms + dt_spont

    def update(self, t_ms:float, recording:bool):
        tdiff_ms = t_ms - self.t_ms
        if tdiff_ms<0: return

        # 1. Has there been a directed stimulation?
        if len(self.t_directstim_ms)>0:
            if self.t_directstim_ms[0]<=t_ms:
                tfire_ms = self.t_directstim_ms.pop(0)
                self.t_act_ms.append(tfire_ms)

        # 2. Update variables.
        self.update_Vm(t_ms, recording)
        self.detect_threshold(t_ms)
        self.spontaneous_activity(t_ms)

        # 3. Remember the update time.
        self.t_ms = t_ms

    def get_recording(self)->dict:
        return {
            'Vm': self.Vm_recorded,
        }
