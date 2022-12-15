#!/usr/bin/env python
"""
Docstring
"""
import pathlib
import EnBiD
import Galaxia

from .constants import *

__all__ = ['Ananke']


class Ananke:
    _pos = 'pos3'
    _vel = 'vel3'
    def __init__(self, particles, name, ngb=64, **kwargs) -> None:
        self.__particles = particles
        self.__name = name
        self.__ngb = ngb
        self.__parameters = kwargs
        self.__catalogue = None
    
    def _run_enbid(self):
        path = pathlib.Path(self.name)
        rho_pos = EnBiD.enbid(self.particles[self._pos], name=path / POS_TAG, ngb=self.ngb)
        rho_vel = EnBiD.enbid(self.particles[self._vel], name=path / VEL_TAG, ngb=self.ngb)
        return {POS_TAG: rho_pos, VEL_TAG: rho_vel}

    def _run_galaxia(self, rho):
        output = Galaxia.make_survey_from_particles(self.particles, rho[POS_TAG], rho[VEL_TAG], simname=self.name, ngb=self.ngb, **self.parameters)
        self.__catalogue = output
    
    def run(self):
        return self._run_galaxia(self._run_enbid())

    @property
    def particles(self):
        return self.__particles

    @property
    def name(self):
        return self.__name

    @property
    def ngb(self):
        return self.__ngb

    @property
    def parameters(self):
        return self.__parameters

    @property
    def catalogue(self):
        if self.__catalogue is None:
            raise RuntimeError("You must use the `run` method before accessing the catalogue")
        else:
            return self.__catalogue


if __name__ == '__main__':
    pass
