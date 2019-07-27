########################################################################
#
#       License: MIT
#       Created: Jan 19, 2013
#       Author:  Francesc Alted - faltet@gmail.com
#
########################################################################

"""
Small benchmark that compares a plain NumPy array copy against
compression through different compressors in Blosc.
"""

import csv
from timeit import default_timer as timer

import blosc_cffi
from cffi import FFI
import numpy as np

ffi = FFI()

N = int(1e8)
clevel = 5
Nexp = np.log10(N)

blosc_cffi.print_versions()

print("Creating NumPy arrays with 10**%d int64/float64 elements:" % Nexp)
arrays = ((np.arange(N, dtype=np.int64), "arange linear distribution"),
          (np.linspace(0, 1000, N), "linspace linear distribution"),
          (np.random.random_integers(0, 1000, N), "random distribution")
          )

in_ = arrays[0][0]
out_ = np.empty(in_.size, dtype=in_.dtype)
with ffi.from_buffer(in_) as in_ptr:
    with ffi.from_buffer(out_) as out_ptr:
        t0 = timer()
        #out_ = np.copy(in_)
        out_ = ffi.memmove(out_ptr, in_ptr, N*8)
        tcpy = timer() - t0
print("  *** ctypes.memmove() *** Time for memcpy():\t%.3f s\t(%.2f GB/s)" % (
    tcpy, (N*8 / tcpy) / 2**30))

print("\nTimes for compressing/decompressing with clevel=%d and %d threads" % (
    clevel, blosc_cffi.ncores))
with open("./results/compress_ptr.csv", "w") as results_file:
    writer = csv.writer(results_file)
    writer.writerow(("Array type", "Compressor", "Filter",
                      "Compression Time (s)", "Compression Bandwidth (GB/s)",
                      "Decompression Time (s)", "Decompression Bandwidth (GB/s)",
                      "Compression Ratio"))
    for (in_, label) in arrays:
        print("\n*** %s ***" % label)
        for cname in blosc_cffi.compressor_list():
            for filter in [blosc_cffi.NOSHUFFLE, blosc_cffi.SHUFFLE, blosc_cffi.BITSHUFFLE]:
                with ffi.from_buffer(in_) as in_ptr:
                    t0 = timer()
                    c = blosc_cffi.compress_ptr(in_ptr,
                                                in_.size, in_.dtype.itemsize,
                                                clevel=clevel, shuffle=filter, cname=cname)
                    tc = timer() - t0
                out = np.empty(in_.size, dtype=in_.dtype)
                with ffi.from_buffer(out) as out_ptr:
                    t0 = timer()
                    blosc_cffi.decompress_ptr(c, out_ptr)
                    td = timer() - t0
                assert((in_ == out).all())
                writer.writerow((label, cname, blosc_cffi.filters[filter],
                                  tc, ((N * 8 / tc) / 2 ** 30),
                                  td, ((N * 8 / td) / 2 ** 30),
                                  N*8. / len(c)))
                print("  *** %-8s, %-10s *** %6.3f s (%.2f GB/s) / %5.3f s (%.2f GB/s)" % (
                    cname, blosc_cffi.filters[filter], tc, ((N * 8 / tc) / 2 ** 30), td, ((N * 8 / td) / 2 ** 30)), end='')
                print("\tCompr. ratio: %5.1fx" % (N*8. / len(c)))
