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
import asyncio
import concurrent.futures
import numpy as np
import matplotlib.pyplot as plt
import uuid
import multiprocessing
from PIL import Image
from asyncio import FIRST_COMPLETED
from concurrent.futures import CancelledError
from multiprocessing import Queue
from multiprocessing.queues import Empty
from skimage.io._plugins.pil_plugin import pil_to_ndarray
from mig.io import IDMCShare, ERDAShare, SFTPStore, SSHFSStore, AsyncSFTPStore


class Data:

    def __init__(self, id):
        assert id is not None
        self.id = id
        self.content = None


class Job:

    def __init__(self, handlers, func, result_queue):
        assert handlers is not None
        assert func is not None
        assert result_queue is not None
        self.id = uuid.uuid4()
        self.data = Data(self.id)
        self.handlers = handlers
        self.func = func
        self.result_queue = result_queue


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


def check_excep(excep):
    try:
        excep = excep.get(block=False)
        print("raising")
        raise excep
    except Empty:
        return None


async def read_handler(f_handler):
    with f_handler:
        return f_handler.read()


async def read_handlers(jobs, output_queue):
    for job in jobs:
        for f_handler in job.handlers:
            print("read data")
            job.data.content = await read_handler(f_handler)
            output_queue.put(job.data)
            print("Sent data")


async def img_to_ndarray(input_queue, output_queue, excep_queue):
    while True:
        check_excep(excep_queue)
        try:
            data = input_queue.get(timeout=2)
            print("got data")
            image = Image.open(io.BytesIO(data.content))
            frames = pil_to_ndarray(image)
            data.content = frames.copy()
            output_queue.put(data)
            print("sent image")
        except Empty:
            pass


async def process_images(input_queue, job, excep):
    print("Start process image")
    while True:
        check_excep(excep)
        try:
            data = input_queue.get(timeout=2)
            if data.id == job.id:
                result = job.func(data.content)
                data.content = result
                print("submitting result")
                job.result_queue.put(data)
        except Empty:
            pass


def run(task, *args):
    loop = asyncio.new_event_loop()
    try:
        task = task(*args)
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(task)
    except CancelledError:
        pass
    finally:
        loop.close()


async def main(fh):
    print("Start main")
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(
         max_workers=4
    )
    m = multiprocessing.Manager()
    loop.set_default_executor(executor)

    q_excep = m.Queue()
    job_files = m.Queue(10)
    job_images = m.Queue(10)
    job1_results = m.Queue(10)
    job2_results = m.Queue(10)

    with IDMCShare('K2wzxDcEBm') as \
            share:

        handlers = [
            # share.open('rec_8bit_ph03_cropC_kmeans_scale510.tif', 'rb'),
            share.open('098_rec06881_stack.tif', 'rb')
        ]

        jobs = [
            # Job([share.open('rec_8bit_ph03_cropC_kmeans_scale510.tif', 'rb')],
            #     foam_labelling, job1_results),
            Job([share.open('098_rec06881_stack.tif', 'rb')],
                alu_foam_nucleation, job2_results)
        ]

        async_jobs = [
            loop.run_in_executor(executor, run, read_handlers,
                                 jobs, job_files),
            loop.run_in_executor(executor, run, img_to_ndarray, job_files,
                                 job_images, q_excep),
        ]

        async_process = [
             loop.run_in_executor(executor, run, process_images, job_images,
                                  job, q_excep) for job in jobs
        ]

        for job in jobs:
            image = job.result_queue.get()
            plt.imshow(image, cmap='bone')
            plt.show()

        q_excep.put(CancelledError)
        q_excep.put(CancelledError)
        completed, pending = await asyncio.wait(async_process)
        print("Finished")
    executor.shutdown(wait=True)


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
    bench_fh.write("serial,scale_image,{},{}\n".format(load_stop-load_start,
                                                       stop-start))

    start = time.time()
    file2 = '098_rec06881_stack.tif'
    with share.open(file2, 'rb') as fh:
        load_start = time.time()
        x = Image.open(io.BytesIO(fh.read()))
        v = pil_to_ndarray(x)
        load_stop = time.time()
        alu_foam_nucleation(v)
    stop = time.time()
    bench_fh.write("serial,098_rec,{},{}\n".format(load_stop-load_start,
                                                   stop-start))
    share.close()


def async(fh):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(fh))
    finally:
        loop.close()


if __name__ == "__main__":
    # with open('bench', 'a') as fh:
    #     fh.write('test,file,load time(sec),exetime(sec)\n')
    #     for num in range(50):
    #         serial(fh)

    with open('bench_async.txt', 'a') as fh:
        fh.write('test,file,time(sec)\n')
        # for num in range(50):
        async(fh)

    # with open('async.txt', 'w') as fh:
    #     for num in range(50):
    #         start = time.time()
    #         async(fh)
    #         stop = time.time()
    #
    #         projections = share.list('projections')
    #         for projection in projections:
    #             if projection.startswith('.'):
    #                 continue
    #             path = os.path.join('projections', projection)
    #             t1 = time.time()
    #             data = share.read_binary(filename=path)
    #             t2 = time.time()
    #             times.append(t2 - t1)
    #
    #         print("num_reads: {}".format(len(times)))
    #         print("total_time: {}".format(sum(times)))
    #         print("avg_read_time: {}".format(sum(times) / len(times)))

