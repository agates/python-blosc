#!/usr/bin/env python3
########################################################################
#
#       License: MIT
#       Created: May 4, 2013
#       Author:  Valentin Haenel - valentin@haenel.co
#       Author:  Francesc Alted - faltet@gmail.com
#
########################################################################

"""
Small benchmark that compares a plain NumPy array copy against
compression through different compressors in Blosc.
"""
from timeit import default_timer as timer

import blosc_cffi
from cffi import FFI
import numpy as np

ffi = FFI()

N = 1e8
clevel = 5
Nexp = np.log10(N)

blosc_cffi.print_versions()

print("Creating a large NumPy array with 10**%d int64 elements:" % Nexp)
in_ = np.arange(N, dtype=np.int64)  # the trivial linear distribution
#in_ = np.linspace(0, 100, N)  # another linear distribution
#in_ = np.random.random_integers(0, 100, N)  # random distribution
print(" ", in_)

tic = timer()
out_ = np.copy(in_)
toc = timer()
print("  Time for copying array with np.copy():     %.3f s" % (toc-tic,))
print()

for cname in blosc_cffi.compressor_list():
    print("Using *** %s *** compressor::" % cname)
    ctic = timer()
    c = blosc_cffi.pack_array(in_, clevel=clevel, shuffle=True, cname=cname)
    ctoc = timer()
    dtic = timer()
    out = blosc_cffi.unpack_array(c)
    dtoc = timer()
    assert((in_ == out).all())
    print("  Time for pack_array/unpack_array:     %.3f/%.3f s." %
          (ctoc-ctic, dtoc-dtic), end='')
    print("\tCompr ratio: %.2f" % (in_.size*in_.dtype.itemsize*1. / len(c)))

    with ffi.from_buffer(in_) as in_ptr:
        with ffi.from_buffer(out_) as out_ptr:
            out_tmp = np.empty(in_.size, dtype=in_.dtype)
            with ffi.from_buffer(out_tmp) as out_tmp_ptr:
                ctic = timer()
                c = blosc_cffi.compress_ptr(in_ptr,
                                            in_.size, in_.dtype.itemsize,
                                            clevel=clevel, shuffle=True, cname=cname)
                ctoc = timer()

                dtic = timer()
                blosc_cffi.decompress_ptr(c, out_tmp_ptr)
                dtoc = timer()
    assert((in_ == out).all())
    print("  Time for compress_ptr/decompress_ptr: %.3f/%.3f s." %
          (ctoc-ctic, dtoc-dtic), end='')
    print("\tCompr ratio: %.2f" % (in_.size*in_.dtype.itemsize*1. / len(c)))
