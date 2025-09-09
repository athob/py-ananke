#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of py-ananke:
# <https://github.com/athob/py-ananke>.
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-ananke/blob/main/COPYRIGHT>
#
"""
"""
import pathlib

from ._name import *
from ._builtin_utils import import_source_file

__all__ = ['get_versions']


get_versions = import_source_file("_version", pathlib.Path(__file__).parent / NAME / '_version.py').get_versions


if __name__ == '__main__':
    raise NotImplementedError()
