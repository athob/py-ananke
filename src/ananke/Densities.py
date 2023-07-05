#!/usr/bin/env python
"""
Contains the Densities class definition

Please note that this module is private. The Densities class is
available in the main ``ananke`` namespace - use that instead.
"""
import pathlib
import EnBiD_ananke as EnBiD

from .constants import *

__all__ = ['Densities']


class Densities:
    """
        Store the particle kernel densities and compute them if necessary.
    """
    def __init__(self, ananke, **kwargs) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this Densities object
            **kwargs
                Additional parameters to be used by the density estimator
        """
        self.__ananke = ananke
        self.__parameters = kwargs
        self.__densities = None
    
    def _run_enbid(self):
        """
            Method to generate the dictionary of kernel density estimates with EnBiD
            that is needed to generate the survey from the pipeline particles
            
            Returns
            ----------
            rho : dict({POS_TAG}=array_like, {VEL_TAG}=array_like)
                A dictionary of same-length arrays representing kernel density
                estimates for the pipeline particles
        """
        path = pathlib.Path(self.name)
        rho_pos = EnBiD.enbid(self.particle_positions, name=path / POS_TAG, ngb=self.ngb, **self.parameters)
        rho_vel = EnBiD.enbid(self.particle_velocities, name=path / VEL_TAG, ngb=self.ngb, **self.parameters)
        self.__densities = {POS_TAG: rho_pos, VEL_TAG: rho_vel}
        return self.__densities
    
    _run_enbid.__doc__ = _run_enbid.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)

    @property
    def ananke(self):
        return self.__ananke
    
    @property
    def particle_positions(self):
        return self.ananke.particle_positions
    
    @property
    def particle_velocities(self):
        return self.ananke.particle_velocities

    @property
    def name(self):
        return self.ananke.name

    @property
    def ngb(self):
        return self.ananke.ngb

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def densities(self):
        if self.__densities is None:
            return self._run_enbid()
        else:
            return self.__densities
    