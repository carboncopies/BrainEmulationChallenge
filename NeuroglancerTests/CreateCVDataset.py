import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import imageio.v3 as iio 

from cloudvolume import CloudVolume
from cloudvolume import Bbox
from cloudvolume.lib import mkdir, touch

info = CloudVolume.create_new_info(
    num_channels = 3,
    layer_type = 'image', # 'image' or 'segmentation'
    data_type = 'uint8', # can pick any popular uint
    encoding = 'jpeg', # see: https://github.com/seung-lab/cloud-volume/wiki/Compression-Choices
    resolution =   [20,   20,   40], # X,Y,Z values in nanometers
    voxel_offset = [0,    0,    0], # values X,Y,Z values in voxels
    chunk_size =   [1024, 1024, 1], # rechunk of image X,Y,Z in voxels
    volume_size =  [1024, 1024, 8], # X,Y,Z size in voxels
)

# If you're using amazon or the local file system, you can replace 'gs' with 's3' or 'file'
vol = CloudVolume('file://out', info=info)
vol.provenance.description = "Description of Data"
vol.provenance.owners = ['email_address_for_uploader/imager'] # list of contact email addresses

vol.commit_info() # generates gs://bucket/dataset/layer/info json file
vol.commit_provenance() # generates gs://bucket/dataset/layer/provenance json file

direct = './D'

# progress_dir = mkdir('progress/') # unlike os.mkdir doesn't crash on prexisting 
# done_files = set([ int(z) for z in os.listdir(progress_dir) ])
# all_files = set(range(vol.bounds.minpt.z, vol.bounds.maxpt.z + 1))

to_upload = os.listdir(direct)#[z for z in all_files.difference(done_files) ]
to_upload.sort()


for z in range(len(to_upload)):
    fpath = to_upload[z]
    img_name = os.path.join(direct, fpath)
    print('Processing ', img_name)
    image = iio.imread(img_name)
    print(image.shape)
    image = np.swapaxes(image, 0, 1)
    image = image[..., np.newaxis]
    image = np.swapaxes(image, 2, 3)
    vol[:,:, z] = image


