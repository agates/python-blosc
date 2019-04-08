# -*- coding: utf-8 -*-
import ctypes
import os

import gc
import pytest

import blosc_cffi

try:
    import numpy
except ImportError:
    numpy = None

try:
    import psutil
except ImportError:
    psutil = None


def test_basic_codec():
    s = b'0123456789'
    c = blosc_cffi.compress(s, typesize=1)
    d = blosc_cffi.decompress(c)
    assert s == d


@pytest.mark.parametrize(("cname", "expected"), ((cname, blosc_cffi.cname2clib[cname])
                                                 for cname in blosc_cffi.compressor_list()))
def test_get_clib(cname, expected):
    s = b'0123456789'
    c = blosc_cffi.compress(s, typesize=1, cname=cname)
    clib = blosc_cffi.get_clib(c)
    assert clib == expected


@pytest.mark.parametrize(("cname",), ((cname,) for cname in blosc_cffi.compressor_list()))
def test_all_compressors(cname):
    s = b'0123456789' * 100
    c = blosc_cffi.compress(s, typesize=1, cname=cname)
    d = blosc_cffi.decompress(c)
    assert s == d


@pytest.mark.parametrize(("filter_",), ((blosc_cffi.NOSHUFFLE,), (blosc_cffi.SHUFFLE,), (blosc_cffi.BITSHUFFLE,)))
def test_all_filters(filter_):
    s = b'0123456789' * 100
    c = blosc_cffi.compress(s, typesize=1, shuffle=filter_)
    d = blosc_cffi.decompress(c)
    assert s == d


def test_set_nthreads_exceptions():
    with pytest.raises(ValueError) as _:
        blosc_cffi.set_nthreads(blosc_cffi.MAX_THREADS + 1)


def test_compress_memoryview():
    # assume the expected answer was compressed from bytes
    b = b'0123456789'
    expected = blosc_cffi.compress(b, typesize=1)

    assert expected == blosc_cffi.compress(memoryview(b), typesize=1)


def test_compress_bytearray():
    # assume the expected answer was compressed from bytes
    b = b'0123456789'
    expected = blosc_cffi.compress(b, typesize=1)

    assert expected == blosc_cffi.compress(bytearray(b), typesize=1)


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_compress_numpy():
    # assume the expected answer was compressed from bytes
    b = b'0123456789'
    expected = blosc_cffi.compress(b, typesize=1)
    assert expected == blosc_cffi.compress(numpy.array([b]), typesize=1)


def test_decompress_bytes():
    # assume the expected answer was compressed from bytes
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(compressed)


def test_decompress_memoryview():
    # assume the expected answer was compressed from bytes
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(memoryview(compressed))


def test_decompress_bytearray():
    # assume the expected answer was compressed from bytes
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(bytearray(compressed))


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_decompress_numpy():
    # assume the expected answer was compressed from bytes
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(numpy.array([compressed]))


def test_decompress_bytes_releasegil():
    # assume the expected answer was compressed from bytes
    blosc_cffi.set_releasegil(True)
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    # now for all the things that support the buffer interface
    assert expected == blosc_cffi.decompress(compressed)

    blosc_cffi.set_releasegil(False)


def test_decompress_memoryview_releasegil():
    # assume the expected answer was compressed from bytes
    blosc_cffi.set_releasegil(True)
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(memoryview(compressed))
    blosc_cffi.set_releasegil(False)


def test_decompress_bytearray_releasegil():
    # assume the expected answer was compressed from bytes
    blosc_cffi.set_releasegil(True)
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(bytearray(compressed))
    blosc_cffi.set_releasegil(False)


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_decompress_numpy_releasegil():
    # assume the expected answer was compressed from bytes
    blosc_cffi.set_releasegil(True)
    expected = b'0123456789'
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(numpy.array([compressed]))
    blosc_cffi.set_releasegil(False)


def test_decompress_bytes_as_bytearray():
    # assume the expected answer was compressed from bytes
    expected = bytearray(b'0123456789')
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(compressed, as_bytearray=True)


def test_decompress_memoryview_as_bytearray():
    # assume the expected answer was compressed from bytes
    expected = bytearray(b'0123456789')
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(memoryview(compressed), as_bytearray=True)


def test_decompress_bytearray_as_bytearray():
    # assume the expected answer was compressed from bytes
    expected = bytearray(b'0123456789')
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(bytearray(compressed), as_bytearray=True)


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_decompress_numpy_as_bytearray():
    # assume the expected answer was compressed from bytes
    expected = bytearray(b'0123456789')
    compressed = blosc_cffi.compress(expected, typesize=1)

    assert expected == blosc_cffi.decompress(numpy.array([compressed]), as_bytearray=True)


def test_compress_exceptions():
    s = b'0123456789'

    pytest.raises(ValueError, blosc_cffi.compress, s, typesize=0)
    pytest.raises(ValueError, blosc_cffi.compress, s, typesize=blosc_cffi.MAX_TYPESIZE + 1)

    pytest.raises(ValueError, blosc_cffi.compress, s, typesize=1, clevel=-1)
    pytest.raises(ValueError, blosc_cffi.compress, s, typesize=1, clevel=10)

    pytest.raises(TypeError, blosc_cffi.compress, 1.0, 1)
    pytest.raises(TypeError, blosc_cffi.compress, ['abc'], 1)

    pytest.raises(ValueError, blosc_cffi.compress, 'abc', typesize=1, cname='foo')

    # Python 3 doesn't support unicode
    pytest.raises(ValueError, blosc_cffi.compress, '0123456789', typesize=0)

    # Create a simple mock to avoid having to create a buffer of 2 GB
    class LenMock(object):
        def __len__(self):
            return blosc_cffi.MAX_BUFFERSIZE + 1

    pytest.raises(ValueError, blosc_cffi.compress, LenMock(), typesize=1)


def test_compress_ptr_exceptions():
    # Make sure we do have a valid address, to reduce the chance of a
    # segfault if we do actually start compressing because the exceptions
    # aren't raised.
    typesize, items = 8, 8
    data = [float(i) for i in range(items)]
    Array = ctypes.c_double * items
    array = Array(*data)
    address = ctypes.addressof(array)

    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, items, typesize=-1)
    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, items, typesize=blosc_cffi.MAX_TYPESIZE + 1)

    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, items, typesize=typesize, clevel=-1)
    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, items, typesize=typesize, clevel=10)

    pytest.raises(TypeError, blosc_cffi.compress_ptr, 1.0, items, typesize=typesize)
    pytest.raises(TypeError, blosc_cffi.compress_ptr, ['abc'], items, typesize=typesize)

    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, -1, typesize=typesize)
    pytest.raises(ValueError, blosc_cffi.compress_ptr, address, blosc_cffi.MAX_BUFFERSIZE + 1, typesize=typesize)


def test_decompress_exceptions():
    pytest.raises(TypeError, blosc_cffi.decompress, 1.0)
    pytest.raises(TypeError, blosc_cffi.decompress, ['abc'])


def test_decompress_ptr_exceptions():
    # make sure we do have a valid address
    typesize, items = 8, 8
    data = [float(i) for i in range(items)]
    Array = ctypes.c_double * items
    in_array = Array(*data)
    c = blosc_cffi.compress_ptr(ctypes.addressof(in_array), items, typesize)
    out_array = ctypes.create_string_buffer(items * typesize)

    pytest.raises(TypeError, blosc_cffi.decompress_ptr, 1.0, ctypes.addressof(out_array))
    pytest.raises(TypeError, blosc_cffi.decompress_ptr, ['abc'], ctypes.addressof(out_array))

    pytest.raises(TypeError, blosc_cffi.decompress_ptr, c, 1.0)
    pytest.raises(TypeError, blosc_cffi.decompress_ptr, c, ['abc'])


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_pack_array_exceptions():
    pytest.raises(TypeError, blosc_cffi.pack_array, 'abc')
    pytest.raises(TypeError, blosc_cffi.pack_array, 1.0)

    items = (blosc_cffi.MAX_BUFFERSIZE // 8) + 1
    one = numpy.ones(1, dtype=numpy.int64)
    pytest.raises(ValueError, blosc_cffi.pack_array, one, clevel=-1)
    pytest.raises(ValueError, blosc_cffi.pack_array, one, clevel=10)

    # use stride trick to make an array that looks like a huge one
    ones = numpy.lib.stride_tricks.as_strided(one, shape=(1, items), strides=(8, 0))[0]

    # This should always raise an error
    pytest.raises(ValueError, blosc_cffi.pack_array, ones)


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_unpack_array_with_unicode_characters():
    input_array = numpy.array(['å', 'ç', 'ø', 'π', '˚'])
    packed_array = blosc_cffi.pack_array(input_array)
    numpy.testing.assert_array_equal(input_array, blosc_cffi.unpack_array(packed_array, encoding='UTF-8'))


def test_unpack_array_exceptions():
    pytest.raises(TypeError, blosc_cffi.unpack_array, 1.0)


@pytest.mark.skipif(not psutil, reason="psutil not available, cannot test for leaks")
@pytest.mark.slow
def test_no_leaks():
    num_elements = 10000000
    typesize = 8
    data = [float(i) for i in range(num_elements)]  # ~76MB
    Array = ctypes.c_double * num_elements
    array = Array(*data)
    address = ctypes.addressof(array)

    def leaks(operation, repeats=3):
        gc.collect()
        used_mem_before = psutil.Process(os.getpid()).memory_info()[0]
        for _ in range(repeats):
            operation()
        gc.collect()
        used_mem_after = psutil.Process(os.getpid()).memory_info()[0]
        # We multiply by an additional factor of .01 to account for
        # storage overhead of Python classes
        return (used_mem_after - used_mem_before) >= num_elements * 8.01

    def compress():
        blosc_cffi.compress(array, typesize, clevel=1)

    def compress_ptr():
        blosc_cffi.compress_ptr(address, num_elements, typesize, clevel=0)

    def decompress():
        cx = blosc_cffi.compress(array, typesize, clevel=1)
        blosc_cffi.decompress(cx)

    def decompress_ptr():
        cx = blosc_cffi.compress_ptr(address, num_elements, typesize, clevel=0)
        blosc_cffi.decompress_ptr(cx, address)

    assert not leaks(compress), 'compress leaks memory'
    assert not leaks(compress_ptr), 'compress_ptr leaks memory'
    assert not leaks(decompress), 'decompress leaks memory'
    assert not leaks(decompress_ptr), 'decompress_ptr leaks memory'


def test_get_blocksize():
    s = b'0123456789' * 1000
    blocksize = 2 ** 14
    blosc_cffi.set_blocksize(blocksize)
    blosc_cffi.compress(s, typesize=1)
    d = blosc_cffi.get_blocksize()
    assert d == blocksize


def test_get_cbuffer_sizes():
    s = b'0123456789' * 100000
    blocksize = 2 ** 16
    blosc_cffi.set_blocksize(blocksize)
    c = blosc_cffi.compress(s, typesize=1)
    t = blosc_cffi.get_cbuffer_sizes(c)
    assert t[0] == 1000000
    # One cannot be sure of the exact compressed bytes, so round to KB
    assert t[1] // 2 ** 10 == 4354 // 2 ** 10
    assert t[2] == blocksize


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_bitshuffle_not_multiple():
    # Check the fix for #133
    x = numpy.ones(27266, dtype='uint8')
    xx = x.tobytes()
    zxx = blosc_cffi.compress(xx, typesize=8, shuffle=blosc_cffi.BITSHUFFLE)
    last_xx = blosc_cffi.decompress(zxx)[-3:]
    assert last_xx == b'\x01\x01\x01'


def test_cbuffer_validate_bytes():
    expected = b'0123456789' * 1000
    compressed = blosc_cffi.compress(expected)

    assert blosc_cffi.cbuffer_validate(compressed)


def test_cbuffer_validate_memoryview():
    expected = b'0123456789' * 1000
    compressed = blosc_cffi.compress(expected)

    assert blosc_cffi.cbuffer_validate(memoryview(compressed))


def test_cbuffer_validate_bytearray():
    expected = b'0123456789' * 1000
    compressed = blosc_cffi.compress(expected)

    assert blosc_cffi.cbuffer_validate(bytearray(compressed))


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_cbuffer_validate_numpy():
    expected = b'0123456789' * 1000
    compressed = blosc_cffi.compress(expected)

    assert blosc_cffi.cbuffer_validate(numpy.array([compressed]))


def test_cbuffer_validate_bytes_failure():
    compressed = b'this_is_total_garbage'

    assert not blosc_cffi.cbuffer_validate(compressed)


def test_cbuffer_validate_memoryview_failure():
    compressed = b'this_is_total_garbage'

    assert not blosc_cffi.cbuffer_validate(memoryview(compressed))


def test_cbuffer_validate_bytearray_failure():
    compressed = b'this_is_total_garbage'

    assert not blosc_cffi.cbuffer_validate(bytearray(compressed))


@pytest.mark.skipif(not numpy, reason="Numpy not available")
def test_cbuffer_validate_numpy_failure():
    compressed = b'this_is_total_garbage'

    assert not blosc_cffi.cbuffer_validate(numpy.array([compressed]))
