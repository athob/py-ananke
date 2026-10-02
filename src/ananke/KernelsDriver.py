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
Contains the KernelsDriver class definition

Please note that this module is private. The KernelsDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict, Callable
from numpy.typing import NDArray
from warnings import warn
import pathlib
import numpy as np
import enbid_ananke as EnBiD

from . import utils
from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['KernelsDriver']


class KernelsDriver:
    """
        Store the particle kernel characteristics and compute them if necessary.
    """
    _kernels = 'kernels'
    def __init__(self, ananke: Ananke, **kwargs: Dict[str, Any]) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this KernelsDriver object
            
            **kwargs
                Additional parameters to be used by the kernels estimator. In
                the current implementation, these include all the configurable
                parameters of EnBiD accessible through the class method
                display_EnBiD_docs (except `name` and `ngb`)
        """
        self.__ananke: Ananke = ananke
        self.__kernels_estimator: Optional[Callable] = kwargs.pop('kernels_estimator', None)
        self.__parameters: Dict[str, Any] = kwargs
        self.kernels = self.particle_kernels

    def __enbid_kernel_estimator(self, positions, velocities, masses, **kwargs):
        path = pathlib.Path(self.name)
        rho_pos = EnBiD.enbid(positions, mass=masses, name=path / POS_TAG, **kwargs)
        rho_vel = EnBiD.enbid(velocities, mass=masses, name=path / VEL_TAG, **kwargs)
        rho = EnBiD.enbid(positions, velocities=velocities, mass=masses, name=path / (POS_TAG+VEL_TAG), **kwargs)
        kernels_from_3d = np.cbrt(masses/(np.vstack([rho_pos, rho_vel])*4/3*np.pi)).T
        normalization_factors = ((masses/rho)/(np.pi**3/6*np.prod(kernels_from_3d**3, axis=1)))[:,None]**(1/6)
        kernels = normalization_factors*kernels_from_3d
        return kernels
    
    def _compute_kernels(self):
        """
            Method to generate via the estimator given at class construction
            the array of kernel sizes estimates that is needed to generate the
            survey from the pipeline particles
            
            Returns
            ----------
            kernels : array_like
                A (Nx2) array representing kernel sizes
                estimates for the pipeline particles
        """
        self.kernels = self._kernels_estimator(self.particle_positions, self.particle_velocities, self.particle_masses, ngb=self.ngb, **self.parameters)
        # path = pathlib.Path(self.name)
        # rho_pos = EnBiD.enbid(self.particle_positions, mass=self.particle_masses, name=path / POS_TAG, ngb=self.ngb, **self.parameters)
        # rho_vel = EnBiD.enbid(self.particle_velocities, mass=self.particle_masses, name=path / VEL_TAG, ngb=self.ngb, **self.parameters)
        # rho = EnBiD.enbid(self.particle_positions, velocities=self.particle_velocities, mass=self.particle_masses, name=path / (POS_TAG+VEL_TAG), ngb=self.ngb, **self.parameters)
        # kernels_from_3d = np.cbrt(self.particle_masses/(np.vstack([rho_pos, rho_vel])*4/3*np.pi)).T
        # normalization_factors = ((self.particle_masses/rho)/(np.pi**3/6*np.prod(kernels_from_3d**3, axis=1)))[:,None]**(1/6)
        # self.kernels = normalization_factors*kernels_from_3d
        return self.kernels

    def _run_enbid(self):
        warn('This method will be deprecated, please use instead method _compute_kernels', DeprecationWarning, stacklevel=2)
        return self._compute_kernels()

    def _check_kernels_format(self, kernels):
        if kernels is not None:
            pass  # TODO
            # if isinstance(kernels, NDArray):
            #     utils.compare_given_and_required(kernels.keys(), optional={POS_TAG, VEL_TAG}, error_message="Given kernels dictionary has wrong set of keys")
            #     utils.confirm_equal_length_arrays_in_dict(kernels, error_message_dict_name="kernels")
            # else:
            #     raise ValueError("Kernels should be either None or an array-like")

    @property
    def _kernels_estimator(self) -> Callable:
        if self.__kernels_estimator is None:
            return self.__enbid_kernel_estimator
        else:
            return self.__kernels_estimator

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
    def particle_masses(self):
        return self.ananke.particle_masses

    @property
    def particle_kernels(self) -> Optional[NDArray]:
        if self._kernels in self.ananke.particles:
            return self.ananke.particles[self._kernels]
        elif 'rho_pos' in self.ananke.particles:
            warn("The use of 'rho_pos' and 'rho_vel' keys to provide density estimates that inform kernels sizes will be removed in a future update in favour of the currently supported key 'kernels' to directly provides those kernel sizes", DeprecationWarning, stacklevel=2)
            particle_densities_stack = [self.ananke.particles['rho_pos']]
            if 'rho_vel' in self.ananke.particles:
                particle_densities_stack.append(self.ananke.particles['rho_vel'])
            return 1/np.cbrt(4/3*np.pi*np.vstack(particle_densities_stack).T)
    
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
    def kernels(self):
        if self.__kernels is not None:
            return self.__kernels
        else:
            return self._compute_kernels()
    
    @kernels.setter
    def kernels(self, kernels):
        self._check_kernels_format(kernels)
        self.__kernels = kernels
    
    @classmethod
    def display_EnBiD_docs(cls):
        """
            Print the EnBiD.run_enbid docstring
        """
        print(EnBiD.run_enbid.__doc__)


if __name__ == '__main__':
    raise NotImplementedError()
