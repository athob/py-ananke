#!/usr/bin/env python
import pathlib
from distutils.core import setup

from src._build_utils import *
from src.constants import NAME, SRC_DIR, PYENBID, PYGALAXIA
from src.__metadata__ import *

ROOT_DIR = pathlib.Path(__file__).parent

long_description = ""

check_submodules(ROOT_DIR)


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
      python_requires='>=3.7.12',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      install_requires=["numpy>=1.22,<2", "scipy>=1.7.2,<2", "pandas>=2,<3",
                        f"EnBiD_ananke @ file://{(ROOT_DIR / PYENBID).resolve()}",
                        f"Galaxia_ananke @ file://{(ROOT_DIR / PYGALAXIA).resolve()}"]
      )
