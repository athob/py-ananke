#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of the py-ananke project,
# <https://github.com/athob/py-ananke>, which is licensed
# under the GNU Affero General Public License v3.0 (AGPL-3.0).
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-ananke/blob/main/COPYRIGHT>
#
"""
ananke
======

Provides a pipeline to generate mock synthetic star catalogs out of a
given set of particles tracing a stellar population.

How to use
----------

ananke comes with the class Ananke, please refer to its documentation
for further help.
"""
from .__metadata__ import *
from ._constants import *
from .Ananke import Ananke

__all__ = ['Ananke', 'make_dummy_particles_input', 'display_available_photometric_systems', 'display_kernels_docs', 'display_EnBiD_docs', 'display_extinction_docs', 'display_errormodel_docs']


make_dummy_particles_input = Ananke.make_dummy_particles_input

display_available_photometric_systems = Ananke.display_available_photometric_systems

display_kernels_docs = Ananke.display_kernels_docs

display_EnBiD_docs = Ananke.display_EnBiD_docs

display_extinction_docs = Ananke.display_extinction_docs

display_errormodel_docs = Ananke.display_errormodel_docs


if __name__ == '__main__':
    raise NotImplementedError()
