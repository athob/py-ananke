#!/usr/bin/env python
"""
Contains the Universe class definition

Please note that this module is private. The Universe class is
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

__all__ = ['Universe']


class Universe:
    """
        Store the Universe parameters.
    """
    _rmin = 'r_min'
    _rmax = 'r_max'
    _rshell = [_rmin,_rmax]
    _default_rshell = np.array([DEFAULTS_FOR_PARFILE[_p] for _p in _rshell])

    def __init__(self, ananke: Ananke, rshell: ArrayLike, **kwargs: Dict[str, Any]) -> None:
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
        self.__ananke: Ananke = ananke
        self.__rshell: NDArray = self.__prepare_rshell(rshell)
        self.__parameters: Dict[str, Any] = kwargs
    
    def __prepare_rshell(self, rshell: ArrayLike) -> NDArray:
        rshell = np.array(rshell)
        rshell[np.isnan(rshell)] = self._default_rshell[np.isnan(rshell)]
        return rshell

    @property
    def ananke(self) -> Ananke:
        return self.__ananke

    @property
    def rshell(self) -> NDArray:
        return self.__rshell
    
    @property
    def to_galaxia_kwargs(self) -> Dict[str, float]:
        return dict(zip(self._rshell, self.rshell))
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters


if __name__ == '__main__':
    raise NotImplementedError()
