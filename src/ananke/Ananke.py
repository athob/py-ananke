#!/usr/bin/env python
"""
Contains the Ananke class definition

Please note that this module is private. The Ananke class is
available in the main ``ananke`` namespace - use that instead.
"""
from typing import TYPE_CHECKING, Any, Optional, Union, Tuple, List, Dict, Iterable
from numpy.typing import NDArray
from galaxia_ananke.photometry.PhotoSystem import PhotoSystem
from warnings import warn
import re
import numpy as np
import pandas as pd
from astropy import units, coordinates

import galaxia_ananke as Galaxia
import galaxia_ananke.photometry as Galaxia_photo

from . import utils
from ._constants import *
from .Universe import Universe
from .Observer import Observer
from .DensitiesDriver import DensitiesDriver
from .ExtinctionDriver import ExtinctionDriver
from .ErrorModelDriver import ErrorModelDriver
from .IntegratedLightDriver import IntegratedLightDriver


__all__ = ['Ananke']


class Ananke:
    """
        Represents a single ananke pipeline.
    """
    _mass = Galaxia.Input._mass  # mass in solar masses
    _pos = Galaxia.Input._pos  # position in kpc
    _vel = Galaxia.Input._vel  # velocity in km/s
    _age = Galaxia.Input._age  # log age in yr 
    _feh = Galaxia.Input._feh  # [Fe/H] in dex relative to solar
    # _alph = Galaxia.Input._alph  # [Mg/Fe]
    # _elem_list = Galaxia.Input._elem_list  # other abundances in the list as [X/H]
    _par_id = Galaxia.Input._parentid  # indices of parent particles in snapshot
    # _dform = Galaxia.Input._dform  # formation distance
    _rho_pos = DensitiesDriver._density_template(POS_TAG)
    _rho_vel = DensitiesDriver._density_template(VEL_TAG)
    _log10NH = ExtinctionDriver._col_density
    _required_particles_keys = Galaxia.Input._required_keys_in_particles
    _optional_particles_keys = Galaxia.Input._optional_keys_in_particles
    _galaxia_particles_keys = _required_particles_keys.union(_optional_particles_keys)
    _photo_sys = "photo_sys"
    _def_obs_position = Observer._default_position
    _def_obs_velocity = Observer._default_velocity
    _def_uni_rshell = Universe._default_rshell
    _def_photo_sys = Galaxia.DEFAULT_PSYS
    _def_cmd_mags = Galaxia.DEFAULT_CMD
    _intrinsic_mag_formatter = '{}_Intrinsic'
    _intrinsic_mag_template = _intrinsic_mag_formatter.format

    def __init__(self, particles: Dict[str, NDArray], name: str, ngb: int = 64, caching: bool = False, append_hash: Optional[bool] = None,
                 d_params: Dict[str, Any] = {}, e_params: Dict[str, Any] = {}, err_params: Dict[str, Any] = {}, il_params: Dict[str, Any] = {},
                 **kwargs: Dict[str, Any]) -> None:
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

            caching : bool
                EXPERIMENTAL: activate caching mode at every steps to resume
                work where it was left at from a previous python instance if
                needed. Default to True.

            append_hash : bool
                TODO

            d_params : dict
                Parameters to configure the kernel density estimation. Use
                class method ``display_density_docs`` to find what parameters
                can be defined

            e_params : dict
                Parameters to configure the extinction pipeline. Use class
                method ``display_extinction_docs`` to find what parameters can
                be defined

            err_params : dict
                Parameters to configure the error model pipeline. Use class
                method ``display_errormodel_docs`` to find what parameters can
                be defined

            il_params : dict
                Parameters to configure the integrated light pipeline. Use
                class method ``display_integratedlight_docs`` to find what
                parameters can be defined

            observer : array-like shape (3,) or dict of array-like shape (3,)
                Coordinates for the observer in phase space. Position and
                velocity quantities must respectively be given in kpc and km/s.
                To only specify position, an array-like object of shape (3,) is
                enough. If specifying both position and velocity, please
                provide a dictionary containing both coordinates as array-like
                objects of shape (3,), respectively denoting the position and
                velocity coordinates with keys ``{_pos}`` and ``{_vel}``.
                Position coordinates default to::
                
                    {_def_obs_position}
                
                and velocity coordinates default to::
                
                    {_def_obs_velocity}
            
            rshell : array-like shape (2,)
                Range in kpc of distances from the observer position of the
                particles that are to be considered. Default to::
                
                    {_def_uni_rshell}

            photo_sys : string or list
                Name(s) of the photometric system(s) Galaxia should use to
                generate the survey. Default to ``{_def_photo_sys}``.
                Available photometric systems can be queried with the class
                method ``display_available_photometric_systems``.

            cmd_magnames : string or dict
                Names of the filters Galaxia should use for the color-magnitude
                diagram box selection.
                The input can be given as string in which case it must meet the
                following format::

                    "band1,band2-band3"
                
                where ``band1`` is the magnitude filter and ``(band2, band3)``
                are the filters that define the ``band2-band3`` color index.
                Alternatively, a dictionary can be passed with the following
                format::

                    dict('magnitude': band1,
                         'color_minuend': band2,
                         'color_subtrahend': band3)
                
                The filter names must correspond to filters that are part of
                the first chosen photometric system in photo_sys. Default to
                ``'{_def_cmd_mags}'``.
            {parameters_from_galaxia}
            
            Notes
            -----
            The input particles must include same-length arrays for every key
            of the list of keys return by property required_particles_keys.
            Particular attention should be given to arrays of keys ``'{_pos}'``
            and ``'{_vel}'`` that must be shaped as (Nx3) arrays of,
            respectively, position and velocity vectors. Use the class method
            ``make_dummy_particles_input`` to generate a dummy example of such
            input dictionary.
        """
        self.__particles: Dict[str, NDArray] = particles
        self.__name: str = name
        self.__ngb: int = ngb
        self.__universe_proxy: Universe = self._prepare_universe_proxy(kwargs)
        self.__photo_sys: str = kwargs.pop(self._photo_sys, Galaxia.DEFAULT_PSYS)
        self.__observer_proxy: Observer = self._prepare_observer_proxy(kwargs)
        self.__parameters: Dict[str, Any] = kwargs
        self.__densitiesdriver_proxy: DensitiesDriver = self._prepare_densitiesdriver_proxy(d_params)
        self.__extinctiondriver_proxy: ExtinctionDriver = self._prepare_extinctiondriver_proxy(e_params)
        self.__errormodeldriver_proxy: ErrorModelDriver = self._prepare_errormodeldriver_proxy(err_params)
        self.__integratedlightdriver_proxy: IntegratedLightDriver = self._prepare_integratedlightdriver_proxy(il_params)
        self.__galaxia_input: Union[Galaxia.Input, None] = None
        self.__galaxia_survey: Union[Galaxia.Survey, None] = None
        self.__galaxia_output: Union[Galaxia.Output, None] = None
        self.caching: bool = caching
        self.append_hash: bool = append_hash

    __init__.__doc__ = __init__.__doc__.format(_def_obs_position=_def_obs_position,
                                               _def_obs_velocity=_def_obs_velocity,
                                               _def_uni_rshell=_def_uni_rshell,
                                               _def_photo_sys=_def_photo_sys,
                                               parameters_from_galaxia = utils.extract_parameters_from_docstring(
                                                   Galaxia.Survey.make_survey.__doc__,
                                                   parameters=[
                                                       'fsample',
                                                       'app_mag_lim_lo, app_mag_lim_hi, abs_mag_lim_lo, abs_mag_lim_hi, color_lim_lo, color_lim_hi'
                                                    ]).replace("\n", "\n            "),
                                               _def_cmd_mags=_def_cmd_mags,
                                               _pos=_pos, _vel=_vel)

    def _prepare_universe_proxy(self, kwargs: Dict[str, Any]) -> Universe:
        _rshell = kwargs.pop('rshell', None)
        if _rshell is None:
            warn('The use of kwargs r_min & r_max will be deprecated, please use instead kwarg observer', DeprecationWarning, stacklevel=2)
            _rshell = np.array([kwargs.pop('r_min', np.nan), kwargs.pop('r_max', np.nan)])
        return Universe(self, _rshell)

    def _prepare_observer_proxy(self, kwargs: Dict[str, Any]) -> Observer:
        _obs = kwargs.pop('observer', None)
        if _obs is None and re.match(',rSun[012],', ',,'.join(kwargs.keys())):
            _obs = {self._pos: np.array([kwargs.pop('rSun0', np.nan), kwargs.pop('rSun1', np.nan), kwargs.pop('rSun2', np.nan)])}
            warn('The use of kwargs rSun0, rSun1 & rSun2 will be deprecated, please use instead kwarg observer', DeprecationWarning, stacklevel=2)
        elif not isinstance(_obs, dict):
            _obs = {self._pos: _obs}
        for key in ['pos', 'vel']:
            if key in _obs.keys():
                new_key = getattr(self, f'_{key}')
                warn(f"The use of key '{key}' in the observer dictionary will be deprecated, please use instead key '{new_key}'", DeprecationWarning, stacklevel=2)
                _obs[new_key] = _obs.pop(key)
        return Observer(self, **_obs)

    def _prepare_densitiesdriver_proxy(self, d_params: Dict[str, Any]) -> DensitiesDriver:
        return DensitiesDriver(self, **d_params)

    def _prepare_extinctiondriver_proxy(self, e_params: Dict[str, Any]) -> ExtinctionDriver:
        return ExtinctionDriver(self, **e_params)

    def _prepare_errormodeldriver_proxy(self, err_params: Dict[str, Any]) -> ErrorModelDriver:
        return ErrorModelDriver(self, **err_params)

    def _prepare_integratedlightdriver_proxy(self, il_params: Dict[str, Any]) -> IntegratedLightDriver:
        return IntegratedLightDriver(self, **il_params)

    def _prepare_galaxia_input(self, rho: Dict[str, NDArray], **kwargs) -> Galaxia.Input:
        input_kwargs = {'name': self.name, 'ngb': self.ngb, 'caching': self.caching}
        if self.append_hash is not None:  input_kwargs['append_hash'] = self.append_hash
        input_kwargs = {**input_kwargs, **kwargs}  # input_dir, k_factor
        if self.__galaxia_input is None:
            self.__galaxia_input = Galaxia.Input(self._galaxia_particles, rho[POS_TAG], rho.get(VEL_TAG), **input_kwargs)
        return self.__galaxia_input

    def _prepare_galaxia_survey(self, input: Galaxia.Input, **kwargs) -> Galaxia.Survey:
        survey_kwargs = {'photo_sys': self.photo_sys, **kwargs}  # surveyname
        if self.__galaxia_survey is None:
            self.__galaxia_survey = Galaxia.Survey(input, **survey_kwargs)
        return self.__galaxia_survey

    def _run_galaxia(self, rho: Dict[str, NDArray], **kwargs) -> Galaxia.Output:
        """
            Method to generate the survey out of the pipeline particles given
            a dictionary of kernel density estimates
            
            Parameters
            ----------
            rho : dict({POS_TAG}=array_like, {VEL_TAG}=array_like)
                A dictionary of same-length arrays representing kernel density
                estimates for the pipeline particles

            input_dir, output_dir : string
                Optional arguments to specify paths for the directories where
                ananke should generate input and output data.
                
            k_factor : float
                Scaling factor applied to the kernels lengths to adjust all
                the kernels sizes uniformly. Lower values reduces the kernels
                extents, while higher values increases them.
                Default to 1 (no adjustment).
                 
            surveyname : string
                Optional name Galaxia should use for the output files. Default
                to 'survey'.
            {parameters_from_galaxia}

            Returns
            -------
            output : :obj:`Galaxia.Output`
                Handler with utilities to utilize the output survey and its data.

            Notes
            -----
            {notes_from_galaxia_output}
            """
        input: Galaxia.Input = self._prepare_galaxia_input(rho, **{k:kwargs.pop(k) for k in ['input_dir', 'k_factor'] if k in kwargs})
        survey: Galaxia.Survey = self._prepare_galaxia_survey(input, **{k:kwargs.pop(k) for k in ['surveyname'] if k in kwargs})
        self.__galaxia_output: Galaxia.Output = survey.make_survey(**self._galaxia_kwargs, **kwargs)
        return self._galaxia_output

    _run_galaxia.__doc__ = _run_galaxia.__doc__.format(POS_TAG=POS_TAG, VEL_TAG=VEL_TAG,
                                                       parameters_from_galaxia = utils.extract_parameters_from_docstring(
                                                           Galaxia.Survey.make_survey.__doc__,
                                                           ignore=[
                                                               'fsample', 'cmd_magnames', 'parfile', 'output_dir',
                                                               'rSun0, rSun1, rSun2', 'vSun0, vSun1, vSun2', 'r_max, r_min',
                                                               'app_mag_lim_lo, app_mag_lim_hi, abs_mag_lim_lo, abs_mag_lim_hi, color_lim_lo, color_lim_hi'
                                                            ]).replace("\n", "\n            "),
                                                       notes_from_galaxia_output = utils.extract_notes_from_docstring(
                                                           Galaxia.Output.__init__.__doc__).replace("\n", "\n            "))

    @classmethod
    def __pp_observed_mags(cls, df: utils.PDOrVaexDF, mag_names: Iterable[str], _dmod: str) -> None:
        for mag in mag_names:
            intrinsic_mag = cls._intrinsic_mag_template(mag)
            if intrinsic_mag not in df.columns:
                df[intrinsic_mag] = df[mag]
            i_max_dmod = np.abs(df[_dmod] if isinstance(df, pd.DataFrame) else df[_dmod].to_pandas_series()).argmax()
            max_dmod = df[_dmod][i_max_dmod:i_max_dmod+1].to_numpy()[0]
            mag_at_max_dmod = df[mag][i_max_dmod:i_max_dmod+1].to_numpy()[0]
            int_mag_at_max_dmod = df[intrinsic_mag][i_max_dmod:i_max_dmod+1].to_numpy()[0]
            if np.abs(int_mag_at_max_dmod + max_dmod - mag_at_max_dmod) > 2*np.abs(np.nextafter(int_mag_at_max_dmod, mag_at_max_dmod)-int_mag_at_max_dmod):
                df[mag] += df[_dmod]

    def _pp_observed_mags(self, galaxia_output: Galaxia.Output) -> None:
        pipeline_name = "observed_magnitudes"
        print(f"Running {pipeline_name} post-processing pipeline")
        mag_names = self.galaxia_catalogue_mag_names
        galaxia_output.apply_post_process_pipeline_and_flush(self.__pp_observed_mags, mag_names, galaxia_output._dmod, flush_with_columns=mag_names)

    def _pp_extinctions(self) -> None:
        pipeline_name = "extinctions"
        print(f"Running {pipeline_name} post-processing pipeline")
        if self._extinctiondriver_proxy._col_density in self.particles or self._extinctiondriver_proxy.mw_model is not None:
            _ = self.extinctions

    def _pp_errors(self) -> None:
        pipeline_name = "error_modeling"
        print(f"Running {pipeline_name} post-processing pipeline")
        if not self._errormodeldriver_proxy.ignore:
            _ = self.errors

    def run(self, caching: Optional[bool] = None, append_hash: Optional[bool] = None,
                  no_post_processing: Optional[bool] = False, **kwargs) -> Galaxia.Output:
        """
            Method to run the pipeline
            
            Parameters
            ----------
            caching : bool
                EXPERIMENTAL: activate caching mode at every steps to resume
                work where it was left at from a previous python instance if
                needed. Default to existing caching given to object at
                construction.

            append_hash : bool
                Only relevant if caching is active. When True, ananke
                automatically adds truncated hashes to all files it produces,
                to uniquely identify them. Default to True.

            input_dir, output_dir, i_o_dir : string
                Optional arguments to specify paths for the directories where
                ananke should generate input and output data. If the i_o_dir
                keyword argument is provided, it overrides any path given to
                the input_dir and output_dir keyword arguments.

            no_post_processing : bool
                If True, ignore the post-processing pipeline following the
                galaxia_ananke run. This post-processing pipeline involves
                the replacement of absolute magnitude quantities by their
                apparent ones, followed by the extinction estimation pipeline
                and by the error model application. Default to False.
            {parameters_from_run_galaxia}

            Returns
            -------
            galaxia_output : :obj:`Galaxia.Output`
                Handler with utilities to utilize the output survey and its
                data.
            
            Notes
            -----
            {notes_from_run_galaxia}

            Ananke complements this set of properties with those that are
            generated from its various post-processing subroutines. As a result
            the ``photosys_filtername``-formatted columns contain the apparent
            photometry, computed with addition of extinction and instrument
            error. Each component contributing to this final apparent
            photometry are stored in other columns with the
            ``photosys_filtername`` format with relevant prefixing/suffixing as
            listed below:
            
            * The intrinsic photometry are stored in the suffixed ``{_Intrinsic}`` keys
            * The extinction values are stored in the prefixed ``{A_}`` keys
            * The properties' standard error are stored in the suffixed ``{_Sig}`` keys
            * The properties' actually drawn gaussian error are stored in the suffixed ``_Err`` keys

            Note that because the error model generally also affect astrometry,
            the latter 2 suffixing rules also apply to the astrometric
            properties.
            
            The extinction post-processing routine also add 3 properties:

            * The line-of-sight hydrogen column density in {log10_NH_unit} and decimal logarithmic scale via key ``{log10_NH}``
            * The reddening index via key ``{E_B_V}``
            * The reference extinction (which extinction coefficients are based on) via key ``{A_0}``
        """
        if caching is not None:  self.caching: bool = caching
        if append_hash is not None:  self.append_hash: bool = append_hash
        if 'i_o_dir' in kwargs:  kwargs['input_dir'] = kwargs['output_dir'] = kwargs.pop('i_o_dir')
        galaxia_output: Galaxia.Output = self._run_galaxia(self.densities, **kwargs)
        if not no_post_processing:
            galaxia_output.check_state_before_running(description="ananke_pp_observed_mags")(self._pp_observed_mags)(galaxia_output)
            galaxia_output.check_state_before_running(description="ananke_pp_extinctions", level=1)(self._pp_extinctions)()
            galaxia_output.check_state_before_running(description="ananke_pp_errors", level=1)(self._pp_errors)()
        return galaxia_output

    run.__doc__ = run.__doc__.format(
        parameters_from_run_galaxia = utils.extract_parameters_from_docstring(
            _run_galaxia.__doc__,
            ignore=['input_dir, output_dir', 'rho']).replace("\n", "\n            "),
        notes_from_run_galaxia = utils.extract_notes_from_docstring(
            _run_galaxia.__doc__).replace("\n", "\n            "),
        _Intrinsic = _intrinsic_mag_template(""),
        A_ = "A_",  # TODO
        _Sig = "_Sig",
        _Err = "_Err",
        log10 = "$log_{10}$",
        log10_NH_unit = "$cm^{-2}$",
        log10_NH = _log10NH,
        E_B_V = "E(B-V)",
        A_0 = "A_0")

    @property
    def _densitiesdriver_proxy(self) -> DensitiesDriver:
        return self.__densitiesdriver_proxy

    @property
    def _extinctiondriver_proxy(self) -> ExtinctionDriver:
        return self.__extinctiondriver_proxy

    @property
    def _errormodeldriver_proxy(self) -> ErrorModelDriver:
        return self.__errormodeldriver_proxy

    @property
    def _integratedlightdriver_proxy(self) -> IntegratedLightDriver:
        return self.__integratedlightdriver_proxy

    @property
    def particles(self) -> Dict[str, NDArray]:
        return self.__particles

    @property
    def particle_masses(self) -> NDArray:
        return self.particles[self._mass]

    @property
    def particle_positions(self) -> NDArray:
        return self.particles[self._pos]

    @property
    def particle_velocities(self) -> NDArray:
        return self.particles[self._vel]

    @property
    def particle_metallicities(self) -> NDArray:
        return self.particles[self._feh]

    @property
    def particle_ages(self) -> NDArray:
        return self.particles[self._age]

    @property
    def particle_parentids(self) -> NDArray:
        return self.particles[self._par_id] if self._par_id in self.particles else np.arange(self.particle_masses.shape[0])

    @property
    def name(self) -> str:
        return self.__name

    @property
    def ngb(self) -> int:
        return self.__ngb

    @property
    def caching(self) -> bool:
        return self.__caching

    @caching.setter
    def caching(self, value: bool) -> None:
        if value:
            warn(f"You have requested caching mode, be aware this feature is currently experimental and may result in unintended behaviour.", DeprecationWarning, stacklevel=2)
        self.__caching: bool = value
        self._densitiesdriver_proxy.parameters['caching'] = self.caching
      
    @property
    def append_hash(self) -> bool:
        return self.__append_hash

    @append_hash.setter
    def append_hash(self, value: bool) -> None:
        self.__append_hash: bool = value

    @property
    def universe(self) -> Universe:
        return self.__universe_proxy

    @property
    def universe_rshell(self) -> NDArray:
        return self.universe.rshell

    @property
    def observer(self) -> Observer:
        return self.__observer_proxy

    @property
    def observer_position(self) -> NDArray:
        return self.observer.position

    @property
    def observer_velocity(self) -> NDArray:
        return self.observer.velocity

    @property
    def particle_observed_positions(self) -> NDArray:
        return self.particle_positions - self.observer_position

    @property
    def particle_observed_velocities(self) -> NDArray:
        return self.particle_velocities - self.observer_velocity

    @property
    def particle_observed_distances(self) -> NDArray:
        return np.linalg.norm(self.particle_observed_positions, axis=1)

    @property
    def particle_input_kernels(self) -> NDArray:
        return self._galaxia_input.kernels
    
    @property
    def particle_input_position_kernels(self) -> NDArray:
        return self.particle_input_kernels.T[0]
    
    @property
    def particle_input_velocity_kernels(self) -> NDArray:
        return self.particle_input_kernels.T[1]
    
    @property
    def particle_nearest_observed_distances(self) -> NDArray:
        return np.clip(self.particle_observed_distances - self.particle_input_position_kernels, 0.01, np.inf)
    
    @property
    def particle_nearest_observed_distmod(self) -> NDArray:
        return coordinates.Distance(self.particle_nearest_observed_distances*units.kpc).distmod.value

    @property
    def densities(self) -> Dict[str, NDArray]:
        return self._densitiesdriver_proxy.densities

    @property
    def extinctions(self):  # TODO figure out output typing
        return self._extinctiondriver_proxy.extinctions

    @property
    def errors(self):  # TODO figure out output typing
        return self._errormodeldriver_proxy.errors

    @property
    def residuals(self):
        return self._integratedlightdriver_proxy.particle_residual_photometry

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters

    @property
    def photo_sys(self) -> str:
        return self.__photo_sys

    @property
    def galaxia_photosystems(self) -> List[PhotoSystem]:  # TODO race condition with the implementation in extinction using the following 3 properties, requires rethinking Galaxia, maybe with the future photometryspecs implementation: ultimate goal is to get isochrones from a Galaxia object without explicitely calling Galaxia class methods
        return Galaxia.Survey.prepare_photosystems(self.photo_sys)
   
    @property
    def galaxia_isochrones(self):
        warn('This property will be deprecated, please use instead property galaxia_photosystems', DeprecationWarning, stacklevel=2)
        return self.galaxia_photosystems

    @property
    def galaxia_catalogue_mag_names(self) -> Tuple[str]:
        return Galaxia.Output._compile_export_mag_names(self.galaxia_photosystems)

    @property
    def intrinsic_catalogue_mag_names(self) -> Tuple[str]:
        return tuple(map(self._intrinsic_mag_template, self.galaxia_catalogue_mag_names))

    @property
    def galaxia_catalogue_mag_and_astrometrics(self) -> Tuple[str]:
        return self.galaxia_catalogue_mag_names + (Galaxia.Output._pi,) + Galaxia.Output._cel + Galaxia.Output._mu + (Galaxia.Output._vr,)

    @property
    def galaxia_catalogue_keys(self) -> Tuple[str]:
        return Galaxia.Output._make_catalogue_keys(self.galaxia_photosystems)

    @property
    def photosystems_zeropoints(self) -> units.Quantity:
        return np.hstack([ps.zeropoints for ps in self.galaxia_photosystems])

    @property
    def photosystems_zeropoints_dict(self) -> Dict[str, units.Quantity]:
        return dict(zip(self.galaxia_catalogue_mag_names, self.photosystems_zeropoints))

    @property
    def _galaxia_kwargs(self) -> Dict[str, Any]:
        return {**self.universe.to_galaxia_kwargs, **self.observer.to_galaxia_kwargs, **self.parameters}

    @property
    def _galaxia_particles(self) -> Dict[str, NDArray]:
        return {key: self.particles[key] for key in self._galaxia_particles_keys if key in self.particles}

    @property
    def _output(self):
        warn('This property will be deprecated, please use instead property _galaxia_output', DeprecationWarning, stacklevel=2)
        return self._galaxia_output

    @property
    def _galaxia_output(self) -> Galaxia.Output:
        if self.__galaxia_output is None:
            raise RuntimeError("You must use the `run` method before accessing the catalogue")
        else:
            return self.__galaxia_output

    @property
    def _galaxia_survey(self) -> Galaxia.Survey:
        return self._galaxia_output.survey

    @property
    def _galaxia_input(self) -> Galaxia.Input:
        return self._galaxia_survey.input

    @classmethod
    def make_dummy_dictionary_description(cls) -> str:
        description = """{particles_dictionary_description}
            Ananke compute the phase space densities that are used to
            determine particle smoothing lengths, but the dictionary can
            include pre-computed densities with the following entries:
            {density_properties}
        """.format(particles_dictionary_description=Galaxia.Input.particles_dictionary_description,
                   density_properties=''.join(
                       [f"\n            * {desc} via key ``{str(key)}``"
                        for key, desc in [Galaxia.Input._positiondensity_prop,
                                          Galaxia.Input._velocitydensity_prop]]))
        return description

    @classmethod
    def make_dummy_particles_input(cls, n_parts=10**5, with_densities=False) -> Dict[str, NDArray]:
        """
            Generate an example dummy input particles dictionary for Ananke
            made of randomly generated arrays.

            Parameters
            ----------
            n_parts : int
                Number of particles the example include. Default to 10**5.
            
            with_densities : bool
                Flag to include dummy densities estimates in the returned
                dictionary. Default to False

            Returns
            -------
            p : dict
                Dummy example input particles dictionary for Ananke.
            
            Notes
            -----
            {dummy_dictionary_description}
        """
        p = Galaxia.make_dummy_particles_input(n_parts)
        p[cls._log10NH] = 22 + np.random.randn(n_parts)
        if with_densities:
            p[cls._rho_pos], p[cls._rho_vel] = Galaxia.make_dummy_densities_input(n_parts)
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
        return Galaxia_photo.available_photo_systems

    @classmethod
    def display_density_docs(cls) -> None:
        """
            Print the DensitiesDriver constructor docstring
        """
        print(DensitiesDriver.__init__.__doc__)

    @classmethod
    def display_EnBiD_docs(cls) -> None:
        """
            Print the EnBiD.run_enbid method docstring
        """
        DensitiesDriver.display_EnBiD_docs()

    @classmethod
    def display_extinction_docs(cls) -> None:
        """
            Print the ExtinctionDriver constructor docstring
        """
        print(ExtinctionDriver.__init__.__doc__)

    @classmethod
    def display_errormodel_docs(cls) -> None:
        """
            Print the ErrorModelDriver constructor docstring
        """
        print(ErrorModelDriver.__init__.__doc__)

    @classmethod
    def display_integratedlight_docs(cls) -> None:
        """
            Print the IntegratedLightDriver constructor docstring
        """
        print(IntegratedLightDriver.__init__.__doc__)

    @classmethod
    def display_galaxia_makesurvey_docs(cls) -> None:
        """
            Print the Galaxia.Survey.make_survey method docstring
        """
        print(Galaxia.Survey.make_survey.__doc__)


Ananke.make_dummy_particles_input.__func__.__doc__ = Ananke.make_dummy_particles_input.__doc__.format(
    dummy_dictionary_description=Ananke.make_dummy_dictionary_description())


if __name__ == '__main__':
    raise NotImplementedError()
