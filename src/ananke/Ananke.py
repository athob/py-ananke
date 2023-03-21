#!/usr/bin/env python
"""
Contains the Ananke class definition

Please note that this module is private. The Ananke class is
available in the main ``ananke`` namespace - use that instead.
"""
import pathlib
import EnBiD
import Galaxia

from .constants import *

__all__ = ['Ananke']


class Ananke:
    """
        Represents a single ananke pipeline.

        Parameters
        ----------
        particles : dict
            A dictionary of same-length arrays representing particles
            data of a stellar population - see notes for formatting
        name : str
            Name for the pipeline
        ngb : int
            Number of neighbours to use in kernel density estimation
        **kwargs
            Additional parameters used by the function
            make_survey_from_particles in Galaxia
        
        Notes
        -----
        The input particles must include same_length arrays for every key of
        the list of keys return by property required_particles_keys.
        Particular attention should be given to arrays of keys '{_pos}' and
        '{_vel}' that must be shaped as (Nx3) arrays of, respectively,
        position and velocity vectors.
    """
    _pos = 'pos3'
    _vel = 'vel3'
    _required_particles_keys = Galaxia.Input._required_keys_in_particles
    __doc__ = __doc__.format(_pos=_pos, _vel=_vel)

    def __init__(self, particles, name, ngb=64, **kwargs) -> None:
        self.__particles = particles
        self.__name = name
        self.__ngb = ngb
        self.__parameters = kwargs
        self.__output = None
    
    def _run_enbid(self):
        """
            Method to generate the dictionary of kernel density estimates that
            is needed to generate the survey from the pipeline particles
            
            Returns
            ----------
            rho : dict({POS_TAG}=array_like, {VEL_TAG}=array_like)
                A dictionary of same-length arrays representing kernel density
                estimates for the pipeline particles
        """
        path = pathlib.Path(self.name)
        rho_pos = EnBiD.enbid(self.particles[self._pos], name=path / POS_TAG, ngb=self.ngb)
        rho_vel = EnBiD.enbid(self.particles[self._vel], name=path / VEL_TAG, ngb=self.ngb)
        return {POS_TAG: rho_pos, VEL_TAG: rho_vel}
    
    _run_enbid.__doc__ = _run_enbid.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)

    def _run_galaxia(self, rho):
        """
            Method to generate the survey out of the pipeline particles given
            a dictionary of kernel density estimates
            
            Parameters
            ----------
            rho : dict({POS_TAG}=array_like, {VEL_TAG}=array_like)
                A dictionary of same-length arrays representing kernel density
                estimates for the pipeline particles
        """
        output = Galaxia.make_survey_from_particles(self.particles, rho[POS_TAG], rho[VEL_TAG], simname=self.name, ngb=self.ngb, **self.parameters)
        self.__output = output
    
    _run_galaxia.__doc__ = _run_galaxia.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)
    
    def run(self):
        """
            Run the pipeline
        """
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
    def required_particle_keys(self):
        return self._required_particles_keys

    @property
    def _output(self):
        if self.__output is None:
            raise RuntimeError("You must use the `run` method before accessing the catalogue")
        else:
            return self.__output


if __name__ == '__main__':
    pass
