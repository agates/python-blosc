# -*- coding: utf-8 -*-
########################################################################
#
#       License: BSD 3-clause
#       Created: September 22, 2010
#       Author:  Francesc Alted - faltet@gmail.com
#
########################################################################

# flake8: noqa

import os

from setuptools import Extension
from setuptools import setup
from distutils.command.build_ext import build_ext
from setuptools import find_packages


with open('README.rst') as f:
    long_description = f.read()

# Blosc version
VERSION = open('VERSION').read().strip()

with open('src/blosc_cffi/version.py', 'w') as version_file:
    # Create the version.py file
    version_file.write('__version__ = "%s"\n' % VERSION)

# Global variables
CFLAGS = os.environ.get('CFLAGS', '').split()
LFLAGS = os.environ.get('LFLAGS', '').split()

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
      ext_modules=[
          Extension("blosc_cffi.blosc_extension",
                    libraries=["blosc"],
                    sources=["src/blosc_cffi/blosc_extension.c"],
                    extra_link_args=LFLAGS,
                    extra_compile_args=CFLAGS
                    ),
      ],
      install_requires=[
          'cffi',
      ],
      tests_require=['numpy', 'psutil'],
      extras_require={
      },
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      zip_safe=False,
      cmdclass={'build_ext': build_ext},
      )
