# Calcium_Imaging.py
# Randal A. Koene, 20230921

'''
Definitions of simulated calcium imaging.
See this article about fluorescence microscopy: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4711767/

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

#from .System import System
import numpy as np

from .Spatial import VecBox, point_is_within_box
from .Neuron import Neuron

class fluorescent_voxel:
	def __init__(self, xyz:np.array, voxel_um:float, neuron:Neuron, adj_dist_ratio=0):
		'''
		See: https://docs.google.com/document/d/1t1bPin-7YHswiNs4z7tSqFOLp7a1RQBXQQdhumkoOpQ/edit
		Note that adj_dist_ratio is d/adjacent_radius_um, where d is the distance
		from a specific voxel where adjacents were searched to this adjacent xyz.
		'''
		self.xyz = xyz
		self.voxel_um = voxel_um
		self.neuron_ref = neuron
		self.intersects = adj_dist_ratio==0 # If False then adjacent.
		self.act_brightness = 1.0-adj_dist_ratio # Reduce when adjacent at some distance.
		self.depth_brightness = 1.0
		self.image_pixels = []
		self.fifo_ref = None

	def get_adjacent_dict(self, adjacent_radius_um:float)->dict:
		'''
		Walk through the virtual voxels in a 3D box centered on self.xyz.
		For each location determine if it is within adjacent_radius_um
		of self.xyz. If so, then create an adjacent voxel object and
		add it to the dict that is returned with an integer indices key.
		'''
		adjacent_voxels_dict = {}
		radius_steps = int(adjacent_radius_um // self.voxel_um)
		if radius_steps==0: return {}
		for x in range(-radius_steps, radius_steps+1):
			for y in range(-radius_steps, radius_steps+1):
				for z in range(-radius_steps, radius_steps+1):
					v = np.array([x*self.voxel_um, y*self.voxel_um, z*self.voxel_um])
					r = np.sqrt(v.dot(v))
					if r < adjacent_radius_um:
						adj_xyz = self.xyz + v
						adj = fluorescent_voxel(
							adj_xyz,
							self.voxel_um,
							self.neuron_ref,
							adj_dist_ratio=r/adjacent_radius_um)
						indices_key = '%d_%d_%d' % (x,y,z)
						adjacent_voxels_dict[indices_key] = adj
		return adjacent_voxels_dict

	def set_depth_dimming(self, subvolume:VecBox):
		top_center = subvolume.center + (subvolume.half[3]*subvolume.dz)
		bottom_center = subvolume.center - (subvolume.half[3]*subvolume.dz)
		d_top = np.linalg.norm(top_center-self.xyz)
		d_bottom = np.linalg.norm(bottom_center-self.xyz)
		depth_dimming = d_top / (d_top + d_bottom)
		self.depth_brightness = 1.0 - depth_dimming

	def set_image_pixels(self, subvolume:VecBox):
		'''
		TODO: See the TODO note in Calcium_Imaging.initialize_projection_circles().
		'''
		dxyz = self.xyz - subvolume.center
		xy = dxyz[0:2]
		self.image_pixels.append(xy)

	def record_fluorescence(self, image_t:np.array):
		'''
		Use the FIFO queue data, as well as self.act_brightness and
		self.depth_brightness to add fluorescence value to the set
		of pixels in image_t that are affected by this voxel.
		TODO: Make sure this equation actually produces something like
		      what calcium imaging shows through fluorescence, both
		      when membrane potential is low and high (corresponding
		      calcium concentrations).
		'''
		Vdiff = self.neuron_ref.FIFO[-1] - self.neuron_ref.Vrest_mV
		V_add = Vdiff * self.act_brightness * self.depth_brightness
		for pixel in self.image_pixels:
			image_t[int(pixel[0]),int(pixel[1])] += V_add

def voxels_within_bounds(candidate_voxels:list, subvolume:VecBox)->list:
	visible_voxels = []
	for voxel in candidate_voxels:
		if point_is_within_box(voxel.xyz, subvolume):
			visible_voxels.append(voxel)
	return visible_voxels

class Calcium_Imaging:
	def __init__(self, specs:dict, system_ref):
		'''
		The characteristics in specs override default characteristics.
		Any that are not defined in specs remain at default values.
		'''
		self.specs = {
			'id': 'calcium_'+str(np.random.rand())[2:5], # Random generated default ID.
	        'fluorescing_neurons': system_ref.get_all_neuron_IDs(), # All neurons show up in calcium imaging.
	        'calcium_indicator': 'jGCaMP8', # Fast sensitive GCaMP (Zhang et al., 2023).
	        'indicator_rise_ms': 2.0,
	        'indicator_interval_ms': 20.0, # Max. spike rate trackable 50 Hz.
	        'imaged_subvolume': VecBox(
	        		center=np.array([0, 0, 0]),
	        		half=np.array([5.0, 5,0, 2,0]),
	        		dx=np.array([1.0, 0.0, 0.0]),
	        		dy=np.array([0.0, 1.0, 0.0]),
	        		dz=np.array([0.0, 0.0, 1.0]), # Positive dz indicates most visible top surface.
	        	),
	        #'microscope_lensfront_position_um': (0.0, 20.0, 0.0),
	        #'microscope_rear_position_um': (0.0, 40.0, 0.0),
	        'voxelspace_side_px': 30,
		}
		self.specs.update(specs)

		self.id = specs['id']
		self.fluorescing_neurons = specs['fluorescing_neurons']
		self.calcium_indicator = specs['calcium_indicator']
		self.indicator_rise_ms = specs['indicator_rise_ms']
		self.indicator_interval_ms = specs['indicator_interval_ms']
		#self.microscope_lensfront_position_um = specs['microscope_lensfront_position_um']
		#self.microscope_rear_position_um = specs['microscope_rear_position_um']
		self.system_ref = system_ref

		self.neuron_refs = system_ref.get_neurons_by_IDs(self.fluorescing_neurons)

		self.voxelspace = []

		self.t_recorded_ms = []
		self.image_dims_px = None
		self.image_t = None
		self.images = []

		self.voxel_um = self.get_voxel_size_um()
		self.include_components = self.get_visible_components_list()
		self.set_image_sizes()
		self.instantiate_voxel_space()
		self.initialize_depth_dimming()
		self.initialize_projection_circles()
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
			return ['soma']
		elif self.calcium_indicator=='synGCaMP6f':
			return ['soma', 'axon', 'synapse']
		else:
			return ['soma']

	def set_image_sizes(self):
		x_px = int((2*self.specs['imaged_subvolume'].half[0])//self.voxel_um)
		y_px = int((2*self.specs['imaged_subvolume'].half[1])//self.voxel_um)
		self.image_dims_px = (x_px, y_px)

	def instantiate_voxel_space(self):
		'''
		Traverse morphology of fluorescing neurons in the system.
		For each component, determine all of the "voxels" intersected
		and adjacent voxels. Instantiate those as voxel objects.
		'''
		candidate_voxels = []
		for neuron in self.neuron_refs:
			candidate_voxels += neuron.get_voxels(
				voxel_um=self.voxel_um,
				adjacent_radius_um=0.1,
				include_components=self.include_components)
		self.voxelspace = voxels_within_bounds(candidate_voxels, self.specs['imaged_subvolume'])

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
		for voxel in self.voxelspace:
			voxel.set_image_pixels(self.specs['imaged_subvolume'])

	def initialize_fluorescing_neurons_FIFOs(self):
		for neuron in self.neuron_refs:
			# TODO: Set different FIFO sizes for different GCaMP types.
			neuron.set_FIFO(2.0, self.system_ref.dt_ms)

	def record(self, t_ms:float):
		self.t_recorded_ms.append(t_ms)
		# TODO: Generate actual images for the fluorescence.
		self.image_t = np.zeros(self.image_dims_px)
		for voxel in self.voxelspace:
			voxel.record_fluorescence(self.image_t)
		self.images.append(self.image_t)

	def get_recording(self)->dict:
		data = {}
		data[self.calcium_indicator] = self.images
		return data
