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
from .DensitiesDriver import DensitiesDriver
from .ExtinctionDriver import ExtinctionDriver
from .ErrorModelDriver import ErrorModelDriver

__all__ = ['Ananke']


class Ananke:
    """
        Represents a single ananke pipeline.
    """
    _mass = Galaxia.Input._mass  # mass in solar masses
    _pos = Galaxia.Input._pos  # position in kpc
    _vel = Galaxia.Input._vel  # velocity in km/s
    _age = 'age'  # log age in yr 
    _feh = 'feh'  # [Fe/H] in dex relative to solar
    _alph = 'alpha'  # [Mg/Fe]
    _mg = 'magnesium'  # [Mg/H]
    _elem_list = ['helium', 'carbon', 'nitrogen', 'oxygen', 'neon', _mg, 'silicon', 'sulphur', 'calcium']  # other abundances in the list as [X/H]
    _par_id = 'parentid'  # indices of parent particles in snapshot
    _dform = 'dform'  # formation distance
    _required_particles_keys = Galaxia.Input._required_keys_in_particles
    _optional_particles_keys = Galaxia.Input._optional_keys_in_particles
    _galaxia_particles_keys = _required_particles_keys.union(_optional_particles_keys)
    _photo_sys = "photo_sys"
    _def_obs_position = Observer._default_position
    _def_uni_rshell = Universe._default_rshell
    _def_photo_sys = Galaxia.DEFAULT_PSYS
    _def_cmd_mags = Galaxia.DEFAULT_CMD
    _def_cmd_box = Galaxia.DEFAULT_CMD_BOX
    _observed_mag_formatter = '{}_Obs'
    _observed_mag_template = _observed_mag_formatter.format

    def __init__(self, particles, name, ngb=64, d_params={}, e_params={}, err_params={}, **kwargs) -> None:
        """
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
                Parameters to configure the extinction pipeline. Use class
                method display_extinction_docs to find what parameters can be
                defined

            err_params : dict
                Parameters to configure the error model pipeline. Use class
                method display_errormodel_docs to find what parameters can be
                defined

            observer : array-like shape (3,)
                Coordinates for the observer position in kpc. Default to
                {_def_obs_position}.
            
            rshell : array-like shape (2,)
                Range in kpc of distances from the observer position of the
                particles that are to be considered. Default to
                {_def_uni_rshell}.

            photo_sys : string or list
                Name(s) of the photometric system(s) Galaxia should use to
                generate the survey. Default to {_def_photo_sys}.
                Available photometric systems can be queried with the class
                method display_available_photometric_systems.

            cmd_magnames : string or dict
                Names of the filters Galaxia should use for the color-magnitude
                diagram box selection.
                The input can be given as string in which case it must meet the
                following format:
                    "band1,band2-band3"
                where band1 is the magnitude filter and (band2, band3) are the
                filters that define the band2-band3 color index.
                Alternatively, a dictionary can be passed with the following
                format:
                    dict('magnitude': band1,
                         'color_minuend': band2,
                         'color_subtrahend': band3)
                The filter names must correspond to filters that are part of
                the first chosen photometric system in photo_sys. Default to
                {_def_cmd_mags}.
                
            app_mag_lim_lo : float
            app_mag_lim_hi : float
            abs_mag_lim_lo : float
            abs_mag_lim_hi : float
            color_lim_lo : float
            color_lim_hi : float
                These allow to specify the limits of the chosen color-magnitude
                diagram box selection (lo for lower and hi for upper). app_mag,
                abs_mag and color represent respectively limits in apparent
                magnitudes, absolute magnitudes and color index. Default values
                follow those set in:
                {_def_cmd_box}.

            fsample : float
                Sampling rate from 0 to 1 for the resulting synthetic star
                survey. 1 returns a full sample while any value below returns
                partial surveys. Default to 1.
            
            Notes
            -----
            The input particles must include same-length arrays for every key of
            the list of keys return by property required_particles_keys.
            Particular attention should be given to arrays of keys '{_pos}' and
            '{_vel}' that must be shaped as (Nx3) arrays of, respectively,
            position and velocity vectors. Use the class method
            make_dummy_particles_input to generate a dummy example of such input
            dictionary.
        """
        self.__particles = particles
        self.__name = name
        self.__ngb = ngb
        self.__universe_proxy = self._prepare_universe_proxy(kwargs)
        self.__photo_sys = kwargs.pop(self._photo_sys, Galaxia.DEFAULT_PSYS)
        self.__observer_proxy = self._prepare_observer_proxy(kwargs)
        self.__parameters = kwargs
        self.__densitiesdriver_proxy = self._prepare_densitiesdriver_proxy(d_params)
        self.__extinctiondriver_proxy = self._prepare_extinctiondriver_proxy(e_params)
        self.__errormodeldriver_proxy = self._prepare_errormodeldriver_proxy(err_params)
        self.__galaxia_input = None
        self.__galaxia_survey = None
        self.__galaxia_output = None

    __init__.__doc__ = __init__.__doc__.format(_def_obs_position=_def_obs_position,
                                               _def_uni_rshell=_def_uni_rshell,
                                               _def_photo_sys=_def_photo_sys,
                                               _def_cmd_mags=_def_cmd_mags,
                                               _def_cmd_box=_def_cmd_box,
                                               _pos=_pos, _vel=_vel)

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

    def _prepare_densitiesdriver_proxy(self, d_params):
        return DensitiesDriver(self, **d_params)

    def _prepare_extinctiondriver_proxy(self, e_params):
        return ExtinctionDriver(self, **e_params)

    def _prepare_errormodeldriver_proxy(self, err_params):
        return ErrorModelDriver(self, **err_params)

    def _prep_galaxia_input(self, rho, knorm = 0.596831):
        if self.__galaxia_input is None:
            self.__galaxia_input = Galaxia.Input(self._galaxia_particles, rho[POS_TAG], rho[VEL_TAG], name=self.name, knorm=knorm, ngb=self.ngb)
        return self.__galaxia_input

    def _prep_galaxia_survey(self, input, surveyname = 'survey'):
        if self.__galaxia_survey is None:
            self.__galaxia_survey = Galaxia.Survey(input, photo_sys=self.photo_sys, surveyname=surveyname)
        return self.__galaxia_survey

    def _run_galaxia(self, rho, **kwargs):
        """
            Method to generate the survey out of the pipeline particles given
            a dictionary of kernel density estimates
            
            Parameters
            ----------
            rho : dict({POS_TAG}=array_like, {VEL_TAG}=array_like)
                A dictionary of same-length arrays representing kernel density
                estimates for the pipeline particles

            knorm : float
                TBD. Default to 0.596831.
                        
            surveyname : string
                Optional name Galaxia should use for the output files. Default
                to 'survey'.

            **kwargs
                Additional parameters used by the method make_survey of
                Galaxia's Survey objects

            Returns
            -------
            output : :obj:`Galaxia.Output`
                Handler with utilities to utilize the output survey and its data.
            """
        input = self._prep_galaxia_input(rho, **{k:kwargs.pop(k) for k in ['knorm'] if k in kwargs})
        survey = self._prep_galaxia_survey(input, **{k:kwargs.pop(k) for k in ['surveyname'] if k in kwargs})
        self.__galaxia_output = survey.make_survey(**self._galaxia_kwargs, **kwargs)
        return self._galaxia_output
    
    _run_galaxia.__doc__ = _run_galaxia.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG)
    
    def run(self, **kwargs):
        """
            Method to run the pipeline
            
            Parameters
            ----------
            knorm : float
                TBD. Default to 0.596831.
                        
            surveyname : string
                Optional name Galaxia should use for the output files. Default
                to 'survey'.

            **kwargs
                Additional parameters used by the method make_survey of
                Galaxia's Survey objects

            Returns
            -------
            galaxia_output : :obj:`Galaxia.Output`
                Handler with utilities to utilize the output survey and its data.
        """
        galaxia_output = self._run_galaxia(self.densities, **kwargs)
        if self._extinctiondriver_proxy._col_density in self.particles:
            _ = self.extinctions
        _ = self.errors
        return galaxia_output

    @property
    def _densitiesdriver_proxy(self):
        return self.__densitiesdriver_proxy

    @property
    def _extinctiondriver_proxy(self):
        return self.__extinctiondriver_proxy
    
    @property
    def _errormodeldriver_proxy(self):
        return self.__errormodeldriver_proxy

    @property
    def particles(self):
        return self.__particles
    
    @property
    def particle_masses(self):
        return self.particles[self._mass]
    
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
        return self._densitiesdriver_proxy.densities
    
    @property
    def extinctions(self):
        return self._extinctiondriver_proxy.extinctions

    @property
    def errors(self):
        return self._errormodeldriver_proxy.errors

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def photo_sys(self):
        return self.__photo_sys

    @property
    def galaxia_isochrones(self):  # TODO race condition with the implementation in extinction using the following 3 properties, requires rethinking Galaxia, maybe with the future photometryspecs implementation: ultimate goal is to get isochrones from a Galaxia object without explicitely calling Galaxia class methods
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
    
    @classmethod
    def make_dummy_particles_input(cls, n_parts=10**5):  # TODO consider moving part of that method to Galaxia Input?
        """
            Generate an example dummy input particles dictionary for Ananke
            made of randomly generated arrays.

            Parameters
            ----------
            n_parts : int
                Number of particles the example include. Default to 10**5.

            Returns
            -------
            p : dict
                Dummy example input particles for Ananke.
        """
        p = {}
        p[cls._pos] = 30*np.random.randn(n_parts, 3)
        p[cls._vel] = 50*np.random.randn(n_parts, 3)
        p[cls._mass] = 5500 + 700*np.random.randn(n_parts)
        p[cls._age] = 9.7 + 0.4*np.random.randn(n_parts)
        p[cls._feh] = -0.7 + 0.4*np.random.randn(n_parts)
        for el in cls._elem_list:
            p[el] = -0.6 + 0.4*np.random.randn(n_parts)
        p[cls._alph] = p[cls._mg] - p[cls._feh]
        p[cls._par_id] = np.arange(n_parts)
        p[cls._dform] = np.zeros(n_parts, dtype='float32')
        p[ExtinctionDriver._col_density] = 22 + np.random.randn(n_parts)
        return p
    
    @classmethod
    def display_available_photometric_systems(cls):
        """
            Return a nested dictionary of all photometric systems that are
            available in Galaxia.

            Returns
            -------
            available_photo_systems : dict
                Dictionary of dictionaries of Isochrone objects.
        """
        return Galaxia.photometry.available_photo_systems

    @classmethod
    def display_extinction_docs(cls):
        """
            Print the ExtinctionDriver constructor docstring
        """
        print(ExtinctionDriver.__init__.__doc__)

    @classmethod
    def display_errormodel_docs(cls):
        """
            Print the ErrorModelDriver constructor docstring
        """
        print(ErrorModelDriver.__init__.__doc__)


if __name__ == '__main__':
    pass
