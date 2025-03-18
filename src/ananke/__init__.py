#!/usr/bin/env python
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

__all__ = ['Ananke', 'make_dummy_particles_input', 'display_available_photometric_systems', 'display_density_docs', 'display_EnBiD_docs', 'display_extinction_docs', 'display_errormodel_docs']


make_dummy_particles_input = Ananke.make_dummy_particles_input

display_available_photometric_systems = Ananke.display_available_photometric_systems

display_density_docs = Ananke.display_density_docs

display_EnBiD_docs = Ananke.display_EnBiD_docs

display_extinction_docs = Ananke.display_extinction_docs

display_errormodel_docs = Ananke.display_errormodel_docs


if __name__ == '__main__':
    raise NotImplementedError()
