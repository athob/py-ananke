#!/usr/bin/env python
"""
Contains the Observer class definition

Please note that this module is private. The Observer class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict
from numpy.typing import ArrayLike, NDArray
import numpy as np
from galaxia_ananke._defaults import DEFAULTS_FOR_PARFILE

from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['Observer']


class Observer:  # TODO SkyCoord for center point: SkyCoord(u=-rSun[0], v=-rSun[1], w=-rSun[2], unit='kpc', representation_type='cartesian', frame='galactic')
    """
        Store the observer parameters.
    """
    _pos0 = 'rSun0'
    _pos1 = 'rSun1'
    _pos2 = 'rSun2'
    _pos = [_pos0,_pos1,_pos2]
    _default_position = np.array([DEFAULTS_FOR_PARFILE[_p] for _p in _pos])
    _vel0 = 'vSun0'
    _vel1 = 'vSun1'
    _vel2 = 'vSun2'
    _vel = [_vel0,_vel1,_vel2]
    _default_velocity = np.array([DEFAULTS_FOR_PARFILE[_p] for _p in _vel])
    _pha = _pos+_vel

    def __init__(self, ananke: Ananke, pos3: ArrayLike = None, vel3: ArrayLike = None, **kwargs: Dict[str, Any]) -> None:
        """
        Parameters
        ----------
        ananke : Ananke object
            The Ananke object that utilizes this Observer object
        pos3 : array-like shape (3,)
            Position of the observer. Default to None
        vel3 : array-like shape (3,)
            Velocity of the observer. Default to None
        **kwargs
            Additional parameters
        """
        self.__ananke: Ananke = ananke
        self.__position: NDArray = self.__prepare_position(pos3)
        self.__velocity: NDArray = self.__prepare_velocity(vel3)
        self.__parameters: Dict[str, Any] = kwargs

    @classmethod
    def __prepare_against_default(cls, vector: ArrayLike, default: NDArray) -> NDArray:
        vector = np.array(len(default)*[np.nan] if vector is None else vector)
        vector[np.isnan(vector)] = default[np.isnan(vector)]
        return vector
    
    def __prepare_position(self, pos: ArrayLike) -> NDArray:
        return self.__prepare_against_default(pos, self._default_position)

    def __prepare_velocity(self, vel: ArrayLike) -> NDArray:
        return self.__prepare_against_default(vel, self._default_velocity)

    @property
    def ananke(self) -> Ananke:
        return self.__ananke

    @property
    def position(self) -> NDArray:
        return self.__position
    
    @property
    def velocity(self) -> NDArray:
        return self.__velocity
    
    @property
    def phase_space(self) -> NDArray:
        return np.hstack([self.position, self.velocity])
    
    @property
    def to_galaxia_kwargs(self) -> Dict[str, float]:
        return dict(zip(self._pha, self.phase_space))
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters


if __name__ == '__main__':
    raise NotImplementedError()
