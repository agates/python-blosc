# -*- coding: utf-8 -*-
"""
threadpool.py
Created on Sun Oct 23 12:03:46 2016
@author: Robert A. Mcleod - robbmcleod@gmail.com

Compares running blosc_cffi with and without GIL release, and compares various
combinations of ThreadPool threads and blosc_cffi-threads for operating on large
chunks.  The target is an image stack [50,1024,1024], where each frame can 
be compressed as a chunk.
"""

import numpy as np
from timeit import default_timer as timer
import blosc_cffi
from multiprocessing.pool import ThreadPool

nRuns = 5
dtype = 'int64'
m = 48
N = 2048
MegaBytes = m * N * N * np.dtype(dtype).itemsize / 2 ** 20
maxThreads = blosc_cffi.nthreads

BLOCKSIZE = 2 ** 18
CLEVEL = 4
SHUFFLE = blosc_cffi.SHUFFLE
COMPRESSOR = 'zstd'


def compress_slice(args):
    """
    args = (numpy array address, array_size, item_size, bytesList, bytesIndex)
    """
    args[3][args[4]] = blosc_cffi.compress_ptr(args[0], args[1], args[2],
                                               clevel=CLEVEL, shuffle=SHUFFLE, cname=COMPRESSOR)


def decompress_slice(J, list_bytes):
    pass


def compress_stack(image_stack, blosc_threads=1, pool_threads=maxThreads):
    """
    Does frame compression using a ThreadPool to distribute the load. 
    """
    blosc_cffi.set_nthreads(blosc_threads)
    tPool = ThreadPool(pool_threads)

    num_slices = image_stack.shape[0]
    # Build parameters list for the threaded processeses, consisting of index
    tArgs = [None] * num_slices
    itemSize = image_stack.dtype.itemsize
    bytesList = [None] * num_slices
    for J in np.arange(num_slices):
        tArgs[J] = (image_stack[J, :, :].__array_interface__['data'][0], \
                    N * N, itemSize, bytesList, J)

    # All operations are done 'in-place' 
    tPool.map(compress_slice, tArgs)
    tPool.close()
    tPool.join()


def decompress_stack(image_shape, image_dtype, blosc_threads=1, pool_threads=maxThreads):
    blosc_cffi.set_nthreads(blosc_threads)
    tPool = ThreadPool(pool_threads)

    num_slices = image_shape[0]
    imageStack = np.empty(image_shape)


blosc_cffi.print_versions()
blosc_cffi.set_blocksize(BLOCKSIZE)
print("Creating NumPy stack with %d float32 elements:" % (m * N * N))

stack = np.zeros([m, N, N], dtype=dtype)
xmesh, ymesh = np.meshgrid(np.arange(-N / 2, N / 2), np.arange(-N / 2, N / 2))
compress_mesh = (np.cos(xmesh) + np.exp(-ymesh ** 2 / N)).astype(dtype)
for J in np.arange(m):
    stack[J, :, :] = compress_mesh

# Determine arrangement of pool threads and blosc_cffi threads
testCases = int(np.floor(np.log2(maxThreads)) + 1)
powProduct = 2 ** np.arange(0, testCases)
poolThreads = np.hstack([1, powProduct])
bloscThreads = np.hstack([1, powProduct[::-1]])
# Let's try instead just pool threads...
# poolThreads = np.arange( 1, maxThreads+1 )
# bloscThreads = np.ones_like( poolThreads )

solo_times = np.zeros_like(poolThreads, dtype='float64')
solo_unlocked_times = np.zeros_like(poolThreads, dtype='float64')
locked_times = np.zeros_like(poolThreads, dtype='float64')
unlocked_times = np.zeros_like(poolThreads, dtype='float64')

for J in np.arange(nRuns):
    print("Run  %d of %d" % (J + 1, nRuns))
    blosc_cffi.set_releasegil(False)
    for I in np.arange(len(poolThreads)):
        t1 = timer()
        blosc_cffi.set_nthreads(bloscThreads[I])
        blosc_cffi.compress_ptr(stack.__array_interface__['data'][0], stack.size, stack.dtype.itemsize, \
                                clevel=CLEVEL, shuffle=SHUFFLE, cname=COMPRESSOR)
        solo_times[I] += timer() - t1

    blosc_cffi.set_releasegil(True)
    for I in np.arange(len(poolThreads)):
        t2 = timer()
        blosc_cffi.set_nthreads(bloscThreads[I])
        blosc_cffi.compress_ptr(stack.__array_interface__['data'][0], stack.size, stack.dtype.itemsize, \
                                clevel=CLEVEL, shuffle=SHUFFLE, cname=COMPRESSOR)
        solo_unlocked_times[I] += timer() - t2

    blosc_cffi.set_releasegil(True)
    for I in np.arange(len(poolThreads)):
        t3 = timer()
        compress_stack(stack, blosc_threads=bloscThreads[I], pool_threads=poolThreads[I])
        unlocked_times[I] += timer() - t3

    blosc_cffi.set_releasegil(False)
    for I in np.arange(len(poolThreads)):
        t4 = timer()
        compress_stack(stack, blosc_threads=bloscThreads[I], pool_threads=poolThreads[I])
        locked_times[I] += timer() - t4

solo_times /= nRuns
solo_unlocked_times /= nRuns
locked_times /= nRuns
unlocked_times /= nRuns
print("##### NO PYTHON THREADPOOL -- GIL LOCKED #####")
print(" -- Baseline normal blosc_cffi operation --")
for I in np.arange(len(poolThreads)):
    print("    Compressed %.2f MB with %d pool threads, %d blosc_cffi threads in: %f s" \
          % (MegaBytes, 0, bloscThreads[I], solo_times[I]))
print("##### NO PYTHON THREADPOOL -- GIL RELEASED #####")
print(" -- Shows penalty for releasing GIL in normal blosc_cffi operation --")
for I in np.arange(len(poolThreads)):
    print("    Compressed %.2f MB with %d pool threads, %d blosc_cffi threads in: %f s" \
          % (MegaBytes, 0, bloscThreads[I], solo_unlocked_times[I]))
print("##### GIL LOCKED w/ PYTHON THREADPOOL #####")
print(" -- Shows that GIL stops ThreadPool from working --")
for I in np.arange(len(poolThreads)):
    print("    Compressed %.2f MB with %d pool threads, %d blosc_cffi threads in: %f s" \
          % (MegaBytes, poolThreads[I], bloscThreads[I], locked_times[I]))
print("##### GIL RELEASED w/ PYTHON THREADPOOL #####")
print(" -- Shows scaling between Python multiprocessing.threadPool and blosc_cffi threads --")
for I in np.arange(len(poolThreads)):
    print("    Compressed %.2f MB with %d pool threads, %d blosc_cffi threads in: %f s" \
          % (MegaBytes, poolThreads[I], bloscThreads[I], unlocked_times[I]))
