# BSNeuron.py
# Randal A. Koene, 20230624

'''
Definitions of ball-and-stick neuron types.
'''

import numpy as np

from .common.Spatial import PlotInfo
from .BG_API import BGNES_BS_compartment_create, BGNES_connection_staple_create, BGNES_DAC_set_output_list
from .Geometry import Sphere, Cylinder
from .common.Neuron import Neuron

# def dblexp(amp:float, tau_rise:float, tau_decay:float, tdiff:float)->float:
#     if tdiff<0: return 0
#     return amp*( -np.exp(-tdiff/tau_rise) + np.exp(-tdiff/tau_decay) )

class BS_Neuron(Neuron):
    '''
    A ball-and-stick neuron with 3D physical geometry and integrate-and-fire
    function.
    '''
    def __init__(self, id:str, soma:Sphere, axon:Cylinder):
        super().__init__(id)


        self.Vm_mV = -60.0      # Membrane potential
        self.Vrest_mV = -60.0   # Resting membrane potential
        self.Vact_mV = -50.0    # Action potential firing threshold

        self.Vahp_mV = -20.0
        self.tau_AHP_ms = 30.0

        self.tau_PSPr = 5.0     # All BS receptors are identical
        self.tau_PSPd = 25.0
        self.vPSP = 20.0

        self.morphology = {
            'soma': soma,
            'axon': axon,
        }
        # Create soma compartment:
        self.soma_id = BGNES_BS_compartment_create(
            ShapeID=soma.id,
            MembranePotential_mV=self.Vm_mV,
            RestingPotential_mV=self.Vrest_mV,
            SpikeThreshold_mV=self.Vact_mV,
            DecayTime_ms=self.tau_AHP_ms,
            AfterHyperpolarizationAmplitude_mV=self.Vahp_mV,
        )
        # Create axon compartment:
        self.axon_id = BGNES_BS_compartment_create(
            ShapeID=axon.id,
            MembranePotential_mV=self.Vm_mV,
            RestingPotential_mV=self.Vrest_mV,
            SpikeThreshold_mV=self.Vact_mV,
            DecayTime_ms=self.tau_AHP_ms,
            AfterHyperpolarizationAmplitude_mV=self.Vahp_mV,
        )
        self.staple_id = BGNES_connection_staple_create(self.soma_id, self.axon_id)
        self.receptors = []
        self.t_directstim_ms = []
        self.patch_id = None

        # self.t_ms = 0
        # self._has_spiked = False
        # self.in_absref = False
        # self.t_act_ms = []
        # self._dt_act_ms = None

        # self.t_recorded_ms = []
        # self.Vm_recorded = []

    def attach_direct_stim(self, t_ms:float):
        if self.patch_id is None:
            self.patch_id = BGNES_DAC_create(
                DestinationCompartmentID=self.soma_id,
                ClampLocation_nm=[0,0,0])
        self.t_directstim_ms.append(t_ms)

    def register_DAC_data_list(self):
        if self.patch_id is not None:
            DAC_settings = [ (0, self.Vrest_mV) ]
            for t_stim in self.t_directstim_ms:
                DAC_settings.append( (t_stim, self.Vact_mV+10.0 ) )
                DAC_settings.append( (t_stim+5.0, self.Vrest_mV ) )
        BGNES_DAC_set_output_list(self.patch_id, DAC_settings)

    def show(self, pltinfo=None):
        if pltinfo is None: pltinfo = PlotInfo('Neuron %s.' % str(self.id))
        for cellcomp in self.morphology:
            self.morphology[cellcomp].show(pltinfo)

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
        if recording: self.record(t_ms)

    def detect_threshold(self, t_ms:float):
        '''
        Compare Vm with Vact.
        '''
        if self.in_absref: return
        if self.Vm_mV >= self.Vact_mV:
            self.t_act_ms.append(t_ms)

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

        # 3. Remember the update time.
        self.t_ms = t_ms

    def get_recording(self)->dict:
        return {
            'Vm': self.Vm_recorded,
        }
