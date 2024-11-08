# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import io
import time
import tqdm
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from skimage.io._plugins.pil_plugin import pil_to_ndarray
from mig.io import IDMCShare


def foam_labelling(stack_image):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))
    for i, (cax, clabel) in enumerate(zip([ax1, ax2, ax3], ['xy', 'zy', 'zx'])):
        cax.imshow(np.sum(stack_image, i).squeeze(), interpolation='none', cmap='bone_r')
        cax.set_title('%s Projection' % clabel)
        cax.set_xlabel(clabel[0])
        cax.set_ylabel(clabel[1])

    from skimage.morphology import convex_hull_image as chull
    bubble_image = np.stack([chull(csl > 0) & (csl == 0) for csl in stack_image])
    bubble_invert = np.invert(bubble_image)

    from scipy import ndimage as ndi
    from scipy.ndimage.morphology import distance_transform_edt as distmap
    bubble_dist = distmap(bubble_invert)

    # # Watershed segmentation
    from skimage.feature import peak_local_max
    from skimage.morphology import watershed
    bubble_seeds = peak_local_max(bubble_dist, min_distance=12, indices='false')

    markers = ndi.label(bubble_seeds)[0]
    cropped_markers = markers[50:450, 50:450, 50:450]
    cropped_bubble_dist = bubble_dist[50:450, 50:450, 50:450]
    cropped_bubble_inver = bubble_invert[50:450, 50:450, 50:450]
    labeled_bubbles = watershed(-cropped_bubble_dist, cropped_markers,
                                mask=cropped_bubble_inver)

    # interpolation='nearest')
    # Feature properties
    from skimage.measure import regionprops
    props = regionprops(labeled_bubbles)
    props[100].filled_area


def alu_foam_nucleation(stack_image):
    nhight, ncols, nrows = stack_image.shape
    row, col = np.ogrid[:nrows, :ncols]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))
    for i, (cax, clabel) in enumerate(zip([ax1, ax2, ax3], ['xy', 'zy', 'zx'])):
        cax.imshow(np.sum(stack_image, i).squeeze(), interpolation='none', cmap='bone_r')
        cax.set_title('%s Projection' % clabel)
        cax.set_xlabel(clabel[0])
        cax.set_ylabel(clabel[1])


def serial(bench_fh):
    share = IDMCShare('K2wzxDcEBm')
    start = time.time()
    file1 = 'rec_8bit_ph03_cropC_kmeans_scale510.tif'
    with share.open(file1, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        foam_labelling(v)
    stop = time.time()
    bench_fh.write("serial,scale_image,{},{}\n".format(load_stop - load_start,
                                                       stop - start))
    with share.open(file1, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        foam_labelling(v)


    start = time.time()
    file2 = '098_rec06881_stack.tif'
    with share.open(file2, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        alu_foam_nucleation(v)
    stop = time.time()
    bench_fh.write("serial,098_rec,{},{}\n".format(load_stop - load_start,
                                                   stop - start))
    share.close()


def local(bench_fh):

    start = time.time()
    file1 = 'max_data/rec_8bit_ph03_cropC_kmeans_scale510.tif'
    with open(file1, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        foam_labelling(v)
    stop = time.time()
    bench_fh.write("serial,scale_image,{},{}\n".format(load_stop - load_start,
                                                       stop - start))

    start = time.time()
    file2 = 'max_data/098_rec06881_stack.tif'
    with open(file2, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        alu_foam_nucleation(v)
    stop = time.time()
    bench_fh.write("serial,098_rec,{},{}\n".format(load_stop - load_start,
                                                   stop - start))


if __name__ == "__main__":
    with open('bench_remote.txt', 'a') as fh:
        #fh.write('test,file,load time(sec),exetime(sec)\n')
        for num in range(2):
            print(num)
            serial(fh)
            fh.flush()
