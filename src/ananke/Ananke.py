#!/usr/bin/env python
"""
Contains the Ananke class definition

Please note that this module is private. The Ananke class is
available in the main ``ananke`` namespace - use that instead.
"""
from warnings import warn
import numpy as np

import Galaxia_ananke as Galaxia

from .constants import *
from .Universe import Universe
from .Observer import Observer
from .Densities import Densities
from .Extinction import Extinction

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
        d_params : dict
            Parameters to configure the kernel density estimation
        e_params : dict
            Parameters to configure the extinction pipeline
        **kwargs
            Additional parameters used by the function
            make_survey_from_particles in Galaxia
        
        Notes
        -----
        The input particles must include same-length arrays for every key of
        the list of keys return by property required_particles_keys.
        Particular attention should be given to arrays of keys '{_pos}' and
        '{_vel}' that must be shaped as (Nx3) arrays of, respectively,
        position and velocity vectors.
    """
    _pos = Galaxia.Input._pos
    _vel = Galaxia.Input._vel
    _required_particles_keys = Galaxia.Input._required_keys_in_particles
    _optional_particles_keys = Galaxia.Input._optional_keys_in_particles
    _galaxia_particles_keys = _required_particles_keys.union(_optional_particles_keys)
    _photo_sys = "photo_sys"
    __doc__ = __doc__.format(_pos=_pos, _vel=_vel)

    def __init__(self, particles, name, ngb=64, d_params={}, e_params={}, **kwargs) -> None:
        self.__particles = particles
        self.__name = name
        self.__ngb = ngb
        self.__universe_proxy = self._prepare_universe_proxy(kwargs)
        self.__observer_proxy = self._prepare_observer_proxy(kwargs)
        self.__parameters = kwargs
        self.__densities_proxy = self._prepare_densities_proxy(d_params)
        self.__extinction_proxy = self._prepare_extinction_proxy(e_params)
        self.__galaxia_output = None

    def _prepare_universe_proxy(self, kwargs):
        _rshell = kwargs.pop('rshell', None)
        if _rshell is None:
            warn('The use of kwargs r_min & r_max will be deprecated, please use instead kwarg observer', DeprecationWarning, stacklevel=2)
            _rshell = np.array([kwargs.pop('r_min', np.nan), kwargs.pop('r_max', np.nan)])
        return Universe(self, _rshell)

    def _prepare_observer_proxy(self, kwargs):
        _obs = kwargs.pop('observer', None)
        if _obs is None:
            warn('The use of kwargs rSun0, rSun1 & rSun2 will be deprecated, please use instead kwarg observer', DeprecationWarning, stacklevel=2)
            _obs = np.array([kwargs.pop('rSun0', np.nan), kwargs.pop('rSun1', np.nan), kwargs.pop('rSun2', np.nan)])
        return Observer(self, _obs)

    def _prepare_densities_proxy(self, d_params):
        return Densities(self, **d_params)

    def _prepare_extinction_proxy(self, e_params):
        return Extinction(self, **e_params)

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
        output = Galaxia.make_survey_from_particles(self._galaxia_particles, rho[POS_TAG], rho[VEL_TAG], simname=self.name, ngb=self.ngb, **self._galaxia_kwargs) # TODO don't use that function, use & save Galaxia objects instead (example improvement is direct access to isochrone objects)
        self.__galaxia_output = output
        return self._galaxia_output
    
    _run_galaxia.__doc__ = _run_galaxia.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)
    
    def _run_extinction(self):
        """
            Method
        """
        return self._galaxia_output, self.extinctions

    def run(self):
        """
            Run the pipeline
        """
        self._run_galaxia(self.densities)
        return self._run_extinction()

    @property
    def particles(self):
        return self.__particles
    
    @property
    def particle_positions(self):
        return self.particles[self._pos]
    
    @property
    def particle_velocities(self):
        return self.particles[self._vel]

    @property
    def name(self):
        return self.__name

    @property
    def ngb(self):
        return self.__ngb
    
    @property
    def universe(self):
        return self.__universe_proxy
    
    @property
    def universe_rshell(self):
        return self.universe.rshell

    @property
    def observer(self):
        return self.__observer_proxy
    
    @property
    def observer_position(self):
        return self.observer.position
    
    @property
    def observer_velocity(self):
        return self.observer.velocity

    @property
    def densities(self):
        return self.__densities_proxy.densities
    
    @property
    def extinctions(self):
        return self.__extinction_proxy.extinctions

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def photo_sys(self):
        return self.parameters.get(self._photo_sys, Galaxia.DEFAULT_PSYS)

    @property
    def galaxia_isochrones(self):
        return Galaxia.Survey.set_isochrones_from_photosys(self.photo_sys)
    
    @property
    def galaxia_export_mag_names(self):
        return Galaxia.Output.Output._compile_export_mag_names(self.galaxia_isochrones)
    
    @property
    def galaxia_export_keys(self):
        return Galaxia.Output.Output._make_export_keys(self.galaxia_isochrones)

    @property
    def _galaxia_kwargs(self):
        return {**self.universe.to_galaxia_kwargs, **self.observer.to_galaxia_kwargs, **self.parameters}

    @property
    def _galaxia_particles(self):
        return {key: self.particles[key] for key in self._galaxia_particles_keys if key in self.particles}

    @property
    def _output(self):
        warn('This property will be deprecated, please use instead property _galaxia_output', DeprecationWarning, stacklevel=2)
        return self._galaxia_output

    @property
    def _galaxia_output(self):
        if self.__galaxia_output is None:
            raise RuntimeError("You must use the `run` method before accessing the catalogue")
        else:
            return self.__galaxia_output


if __name__ == '__main__':
    pass
