from cffi import FFI

from .blosc_constants import BLOSC_MAX_OVERHEAD

ffi = FFI()

ffi.cdef(
    """
    void blosc_init(void);

    void blosc_destroy(void);

    int blosc_compress(int clevel, int doshuffle, size_t typesize, size_t nbytes,
                       const void* src, void* dest, size_t destsize);
    
    int blosc_compress_ctx(int clevel, int doshuffle, size_t typesize,
                           size_t nbytes, const void* src, void* dest,
                           size_t destsize, const char* compressor,
                           size_t blocksize, int numinternalthreads);

    int blosc_decompress(const void* src, void* dest, size_t destsize);
    
    int blosc_decompress_ctx(const void *src, void *dest, size_t destsize, int numinternalthreads);

    int blosc_getitem(const void* src, int start, int nitems, void* dest);

    int blosc_get_nthreads(void);

    int blosc_set_nthreads(int nthreads);

    char* blosc_get_compressor(void);

    int blosc_set_compressor(const char* compname);

    int blosc_compcode_to_compname(int compcode, char** compname);

    int blosc_compname_to_compcode(const char* compname);

    char* blosc_list_compressors(void);

    char* blosc_get_version_string(void);

    int blosc_get_complib_info(char* compname, char** complib, char** version);

    int blosc_free_resources(void);

    void blosc_cbuffer_sizes(const void* cbuffer, size_t* nbytes, size_t* cbytes,
                             size_t* blocksize);
    
    int blosc_cbuffer_validate(const void* cbuffer, size_t cbytes,
                               size_t* nbytes);

    void blosc_cbuffer_metainfo(const void* cbuffer, size_t* typesize, int* flags);

    void blosc_cbuffer_versions(const void* cbuffer, int* version, int* versionlz);

    char* blosc_cbuffer_complib(const void* cbuffer);

    int blosc_get_blocksize(void);

    void blosc_set_blocksize(size_t blocksize);

    void blosc_set_splitmode(int splitmode);
    """
)

c_blosc = ffi.dlopen("blosc")

free_resources = c_blosc.blosc_free_resources
init = c_blosc.blosc_init
destroy = c_blosc.blosc_destroy


class CBloscState:
    RELEASEGIL = 0


def compressor_list():
    return str(ffi.string(c_blosc.blosc_list_compressors()), "UTF-8")


def code_to_name(code):
    with ffi.new("char **") as name_ptr:
        result = c_blosc.blosc_compcode_to_compname(code, name_ptr)

        if result < 0:
            raise Exception("Invalid code")

        return str(ffi.string(name_ptr[0]), "UTF-8")


def name_to_code(name):
    with ffi.from_buffer(bytes(name, "UTF-8")) as name_ptr:
        code = c_blosc.blosc_compname_to_compcode(name_ptr)

    if code < 0:
        raise Exception("Invalid name")

    return code


def clib_info(cname):
    cname_char = ffi.from_buffer(bytes(cname, "UTF-8"))

    with ffi.new("char **") as clib:
        with ffi.new("char **") as version:
            ret = c_blosc.blosc_get_complib_info(cname_char, clib, version)

            if ret < 0:
                raise Exception("Error getting blosc complib info.  Error code {}".format(ret))

            clib_str = ffi.string(clib[0])
            version_str = ffi.string(version[0])

    return str(clib_str, "UTF-8"), str(version_str, "UTF-8")


def get_clib(input_bytes):
    return str(ffi.string(c_blosc.blosc_cbuffer_complib(input_bytes)), "UTF-8")


def set_blocksize(blocksize):
    c_blosc.blosc_set_blocksize(blocksize)


def get_blocksize():
    return c_blosc.blosc_get_blocksize()


def set_nthreads(nthreads):
    # returns old_nthreads
    return c_blosc.blosc_set_nthreads(nthreads)


def set_releasegil(_):
    # C function calls are done with the GIL released ?
    # from https://cffi.readthedocs.io/en/latest/ref.html?highlight=gil
    pass


def get_cbuffer_sizes(cbuffer):
    with ffi.new("size_t *") as nbytes_size_t_ptr:
        with ffi.new("size_t *") as cbytes_size_t_ptr:
            with ffi.new("size_t *") as blocksize_size_t_ptr:
                c_blosc.blosc_cbuffer_sizes(cbuffer, nbytes_size_t_ptr, cbytes_size_t_ptr, blocksize_size_t_ptr)

                return nbytes_size_t_ptr[0], cbytes_size_t_ptr[0], blocksize_size_t_ptr[0]


def cbuffer_validate(cbuffer):
    with ffi.from_buffer(cbuffer) as input_bytes_ptr:
        cbytes = len(input_bytes_ptr)
        with ffi.new("size_t *") as nbytes_size_t_ptr:
            result = c_blosc.blosc_cbuffer_validate(input_bytes_ptr, cbytes, nbytes_size_t_ptr)

    return result == 0


def get_nbytes(input_bytes_ptr, cbytes, nbytes_size_t_ptr):
    with ffi.new("size_t *") as cbytes2_size_t_ptr:
        with ffi.new("size_t *") as blocksize_size_t_ptr:
            c_blosc.blosc_cbuffer_sizes(input_bytes_ptr, nbytes_size_t_ptr,
                                        cbytes2_size_t_ptr,
                                        blocksize_size_t_ptr)

            cbytes2 = cbytes2_size_t_ptr[0]
    if cbytes != cbytes2:
        raise Exception("Not a Blosc buffer or header info is corrupted")


def compress(input_bytes, typesize, clevel=None, shuffle=None, cname=None):
    with ffi.from_buffer(bytes(cname, "UTF-8")) as cname_char:
        with ffi.from_buffer(input_bytes) as input_bytes_ptr:
            nbytes = len(input_bytes_ptr)
            return compress_helper(input_bytes_ptr, nbytes, typesize, clevel, shuffle, cname_char)


def compress_ptr(input_ptr, nbytes, typesize, clevel, shuffle, cname):
    with ffi.from_buffer(bytes(cname, "UTF-8")) as cname_char:
        return compress_helper(input_ptr, nbytes, typesize, clevel, shuffle, cname_char)


def compress_helper(input_bytes_ptr, nbytes, typesize, clevel, shuffle, cname_char):
    compressor_set_result = c_blosc.blosc_set_compressor(cname_char)
    if compressor_set_result < 0:
        raise Exception("Compressor is not available")

    output_max_size = nbytes + BLOSC_MAX_OVERHEAD
    blocksize = c_blosc.blosc_get_blocksize()
    nthreads = c_blosc.blosc_get_nthreads()
    with ffi.new("char []", output_max_size) as output:
        cbytes = c_blosc.blosc_compress_ctx(clevel, shuffle, typesize, nbytes,
                                            input_bytes_ptr, output, output_max_size,
                                            cname_char, blocksize, nthreads)

        if cbytes < 0:
            raise Exception("Error compressing data")

        result = ffi.unpack(output, cbytes)

        return result


def decompress(input_bytes, as_bytearray):
    with ffi.from_buffer(input_bytes) as input_bytes_ptr:
        cbytes = len(input_bytes_ptr)
        with ffi.new("size_t *") as nbytes_size_t_ptr:
            get_nbytes(input_bytes_ptr, cbytes, nbytes_size_t_ptr)
            nbytes = nbytes_size_t_ptr[0]

        with ffi.new("char []", nbytes) as output_ptr:
            decompress_helper(input_bytes_ptr, nbytes, output_ptr)

            output = bytes(ffi.buffer(output_ptr))

    return bytearray(output) if as_bytearray else output


def decompress_ptr(input_ptr, output_ptr):
    with ffi.new("size_t *") as nbytes_size_t_ptr:
        get_nbytes(input_ptr, len(input_ptr), nbytes_size_t_ptr)
        nbytes = nbytes_size_t_ptr[0]

    decompress_helper(input_ptr, nbytes, output_ptr)

    return nbytes


def decompress_helper(input_ptr, nbytes, output_ptr):
    nthreads = c_blosc.blosc_get_nthreads()
    error = c_blosc.blosc_decompress_ctx(input_ptr, output_ptr, nbytes, nthreads)

    if error < 0:
        raise Exception("Error while decompressing data")
    elif error != nbytes:
        raise Exception("Expected {} bytes of decompressed data, got {}".format(nbytes, error))
