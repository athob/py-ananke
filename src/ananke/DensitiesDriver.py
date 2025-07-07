#!/usr/bin/env python
"""
Contains the DensitiesDriver class definition

Please note that this module is private. The DensitiesDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict
from numpy.typing import NDArray
import pathlib
import enbid_ananke as EnBiD

from . import utils
from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['DensitiesDriver']


class DensitiesDriver:
    """
        Store the particle kernel densities and compute them if necessary.
    """
    _density_formatter = 'rho_{}'
    _density_template = _density_formatter.format
    def __init__(self, ananke: Ananke, **kwargs: Dict[str, Any]) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this DensitiesDriver object
            
            **kwargs
                Additional parameters to be used by the density estimator. In
                the current implementation, these include all the configurable
                parameters of EnBiD accessible through the class method
                display_EnBiD_docs
        """
        self.__ananke: Ananke = ananke
        self.__parameters: Dict[str, Any] = kwargs
        self.densities = self.particle_densities
    
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
        self.densities = {POS_TAG: rho_pos, VEL_TAG: rho_vel}
        return self.densities
    
    _run_enbid.__doc__ = _run_enbid.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)

    def _check_densities_format(self, densities):
        if densities is not None:
            if isinstance(densities, dict):
                utils.compare_given_and_required(densities.keys(), optional={POS_TAG, VEL_TAG}, error_message="Given densities dictionary has wrong set of keys")
                utils.confirm_equal_length_arrays_in_dict(densities, error_message_dict_name="densities")
            else:
                raise ValueError("Densities should be either None or a dictionary")

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
    def particle_densities(self) -> Dict[str, NDArray]:
        particle_densities = {}
        if self._density_template(POS_TAG) in self.ananke.particles:
            particle_densities[POS_TAG] = self.ananke.particles[self._density_template(POS_TAG)]
            if self._density_template(VEL_TAG) in self.ananke.particles:
                particle_densities[VEL_TAG] = self.ananke.particles[self._density_template(VEL_TAG)]
        # particle_densities = {
        #     key: self.ananke.particles[self._density_template(key)]
        #     for key in [POS_TAG, VEL_TAG]
        #     if self._density_template(key) in self.ananke.particles
        #     }
        return particle_densities
    
    @property
    def name(self):
        return self.ananke.name

    @property
    def ngb(self):
        return self.ananke.ngb

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters
    
    @property
    def densities(self):
        if self.__densities:
            return self.__densities
        else:
            return self._run_enbid()
    
    @densities.setter
    def densities(self, densities):
        self._check_densities_format(densities)
        self.__densities = densities
    
    @classmethod
    def display_EnBiD_docs(cls):
        """
            Print the EnBiD.run_enbid docstring
        """
        print(EnBiD.run_enbid.__doc__)


if __name__ == '__main__':
    raise NotImplementedError()
