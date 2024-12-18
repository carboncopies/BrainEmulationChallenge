# BSNeuron.py
# Randal A. Koene, 20230624

'''
Definitions of ball-and-stick neuron types.
'''

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

from .common.Spatial import VecBox, PlotInfo
from .Geometry import Sphere, Cylinder
from .SignalFunctions import dblexp, convolve_1d
from .common.Neuron import Neuron
from .Calcium_Imaging import fluorescent_voxel
from .BS_Morphology import BS_Morphology

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

        self.tau_spont_mean_stdev_ms = (0, 0) # 0 means no spontaneous activity
        self.t_spont_next = -1
        self.dt_spont_dist = None

        self.morphology = {
            'soma': soma,
            'axon': axon,
        }
        self.receptors = []

        self.t_ms = 0
        self._has_spiked = False
        self.in_absref = False
        self.t_act_ms = []
        self._dt_act_ms = None

        self.FIFO = None
        self.convolved_FIFO = None
        self.Ca_samples = []
        self.t_Ca_samples = []

        self.t_recorded_ms = []
        self.Vm_recorded = []

    def get_cell_center(self)->tuple:
        return self.morphology['soma'].center_um

    def get_voxels(self, voxel_um:float, subvolume:VecBox, adjacent_radius_um:float, include_components:list)->list:
        '''
        Based on the neuron morphology and voxel specifications, return
        a list of fluorescent_voxel objects intersecting and adjacent to
        the neuron.
        Virtual voxel locations are based on a Euclidean grid with a
        spacing determined by the voxel_um resolution.
        The adjacent_radius_um is interpreted as any virtual voxel
        locations where the corresponding voxel would be within that
        distance from a voxel included in the list.
        The include_components list contains the morphology key strings
        of components that are to be included in the voxel search
        (e.g. in the case of calcium imaging, this can depend on the
        type of GCaMP used).
        To avoid duplicates, and to ensure that intersecting voxels are
        not also provided as adjacent voxels, a unique dict is created
        with keys that indicate a virtual voxel location according to
        three integer indices that are multiplied with voxel_um.
        The steps of the process for each piece of morphology are:
        1. Traverse the morphology in step sizes of voxel_um.
        2. At each step, determine the corresponding voxel location,
           as well as adjacent voxels within the adjacent_radius_um.
        3. Generate corresponding location indices, generate corresponding key.
        4. Check if the voxel already exists in the dict. Intersecting
           voxels have priority over adjacent voxels.
        5. When done, convert the dict values into a list and return that.
        The subvolume definition is used to skip generating candidate voxels
        for morphology components that are entirely outside the subvolume.
        '''
        # TODO: Do the full process. (For now, as a test, we just return
        #       a voxel for the soma center, see Geometry:Sphere.get_voxels().)
        voxel_dict = {}
        # Find intersecting voxels:
        for component in self.morphology:
            if component in include_components:
                #print('DEBUG(BS_Neuron.get_voxels) == Voxel component: '+str(component))
                voxel_dict.update(self.morphology[component].get_voxels(voxel_um, subvolume, self))
        #print('DEBUG(BS_Neuron.get_voxels) == Component voxels: '+str(len(voxel_dict)))
        # Add adjacent voxels:
        voxel_list = list(voxel_dict.values())
        for voxel in voxel_list:
            adjacent_voxels_dict = voxel.get_adjacent_dict(adjacent_radius_um)
            #print('DEBUG(BS_Neuron.get_voxels) == Candidate adjacents: '+str(len(adjacent_voxels_dict)))
            for voxel_indices in adjacent_voxels_dict:
                if voxel_indices not in voxel_dict:
                    voxel_dict[voxel_indices] = adjacent_voxels_dict[voxel_indices]
        #print('DEBUG(BS_Neuron.get_voxels) == Component+Adjacent voxels: '+str(len(voxel_dict)))
        return list(voxel_dict.values())

    def set_FIFO(self, FIFO_ms:float, dt_ms:float):
        fifosize = int(FIFO_ms//dt_ms) + 1
        self.FIFO = np.zeros(fifosize) #np.ones(fifosize)*self.Vrest_mV

    def attach_direct_stim(self, t_ms:float):
        self.t_directstim_ms.append(t_ms)

    def set_spontaneous_activity(self, mean_stdev:tuple):
        self.tau_spont_mean_stdev_ms = mean_stdev
        mu = self.tau_spont_mean_stdev_ms[0]
        sigma = self.tau_spont_mean_stdev_ms[1]
        a, b = 0, 2*mu
        self.dt_spont_dist = stats.truncnorm((a - mu) / sigma, (b - mu) / sigma, loc=mu, scale=sigma)

    def to_dict(self)->dict:
        morphology = {}
        for morph in self.morphology:
            morphology[morph] = self.morphology[morph].to_dict()
        receptors = []
        for receptor in self.receptors:
            receptors.append( (receptor[0].id, receptor[1]) )
        cell_data = {
            'id': self.id,
            'Vm_mV': self.Vm_mV,
            'Vrest_mV': self.Vrest_mV,
            'Vact_mV': self.Vact_mV,

            'Vahp_mV': self.Vahp_mV,
            'tau_AHP_ms': self.tau_AHP_ms,

            'tau_PSPr': self.tau_PSPr,
            'tau_PSPd': self.tau_PSPd,
            'vPSP': self.vPSP,

            'tau_spont_mean_stdev_ms': self.tau_spont_mean_stdev_ms,
            't_spont_next': self.t_spont_next, # TODO: Should this be here?
            'dt_spont_dist': self.dt_spont_dist, # TODO: Should this be here?

            'morphology': morphology,
            'receptors': receptors,
            't_directstim_ms': self.t_directstim_ms,
        }
        return cell_data

    def from_dict(self, cell_data:dict):
        self.id = cell_data['id']
        self.Vm_mV = cell_data['Vm_mV']
        self.Vrest_mV = cell_data['Vrest_mV']
        self.Vact_mV = cell_data['Vact_mV']

        self.Vahp_mV = cell_data['Vahp_mV']
        self.tau_AHP_ms = cell_data['tau_AHP_ms']

        self.tau_PSPr = cell_data['tau_PSPr']
        self.tau_PSPd = cell_data['tau_PSPd']
        self.vPSP = cell_data['vPSP']

        self.tau_spont_mean_stdev_ms = cell_data['tau_spont_mean_stdev_ms']
        self.t_spont_next = cell_data['t_spont_next'] # TODO: Should this be here?
        self.dt_spont_dist = cell_data['dt_spont_dist'] # TODO: Should this be here?

        self.t_directstim_ms = cell_data['t_directstim_ms']
        self.receptors = cell_data['receptors'] # This needs follow-up conversion to references in System.from_dict().
        self.morphology = {}
        for morph in cell_data['morphology']:
            self.morphology[morph] = BS_Morphology(cell_data['morphology'][morph])

    def show(self, pltinfo=None, linewidth=0.5):
        if pltinfo is None: pltinfo = PlotInfo('Neuron %s.' % str(self.id))
        for cellcomp in self.morphology:
            self.morphology[cellcomp].show(pltinfo, linewidth=linewidth)

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

    def update_convolved_FIFO(self, kernel:np.array):
        # We have to flip the signal FIFO, because the most recent is in [0].
        # We need this, because the kernel has a specific time order.
        # Alternatively, when we prepare the kernel we can flip it and
        # remember to view [0] as most recent in the convolution result.
        #v_convolved = convolve_1d(signal=self.FIFO[::-1], kernel=(1/len(kernel))*kernel[::-1])
        #self.convolved_FIFO = np.array(v_convolved)

        Ca_signal = -1.0*self.FIFO[::-1]
        Ca_signal[Ca_signal < 0.0] = 0
        self.convolved_FIFO = np.array(convolve_1d(signal=Ca_signal, kernel=kernel)) #[::-1]))
        self.Ca_samples.append(self.convolved_FIFO[10]+1.0) # A bit arbitrary to be taking the 10th value
        self.t_Ca_samples.append(self.t_ms)

        # if self.t_ms > 80.0:
        #     #tmaxsteps = max([ len(self.convolved_FIFO), len(self.FIFO), len(kernel) ])
        #     tmaxsteps = max([ len(self.convolved_FIFO), len(Ca_signal), len(kernel) ])
        #     t_ms = [ self.t_ms-(tstep*1.0) for tstep in range(tmaxsteps) ]
        #     fig = plt.figure(figsize=(4,4))
        #     plt.title('Fluorescence convolution')
        #     #plt.plot(t_ms[:len(self.FIFO)], (1/60)*self.FIFO, color='r')
        #     plt.plot(t_ms[:len(Ca_signal)], Ca_signal[::-1], color='r')
        #     #plt.plot(t_ms[:len(kernel)], kernel, color='g')
        #     plt.plot(t_ms[:len(self.convolved_FIFO)], self.convolved_FIFO[::-1], color='b')
        #     plt.show()

    def get_recording(self)->dict:
        return {
            'Vm': self.Vm_recorded,
        }
