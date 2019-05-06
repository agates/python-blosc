# -*- coding: utf-8 -*-
########################################################################
#
#       License: BSD 3-clause
#       Created: September 22, 2010
#       Author:  Francesc Alted - faltet@gmail.com
#
########################################################################

# flake8: noqa

from pyclibrary import CParser
from setuptools import setup
from setuptools import find_packages


# Blosc version
VERSION = open('VERSION').read().strip()

with open('README.rst') as f:
    long_description = f.read()

# TODO: Allow customizing this
DEFAULT_INCLUDE = ("/usr/include/limits.h", "/usr/include/blosc.h")

with open('src/blosc_cffi/version.py', 'w') as version_file:
    # Create the version.py file
    version_file.write('__version__ = "%s"\n' % VERSION)

parser = CParser(DEFAULT_INCLUDE)
parser.process_all()
header_values = parser.defs["values"]
blosc_values = ((key, value)
                for key, value in header_values.items()
                if key.startswith("BLOSC") and value is not None)

with open('src/blosc_cffi/blosc_constants.py', 'w') as f:
    for key, value in blosc_values:
        try:
            out_value = int(value)
        except ValueError:
            try:
                out_value = float(value)
            except ValueError:
                out_value = '"{}"'.format(value)
        f.write("{} = {}\n".format(key, out_value))

setup(name="blosc-cffi",
      version=VERSION,
      description='Blosc data compressor using CFFI',
      long_description=long_description,
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Information Technology',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: BSD License',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3 :: Only',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Programming Language :: Python :: Implementation :: CPython',
                   'Programming Language :: Python :: Implementation :: PyPy',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: System :: Archiving :: Compression',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: Unix'],
      author='Francesc Alted, Valentin Haenel, Alecks Gates',
      author_email='faltet@gmail.com, valentin@haenel.co, agates@mail.agates.io',
      maintainer='Francesc Alted, Valentin Haenel, Alecks Gates',
      maintainer_email='faltet@gmail.com, valentin@haenel.co, agates@mail.agates.io',
      url='http://github.com/blosc/python-blosc-cffi',
      license='https://opensource.org/licenses/BSD-3-Clause',
      platforms=['any'],
      install_requires=[
          'cffi',
      ],
      tests_require=['numpy', 'psutil', 'pytest'],
      extras_require={
      },
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      zip_safe=False,
      )
