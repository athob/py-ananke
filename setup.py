#!/usr/bin/env python
import pathlib
from setuptools import setup

from src._build_utils import *
from src.constants import NAME, SRC_DIR, PYENBID, PYGALAXIA
from src.__metadata__ import *

ROOT_DIR = pathlib.Path(__file__).parent

for_all_files = ('__license__', )

long_description = ""

package_data = {NAME: all_files(*for_all_files,
                                basedir=pathlib.Path(SRC_DIR, NAME))}

EnBiD_meta, Galaxia_meta = check_submodules(ROOT_DIR)

setup(name=NAME,
      version=__version__,
      author=__author__,
      author_email=__email__,
      maintainer=__maintainer__,
      maintainer_email=__email__,
      url=__url__,
      description=f"{__project__}: {__description__}",
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=__classifiers__,
      license=__license__,
      copyright=__copyright__,
      python_requires='>=3.8',
      packages=[NAME],
      package_dir={'': SRC_DIR},
      package_data=package_data,
      include_package_data=True,
      install_requires=["numpy>=1.22,<2", "scipy>=1.7.2,<2", "pandas>=2,<3",
                        f"EnBiD_ananke @ file://{(ROOT_DIR / PYENBID).resolve()}",
                        f"Galaxia_ananke @ file://{(ROOT_DIR / PYGALAXIA).resolve()}"]
      )
