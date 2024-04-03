#!/usr/bin/env python3
# xor_sc_groundtruth.py
# Randal A. Koene, 20240329

'''
Give this simple viewer a directory that contains EM images where the names contain slice numbers and X-Y
coordinates, enter an overlap ratio, and this viewer will put together a simple stiched image to view.
'''

from os import listdir
import json
import argparse
import numpy as np
import cv2
import imageio

Parser = argparse.ArgumentParser(description="Slice viewer")
Parser.add_argument("-d", '--dirpath', help="Path of directory to parse")
Parser.add_argument("-s", '--sidesize', help="Stiched image side size in pixels")
Parser.add_argument("-o", '--overlap', help="Overlap percentage")
Parser.add_argument("-i", '--interpolation', help="Interpolation (linear, cubic)")
Args = Parser.parse_args()

print('For actual stitching where positions are not exact or there')
print('may be distortions, see:')
print('https://medium.com/@paulsonpremsingh7/image-stitching-using-opencv-a-step-by-step-tutorial-9214aa4255ec')
print('')

default_path = None
default_sidesize = None
default_overlap = None
default_interpolation = None
try:
    with open('.sliceviewer-dir','r') as f:
        data = json.load(f)
    if 'dir' in data:
        default_path = data['dir']
    if 'sidesize' in data:
        default_sidesize = data['sidesize']
    if 'overlap' in data:
        default_overlap = data['overlap']
    if 'interpolation' in data:
        default_interpolation = data['interpolation']
except:
    pass

if Args.dirpath:
    dirpath = Args.dirpath
else:
    if default_path:
        dirpath = input('Directory path (def.=%s): ' % default_path)
        if dirpath == '':
            dirpath = default_path
    else:
        dirpath = input('Directory path: ')
if dirpath == '':
    print('Missing directory path.')
    exit(1)

if Args.sidesize:
    sidesize = int(Args.sidesize)
else:
    if default_sidesize:
        sidesize = input('Stiched side size in px (def.=%d): ' % default_sidesize)
        if sidesize == '':
            sidesize = default_sidesize
    else:
        sidesize = input('Stiched side size in px: ')
        if sidesize == '':
            print('Missing stitched side size.')
            exit(1)
        else:
            sidesize = int(sidesize)

if Args.overlap:
    overlap = float(Args.overlap)
else:
    if default_overlap:
        overlap = input('Overlap percentage (def.=%d): ' % default_overlap)
        if overlap == '':
            overlap = default_overlap
    else:
        overlap = input('Overlap percentage: ')
        if overlap == '':
            print('Missing overlap percentage.')
            exit(1)
        else:
            overlap = int(overlap)

if Args.interpolation:
    interpolation = float(Args.interpolation)
else:
    if default_interpolation:
        interpolation = input('Interpolation [c]ubic/[a]rea (def.=%s): ' % default_interpolation)
        if interpolation == '':
            interpolation = default_interpolation
        else:
            if interpolation[0] == 'a':
                interpolation = 'area'
            else:
                interpolation = 'cubic'
    else:
        interpolation = input('Interpolation [c]ubic/[a]rea: ')
        if interpolation == '':
            print('Missing interpolation.')
            exit(1)
        else:
            if interpolation[0] == 'a':
                interpolation = 'area'
            else:
                interpolation = 'cubic'

maxcontrast = (input('Maximize contrast? (y/N)') == 'y')

with open('.sliceviewer-dir','w') as f:
    json.dump({ 'dir': dirpath, 'sidesize': sidesize, 'overlap': overlap, 'interpolation': interpolation } ,f)

overlap_ratio = float(overlap)/100.0

all_files = listdir(dirpath)

print('Found %d files.' % len(all_files))

slices = set()
for fname in all_files:
    p = fname.find('_Slice')
    u = fname.find('_', p+6)
    slice_idx = int(fname[p+6:u])
    slices.add(slice_idx)

print('Number of slices     : '+str(len(slices)))
print('Smallest slice number: '+str(min(slices)))
print('Largest slice number : '+str(max(slices)))

def stitch_slice(show_slice_num:int, verbose=True, useoptions=False):
    show_slice = str(show_slice_num)
    slice_images = set()
    for fname in all_files:
        p = fname.find('_Slice'+show_slice+'_')
        if p >= 0:
            slice_images.add(fname)

    if len(slice_images) == 0:
        return None

    if verbose:
        print('Slice %s is composed of %d images.' % (show_slice, len(slice_images)))
    num_per_side = int(np.sqrt(len(slice_images)))
    if verbose:
        print('The stitched slice will contain %d by %d images.' % (num_per_side, num_per_side))

    x_locs = set()
    for fname in slice_images:
        p = fname.find('_X')
        u = fname.find('_', p+2)
        x_loc = float(fname[p+2:u])
        x_locs.add(x_loc)
    y_locs = set()
    for fname in slice_images:
        p = fname.find('_Y')
        u = fname.find('.png', p+2)
        y_loc = float(fname[p+2:u])
        y_locs.add(y_loc)
    if verbose:
        print('Found %d x locations and %d y locations.' % (len(x_locs), len(y_locs)))
    x_locs = list(sorted(x_locs))
    y_locs = list(sorted(y_locs))
    if verbose:
        print('X: '+str(x_locs))
        print('Y: '+str(y_locs))

    divby = 1.0 + (num_per_side - 1)*(1.0 - overlap_ratio)
    img_side_size = int(float(sidesize) / divby)
    step_size = int(float(img_side_size)*(1.0 - overlap_ratio))

    if verbose:
        print('At an overlap ratio of %f, each image will be resized to %d x %d.' % (overlap_ratio, img_side_size, img_side_size))

    for fname in slice_images:
        im = cv2.imread(dirpath+'/'+fname)
        (h, w, c) = im.shape[:3]
        break

    if verbose:
        print('The original size of each image is %d x %d (%d channels).' % (w, h, c))
    resize_ratio = float(img_side_size) / float(w)
    if verbose:
        print('Each image will be resized to %d percent of it original size.' % int(resize_ratio*100))

    #im_stitched = np.zeros((sidesize, sidesize, c), np.uint8)
    im_stitched = np.zeros((sidesize, sidesize), np.uint8)

    for fname in slice_images:
        p = fname.find('_X')
        u = fname.find('_', p+2)
        x_loc = float(fname[p+2:u])
        x_idx = x_locs.index(x_loc)
        p = fname.find('_Y')
        u = fname.find('.png', p+2)
        y_loc = float(fname[p+2:u])
        y_idx = y_locs.index(y_loc)
        #print('Next image position: (%d, %d)' % (x_idx, y_idx))
        x = x_idx*step_size
        y = y_idx*step_size
        im = cv2.imread(dirpath+'/'+fname)
        if interpolation == 'area':
            im_resized = cv2.resize(im[:,:,1], (img_side_size, img_side_size), interpolation = cv2.INTER_AREA)
        else:
            im_resized = cv2.resize(im[:,:,1], (img_side_size, img_side_size), interpolation = cv2.INTER_CUBIC)
        x_end = x+img_side_size
        y_end = y+img_side_size
        #print('Target location: [%d:%d, %d:%d]' % (y, y_end, x, x_end))
        #im_stitched[y:y+img_side_size, x:x+img_side_size, :3] = im_resized
        im_stitched[y:y+img_side_size, x:x+img_side_size] = im_resized

    if useoptions:
        if maxcontrast:
            # Remove the black border
            for x in range(sidesize-1,-1,-1):
                if im_stitched[sidesize//2,x]>0:
                    xlen = x+1
                    break
            for y in range(sidesize-1,-1,-1):
                if im_stitched[y,sidesize//2]>0:
                    ylen = y+1
                    break
            im_stitched = im_stitched[:ylen, :xlen]
            # Get background value
            backval = im_stitched[2,2]
            #print(str(backval))
            # Set background value to zero
            im_stitched[im_stitched == backval] = 0
            # Get the value range
            minval = im_stitched.min()
            maxval = im_stitched.max()
            # Stretch contrast
            stretchval = 255.0/float(maxval)
            im_stitched -= minval
            im_float = im_stitched.astype(np.float32)
            im_float *= stretchval
            im_stitched = im_float.astype(np.uint8)

    return im_stitched

show_slice = input('Slice number to show: ')
if show_slice == '':
    exit(1)
show_slice_num = int(show_slice)

def find_first_with_features(show_slice_num: int, sensitivity:float)->int:
    val_diff = 0
    steps = 0
    while val_diff < sensitivity:
        im_stitched = stitch_slice(show_slice_num)
        edgeskip = sidesize // 5
        #min_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].min()
        #max_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].max()
        min_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip].min()
        max_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip].max()
        val_diff = max_val - min_val
        if val_diff < sensitivity:
            show_slice_num += 40
            if show_slice_num > max(slices):
                return max(slices)
            steps += 1
        else:
            if steps > 0:
                show_slice_num -= 20
            return show_slice_num

def find_last_with_features(show_slice_num: int, sensitivity:float)->int:
    val_diff = 2*sensitivity
    steps = 0
    while val_diff >= sensitivity:
        im_stitched = stitch_slice(show_slice_num)
        edgeskip = sidesize // 5
        #min_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].min()
        #max_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].max()
        min_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip].min()
        max_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip].max()
        val_diff = max_val - min_val
        if val_diff >= sensitivity:
            show_slice_num += 40
            if show_slice_num > max(slices):
                return max(slices)
            steps += 1
        else:
            if steps > 0:
                show_slice_num -= 20
            return show_slice_num

search_for_it = input('Search? (y/N) ')
if search_for_it == 'y':
    sensitivity = input('Sensitivity: ')
    print('\nSeeing first with features...')
    show_slice_num = find_first_with_features(show_slice_num, float(sensitivity))
    print('\nSeeing last with features...')
    last_with_features = find_last_with_features(show_slice_num+20, float(sensitivity))
else:
    last_with_features = max(slices)

print('Slices with features from slice %d to slice %d' % (show_slice_num, last_with_features))

while show_slice_num >= 0:

    im_stitched = stitch_slice(show_slice_num, useoptions=True)

    edgeskip = sidesize // 5

    # mean_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].mean()
    # max_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].max()
    # min_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].min()
    # std_val = im_stitched[edgeskip:sidesize-edgeskip,edgeskip:sidesize-edgeskip,1].std()
    # print('Mean val %d, stdev val %.2f, max val %d, min val %d' % (mean_val, std_val, max_val, min_val))
    cv2.imshow('Slice %s' % str(show_slice_num), im_stitched)
    cv2.waitKey(0) 
    cv2.destroyAllWindows()

    ask_more = True
    while ask_more:
        next_step = input('Show more or save? (Y/n/number/s) ')
        if next_step == 's':
            cv2.imwrite('stitched-'+'%05d.jpg' % show_slice_num, im_stitched)
        else:
            ask_more = False
            if next_step == 'n':
                break
            try:
                next_slice_num = int(next_step)
                show_slice_unm = next_slice_num
            except:
                show_slice_num += 4
    if next_step == 'n':
        break

gif_stepsize = input('GIF step size: ')
if gif_stepsize == '':
    exit(1)
gif_stepsize = int(gif_stepsize)

images = []
#show_slice_num = 0
while show_slice_num <= last_with_features:

    print('(%d / %d)' % (show_slice_num, max(slices)))

    im_stitched = stitch_slice(show_slice_num, verbose=False, useoptions=True)
    if im_stitched is not None:
        images.append(im_stitched)

    show_slice_num += gif_stepsize

print('Created %d stitched images.' % len(images))

imageio.mimsave("stitched.gif", images, loop=0)

# with imageio.get_writer("stitched.gif", mode="I", loop=0) as writer:
#     for im in images:
#         writer.append_data(im)

# def stitch_slice2(show_slice_num:int, verbose=True):
#     show_slice = str(show_slice_num)
#     slice_images = set()
#     for fname in all_files:
#         p = fname.find('_Slice'+show_slice+'_')
#         if p >= 0:
#             slice_images.add(fname)

#     if verbose:
#         print('Slice %s is composed of %d images.' % (show_slice, len(slice_images)))
#     num_per_side = int(np.sqrt(len(slice_images)))
#     if verbose:
#         print('The stitched slice will contain %d by %d images.' % (num_per_side, num_per_side))

#     # Figure out how to identify the N x N images in their indexed positions.
#     x_locs = set()
#     for fname in slice_images:
#         p = fname.find('_X')
#         u = fname.find('_', p+2)
#         x_loc = float(fname[p+2:u])
#         x_locs.add(x_loc)
#     y_locs = set()
#     for fname in slice_images:
#         p = fname.find('_Y')
#         u = fname.find('.png', p+2)
#         y_loc = float(fname[p+2:u])
#         y_locs.add(y_loc)
#     if verbose:
#         print('Found %d x locations and %d y locations.' % (len(x_locs), len(y_locs)))
#     x_locs = list(sorted(x_locs))
#     y_locs = list(sorted(y_locs))
#     if verbose:
#         print('X: '+str(x_locs))
#         print('Y: '+str(y_locs))

#     divby = 1.0 + (num_per_side - 1)*(1.0 - overlap_ratio)
#     img_side_size = int(float(sidesize) / divby)
#     step_size = int(float(img_side_size)*(1.0 - overlap_ratio))

#     if verbose:
#         print('At an overlap ratio of %f, each image will be resized to %d x %d.' % (overlap_ratio, img_side_size, img_side_size))

#     for fname in slice_images:
#         im = cv2.imread(dirpath+'/'+fname)
#         (h, w, c) = im.shape[:3]
#         break

#     if verbose:
#         print('The original size of each image is %d x %d (%d channels).' % (w, h, c))
#     resize_ratio = float(img_side_size) / float(w)
#     if verbose:
#         print('Each image will be resized to %d percent of it original size.' % int(resize_ratio*100))

#     im_stitched = np.zeros((sidesize, sidesize, c), np.uint8)

#     for fname in slice_images:
#         p = fname.find('_X')
#         u = fname.find('_', p+2)
#         x_loc = float(fname[p+2:u])
#         x_idx = x_locs.index(x_loc)
#         p = fname.find('_Y')
#         u = fname.find('.png', p+2)
#         y_loc = float(fname[p+2:u])
#         y_idx = y_locs.index(y_loc)
#         #print('Next image position: (%d, %d)' % (x_idx, y_idx))
#         x = x_idx*step_size
#         y = y_idx*step_size
#         im = cv2.imread(dirpath+'/'+fname)
#         if interpolation == 'area':
#             im_resized = cv2.resize(im, (img_side_size, img_side_size), interpolation = cv2.INTER_AREA)
#         else:
#             im_resized = cv2.resize(im, (img_side_size, img_side_size), interpolation = cv2.INTER_CUBIC)
#         x_end = x+img_side_size
#         y_end = y+img_side_size
#         #print('Target location: [%d:%d, %d:%d]' % (y, y_end, x, x_end))
#         im_stitched[y:y+img_side_size, x:x+img_side_size, :3] = im_resized

#     return im_stitched
