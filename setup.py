#!/usr/bin/env python
import os
import pathlib
import sys
import re
import fileinput
import subprocess
import urllib.request
import distutils
from distutils.errors import CompileError
from distutils.command.build_ext import build_ext as CmdBuildExt
from distutils.cmd import Command
from distutils.core import setup

ROOT_DIR = os.path.split(os.path.abspath(__file__))[0]
NAME = 'ananke'
LOG_DIR = 'log'
SRC_DIR = 'src'
PYENBID = 'py-EnBiD'

long_description = ""

# metadata are set in the below file, but use this here to avoid warnings.
__author__ = __copyright__ = __credits__ = __license__ = __version__ = __maintainer__ = __email__ = __status__ = None
exec(open(os.path.join(ROOT_DIR, SRC_DIR, NAME, "__metadata__.py")).read())


setup(name=NAME,
      version=__version__,
      author=__author__,
      author_email=__email__,
      maintainer=__maintainer__,
      maintainer_email=__email__,
      url="https://github.com/athob/py-ananke",
      description="",
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[
          __status__,
          "Environment :: Console",
          "Intended Audience :: Science/Research",
          __license__,
          "Natural Language :: English",
          "Operating System :: Unix",
          "Programming Language :: Python :: 3",
          "Topic :: Database",
          "Topic :: Scientific/Engineering :: Astronomy",
          "Topic :: Software Development :: Version Control :: Git"
      ],
      python_requires='>=3',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      # package_data={NAME: all_files(*for_all_files, basedir=os.path.join(SRC_DIR, NAME))},
      # include_package_data=True,
      install_requires=['pandas',
                        f"EnBiD @ file://{(pathlib.Path(__file__).parent / PYENBID).resolve()}"],
      # ext_modules=[distutils.extension.Extension('', [])],
      # cmdclass={'build_ext': MyBuildExt, 'test': MyTest},
      )
