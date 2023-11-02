#!/usr/bin/env python
"""
Contains the Universe class definition

Please note that this module is private. The Universe class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
import numpy.typing  # needed for python==3.7
from Galaxia_ananke.constants import DEFAULTS_FOR_PARFILE

from .constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['Universe']


class Universe:
    """
        Store the Universe parameters.
    """
    _rmin = 'r_min'
    _rmax = 'r_max'
    _rshell = [_rmin,_rmax]
    _default_rshell = np.array([DEFAULTS_FOR_PARFILE[_p] for _p in _rshell])

    def __init__(self, ananke: Ananke, rshell: np.typing.ArrayLike, **kwargs) -> None:
        """
        Parameters
        ----------
        ananke : Ananke object
            The Ananke object that utilizes this Universe object
        rshell : array-like shape (2,)
            Range of distances from the observer position of the
            particles that are to be considered.
        **kwargs
            Additional parameters
        """
        self.__ananke = ananke
        self.__rshell = self.__prepare_rshell(rshell)
        self.__parameters = kwargs
    
    def __prepare_rshell(self, rshell: np.typing.ArrayLike):
        rshell = np.array(rshell)
        rshell[np.isnan(rshell)] = self._default_rshell[np.isnan(rshell)]
        return rshell

    @property
    def ananke(self):
        return self.__ananke

    @property
    def rshell(self):
        return self.__rshell
    
    @property
    def to_galaxia_kwargs(self):
        return dict(zip(self._rshell, self.rshell))
        
    @property
    def parameters(self):
        return self.__parameters
    