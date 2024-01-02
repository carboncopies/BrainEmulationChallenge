# Calcium_Imaging.py
# Randal A. Koene, 20230921

'''
Definitions of simulated calcium imaging.
See this article about fluorescence microscopy: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4711767/

Calcium imaging in neurons: https://www.cell.com/neuron/fulltext/S0896-6273(12)00172-9?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0896627312001729%3Fshowall%3Dtrue

Note that to achieve results similar to confocal microscopy
we need to set up very thin subvolumes and image at multiple depths.
See: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6961134/

And see Light Sheet Fluorescent Microscopy: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3201139/
And: https://www.youtube.com/watch?v=vKHQudCKVGc
Keep in mind the difference between in-vivo light sheet imaging and 3D
light sheet microscopy for cleared samples.

TODO:
- Lightsheet of a single sheet should return images only for the sheet plane.
- Non-lightsheet should include some blurring where out of focus, cones could
  be used but may not be ideal.
- Lightsheet 3D should probably include a delay for the scanning of successive
  depths, if at all possible in-vivo.
'''

import matplotlib.pyplot as plt
import numpy as np

from .SignalFunctions import dblexp, delayed_pulse
from .Spatial import PlotInfo, VecBox, point_is_within_box, plot_voxel
from .Geometry import fluorescent_voxel
from .common.Neuron import Neuron

def voxels_within_bounds(candidate_voxels:list, subvolume:VecBox)->list:
    visible_voxels = []
    print('Checking subvolume bounds...')
    for voxel in candidate_voxels:
        if point_is_within_box(voxel.xyz, subvolume):
            visible_voxels.append(voxel)
    return visible_voxels

class Calcium_Imaging:
    def __init__(self, specs:dict, system_ref, pars):
        '''
        The characteristics in specs override default characteristics.
        Any that are not defined in specs remain at default values.
        '''
        self.specs = {
            'id': 'calcium_'+str(np.random.rand())[2:5], # Random generated default ID.
            'fluorescing_neurons': system_ref.get_all_neuron_IDs(), # All neurons show up in calcium imaging.
            'calcium_indicator': 'jGCaMP8', # Fast sensitive GCaMP (Zhang et al., 2023).
            'indicator_rise_ms': 2.0,
            'indicator_decay_ms': 40.0,
            'indicator_interval_ms': 20.0, # Max. spike rate trackable 50 Hz.
            'imaged_subvolume': VecBox(
                    center=np.array([0, 0, 0]),
                    half=np.array([5.0, 5.0, 2.0]),
                    dx=np.array([1.0, 0.0, 0.0]),
                    dy=np.array([0.0, 1.0, 0.0]),
                    dz=np.array([0.0, 0.0, 1.0]), # Positive dz indicates most visible top surface.
                ),
            #'microscope_lensfront_position_um': (0.0, 20.0, 0.0),
            #'microscope_rear_position_um': (0.0, 40.0, 0.0),
            'voxelspace_side_px': 30,
            'imaging_interval_ms': 30.0,
            'generate_during_sim': True,
        }
        self.specs.update(specs)

        self.id = specs['id']
        self.fluorescing_neurons = specs['fluorescing_neurons']
        self.calcium_indicator = specs['calcium_indicator']
        self.indicator_rise_ms = specs['indicator_rise_ms']
        self.indicator_decay_ms = specs['indicator_decay_ms']
        self.indicator_interval_ms = specs['indicator_interval_ms']
        #self.microscope_lensfront_position_um = specs['microscope_lensfront_position_um']
        #self.microscope_rear_position_um = specs['microscope_rear_position_um']
        self.system_ref = system_ref
        self.show = pars.show

        self.neuron_refs = system_ref.get_neurons_by_IDs(self.fluorescing_neurons)

        self.voxelspace = []

        self.fluorescence_kernel = None
        self.max_pixel_contributions = 0

        self.t_recorded_ms = []
        self.image_dims_px = None
        self.image_t = None
        self.images = []
        self.num_samples = 0

        self.voxel_um = self.get_voxel_size_um()
        self.include_components = self.get_visible_components_list()
        self.set_image_sizes()
        self.instantiate_voxel_space(pars=pars)
        self.initialize_depth_dimming()
        self.initialize_projection_circles()
        self.initialize_fluorescence_kernel()
        self.initialize_fluorescing_neurons_FIFOs()

    def get_voxel_size_um(self)->float:
        '''
        Determine voxel size by using voxelspace_side_px together with the
        3D extremities of the space in which objects in the System are
        located.
        '''
        # TODO: Do this later if it makes sense, as this might not be the
        #       sensible way to set resolution. For now, let's just fake
        #       this...
        return 0.1

    def get_visible_components_list(self)->list:
        if self.calcium_indicator=='jGCaMP8':
            return ['soma', 'axon', ]
        elif self.calcium_indicator=='synGCaMP6f':
            return ['soma', 'axon', 'synapse']
        else:
            return ['soma', ]

    def set_image_sizes(self):
        x_px = int((2*self.specs['imaged_subvolume'].half[0])//self.voxel_um)
        y_px = int((2*self.specs['imaged_subvolume'].half[1])//self.voxel_um)
        self.image_dims_px = (x_px, y_px)

    def instantiate_voxel_space(self, pars):
        '''
        Traverse morphology of fluorescing neurons in the system.
        For each component, determine all of the "voxels" intersected
        and adjacent voxels. Instantiate those as voxel objects.
        '''
        candidate_voxels = []
        for neuron in self.neuron_refs:
            add_candidate_voxels = neuron.get_voxels(
                voxel_um=self.voxel_um,
                subvolume=self.specs['imaged_subvolume'],
                adjacent_radius_um=0.1,
                include_components=self.include_components)
            #print('DEBUG(Calcium_Imaging.instantiate_voxel_space) == Neuron %s has %d candidate voxels.' % (neuron.id, len(add_candidate_voxels)))
            candidate_voxels += add_candidate_voxels
        if pars.show['voxels']:
            self.show_voxels(
                savefolder=pars.savefolder,
                voxelfile='Ca-candidate-voxels.'+pars.figext,
                voxelspace=candidate_voxels,
                show_subvolume=True)
        self.voxelspace = voxels_within_bounds(candidate_voxels, self.specs['imaged_subvolume'])
        print('Voxel space contains %d fluorescing voxels.' % len(self.voxelspace))

    def initialize_depth_dimming(self):
        '''
        For each voxel in self.voxelspace, determine a depth dimming value
        based on its relative position between the top surface and the
        bottom surface of the subvolume.
        '''
        for voxel in self.voxelspace:
            voxel.set_depth_dimming(self.specs['imaged_subvolume'])

    def initialize_projection_circles(self):
        '''
        For each voxel in self.voxelspace, find a corresponding circle of
        2D pixels in the imaging plane based on the intersection of its
        sphere of luminance with that plane. The radius of the sphere is
        given by the maximum penetration depth, i.e. the thickness of
        the visible subvolume. Voxels at that distance will affect only
        the pixel directly above them.
        Voxels closer to the surface... (hmm, this may not work as an out of focus
        blurring approach, use something simpler...)
        See: https://math.stackexchange.com/questions/943383/determine-circle-of-intersection-of-plane-and-sphere
        Steps:
        1. Find radius r of the circle.
        2. Find center c of the circle.
        3. Find all pixels within the circle.
        '''
        # TODO: See the TODO at the top of this file!
        #       Right now, simplifying this by only projecting vertically
        #       to pixels directly above the voxel. This is as if one could
        #       carry out lightsheet microscopy at multiple depths up to
        #       some depth and return a summed image (a bit weird, perhaps).
        #       In other words, here we simply project to a pixel at the
        #       x,y location.
        pixel_contributions = np.zeros(self.image_dims_px, dtype=int)
        for voxel in self.voxelspace:
            voxel.set_image_pixels(self.specs['imaged_subvolume'], self.image_dims_px, pixel_contributions)
        self.max_pixel_contributions = pixel_contributions.max()            
        # print('List of voxel locations and corresponding 2D image pixels:')
        # for voxel in self.voxelspace:
        #     print('Voxel at %s projecting to %s.' % (str(voxel.xyz), str(voxel.image_pixels)))

    def initialize_fluorescence_kernel(self):
        kernel = []
        t = 0
        kernel_ms = 2.0*(self.indicator_rise_ms+self.indicator_decay_ms)
        pulse_samples = self.indicator_decay_ms//self.system_ref.dt_ms
        amp = 1/(pulse_samples)
        while t < kernel_ms:
            #k = dblexp(1.0, self.indicator_rise_ms, self.indicator_decay_ms, t)
            k = delayed_pulse(amp=amp, tau_delay=self.indicator_rise_ms, tau_pulse=self.indicator_decay_ms, tdiff=t)
            kernel.append(k)
            t += self.system_ref.dt_ms
        self.fluorescence_kernel = np.array(kernel)

    def initialize_fluorescing_neurons_FIFOs(self):
        for neuron in self.neuron_refs:
            # TODO: Set different FIFO sizes for different GCaMP types.
            neuron.set_FIFO(4.0*(self.indicator_rise_ms+self.indicator_decay_ms), self.system_ref.dt_ms)

    def record(self, t_ms:float):
        if len(self.t_recorded_ms)>0:
            if (t_ms - self.t_recorded_ms[-1])<self.specs['imaging_interval_ms']: return

        self.t_recorded_ms.append(t_ms)
        for neuron in self.neuron_refs:
            neuron.update_convolved_FIFO(self.fluorescence_kernel)
        self.num_samples += 1
        if self.specs['generate_during_sim']:
            self.image_t = np.zeros(self.image_dims_px)
            for voxel in self.voxelspace:
                voxel.record_fluorescence(self.image_t)
            self.images.append(self.image_t.astype(np.uint8))

    def record_aposteriori(self):
        '''
        Generate image stack after the end of simulation.
        '''
        max_Ca = 0
        for neuron in self.neuron_refs:
            max_Ca = max(max_Ca, max(neuron.Ca_samples))
        max_Ca *= (self.max_pixel_contributions/4.0)
        for i in range(self.num_samples):
            self.images.append(np.zeros(self.image_dims_px))
        for voxel in self.voxelspace:
            voxel.record_fluorescence_aposteriori(self.images, max_Ca)
        uint8_images = []
        for i in range(self.num_samples):
            uint8_images.append(np.clip(self.images[i], 0, 255).astype(np.uint8))
        self.images = uint8_images

    def get_recording(self)->dict:
        data = {}
        data[self.calcium_indicator] = self.images
        return data

    def show_voxels(self, savefolder:str, voxelfile:str, voxelspace=None, show_subvolume=False, pltinfo=None, figspecs={'linewidth':0.5,'figext':'pdf'}):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('Calcium Imaging Voxels')
        if voxelspace is None: voxelspace = self.voxelspace
        #print('DEBUG(Calcium_Imaging.show_voxels) == Showing %d voxels.' % len(voxelspace))
        pltinfo.colors['spheres'] = (0,1,0,0.2)
        pltinfo.colors['cylinders'] = (1,0,0,0.2)
        pltinfo.colors['boxes'] = (1.0, 1.0, 0.0, 0.05)

        self.system_ref.show(show=self.show, pltinfo=pltinfo, linewidth=figspecs['linewidth'])
        if show_subvolume:
            self.show_subvolume(savefolder, pltinfo=pltinfo, figspecs=figspecs)
        for voxel in voxelspace:
            voxel.show(pltinfo=pltinfo, linewidth=figspecs['linewidth'])
        if doshow:
            plt.draw()
            plt.savefig(savefolder+'/'+voxelfile, dpi=300)

    def show_subvolume(self, savefolder:str, pltinfo=None, figspecs={'linewidth':0.5,'figext':'pdf'}):
        doshow = pltinfo is None
        if pltinfo is None: pltinfo = PlotInfo('Calcium Imaging Subvolume')
        self.specs['imaged_subvolume'].show(pltinfo=pltinfo, linewidth=figspecs['linewidth'])
        if doshow:
            plt.draw()
            plt.savefig(savefolder+'/Ca-subvolume.'+figspecs['figext'], dpi=300)
