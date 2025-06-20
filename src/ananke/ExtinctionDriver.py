#!/usr/bin/env python
"""
Contains the ExtinctionDriver class definition

Please note that this module is private. The ExtinctionDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union, Set, List, Dict, Callable
from numpy.typing import ArrayLike, NDArray
from warnings import warn
from functools import cached_property
from collections.abc import Iterable
import numpy as np
import pandas as pd

from . import utils
from ._default_extinction_coeff import *
from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke
    import galaxia_ananke as Galaxia

__all__ = ['ExtinctionDriver']


class ExtinctionDriver:
    """
        Proxy to the utilities for given extinction parameters.
    """
    _col_density = "log10_NH"  # log10 NH column densities between Observer position and particle
    _galaxia_pos = ['px', 'py', 'pz']
    _interp_col_dens = _col_density
    _reddening = 'E(B-V)'
    _extinction_formatter = 'A_{}'
    _extinction_template = _extinction_formatter.format
    _extinction_0 = _extinction_template(0)
    _extra_output_keys = (_reddening, _extinction_0)

    def __init__(self, ananke: Ananke, **kwargs: Dict[str, Any]) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this ExtinctionDriver object
                
            q_dust : float
                Inverted conversion factor for dust efficiency represented by the
                ratio between reddenning and column density E(B-V)/N_H. Default to
                {Q_DUST}

            total_to_selective : float
                Optical total-to-selective extinction ratio between extinction and
                reddenning A(V)/E(B-V). Default to {TOTAL_TO_SELECTIVE}

            mw_model : str
                Optional, can be used to request a specific MW extinction model.
                The only available model is "Marshall2006", future updates may
                expand model availability.

            extinction_coeff : function [df --> dict(band: coefficient)]
                Use to specify a function that returns extinction coefficients per
                band from characterisitics of the extinguished star given in a
                dataframe format. The function must return the coefficients per
                band in a dictionary format with keys corresponding to the band
                names returned by Galaxia (use property galaxia_catalogue_mag_names
                of the Ananke object). By default, the class will query the chosen
                photometric system to check if it has a default function to use.
                If it doesn't find one it will simply fill extinction with nan
                values.
        """
        self.__ananke: Ananke = ananke
        self.__parameters: Dict[str, Any] = kwargs
        self._test_extinction_coeff()
    
    __init__.__doc__ = __init__.__doc__.format(Q_DUST=Q_DUST, TOTAL_TO_SELECTIVE=TOTAL_TO_SELECTIVE)

    def __getattr__(self, item):
        if (item in self.ananke.__dir__() and item.startswith('particle')):
            return getattr(self.ananke, item)
        else:
            return self.__getattribute__(item)

    @property
    def ananke(self) -> Ananke:
        return self.__ananke

    @property
    def particle_column_densities(self) -> NDArray:
        return self.particles[self._col_density] if self._col_density in self.particles else np.nan*self.particle_masses
    
    @property
    def galaxia_output(self) -> Galaxia.Output:
        return self.ananke._galaxia_output

    @classmethod
    def _make_column_density_interpolator(cls, xhel_p, lognh, rshell = (0,np.inf)) -> utils.LinearNDInterpolatorExtrapolator:
        # TODO coordinates.SkyCoord(**dict(zip([*'uvw'], xhel_p.T)), unit='kpc', representation_type='cartesian', frame='galactic') ?
        # return distances from observer to particles
        dhel_p = np.linalg.norm(xhel_p, axis=1)
        # return the min,max extent of the shell of particles used by Galaxia (with a +-0.1 margin factor)
        rmin, rmax = np.array(rshell) * [0.9, 1.1]
        # create a mask for the particles that are within the shell
        sel_interp = (rmin<dhel_p) & (dhel_p<rmax)
        # generate the interpolator to use to get the column densities at positions in and around the particles
        interpolator = utils.LinearNDInterpolatorExtrapolator(np.vstack([3*[0],xhel_p[sel_interp]]),
                                                              np.hstack([0,10**lognh[sel_interp]]),
                                                              rescale=False)  # TODO investigate NaN outputs from interpolator
        calibrating_center = np.mean(xhel_p[sel_interp],axis=0)
        interpolator(calibrating_center)
        return interpolator

    @cached_property
    def column_density_interpolator(self) -> utils.LinearNDInterpolatorExtrapolator:
        if self.mw_model is None:
            xhel_p = self.ananke.particle_positions - self.ananke.observer_position[:3]
            lognh = self.particle_column_densities
            rshell = self.ananke.universe_rshell
        elif self.mw_model == 'Marshall2006':
            xhel_p = np.array(marshall2006['x','y','z'].as_array().tolist())
            lognh = np.log10(marshall2006['ext'].value.unmasked/(self.q_dust*self.total_to_selective))
            rshell = (0, np.inf)
        return self._make_column_density_interpolator(xhel_p, lognh, rshell=rshell)

    @staticmethod
    def _expand_and_apply_extinction_coeff(df, A0, extinction_coeff) -> Dict[str, ArrayLike]:
        if not isinstance(extinction_coeff, Iterable):
            extinction_coeff = [extinction_coeff]
        return {
            key: ((coeff if isinstance(coeff, np.ndarray) else coeff.to_numpy())*
                  (A0 if isinstance(A0, np.ndarray) else A0.to_numpy()))  # TODO temporary fix while waiting issue https://github.com/vaexio/vaex/issues/2405 to be fixed
            for coeff_dict in [
                (ext_coeff(df) if callable(ext_coeff) else ext_coeff)
                for ext_coeff in extinction_coeff
                ]
            for key,coeff in coeff_dict.items()
            }  # TODO adapt to dataframe type of output?

    def _test_extinction_coeff(self) -> None:
        dummy_df = utils.RecordingDataFrame([], columns = self.ananke.galaxia_catalogue_keys + self._extra_output_keys)  # TODO make use of dummy_df.record_of_all_used_keys
        dummy_df.loc[0] = np.nan
        try:
            dummy_ext = self._expand_and_apply_extinction_coeff(dummy_df, dummy_df[self._extinction_0], self.extinction_coeff)
        except KeyError as KE:
            raise KE  # TODO make it more informative
        utils.compare_given_and_required(dummy_ext.keys(), self.ananke.galaxia_catalogue_mag_names, error_message="Given extinction coeff function returns wrong set of keys")
    
    @property
    def _extinction_keys(self) -> Set[str]:
        return set(map(self._extinction_template, self.ananke.galaxia_catalogue_mag_names))

    @classmethod
    def __pp_pipeline(cls, df: utils.PDOrVaexDF, column_density_interpolator: utils.LinearNDInterpolatorExtrapolator,
                           q_dust: float, total_to_selective: float, extinction_keys: Set[str],
                           extinction_coeff: List[Union[Callable[[utils.PDOrVaexDF],
                                                                 Dict[str, NDArray]],
                                                        Dict[str, float]]], _dmod: str,
                           _intrinsic_mag_template: Callable[[str],str]) -> None:
        if cls._interp_col_dens not in df.columns:
            column_densities = df[cls._interp_col_dens] = column_density_interpolator(np.array(df[cls._galaxia_pos]))
        if cls._reddening not in df.columns:
            reddening        = df[cls._reddening]       = q_dust * column_densities
        if cls._extinction_0 not in df.columns:
            extinction_0     = df[cls._extinction_0]    = total_to_selective * reddening
        if extinction_keys.difference(df.columns):
            for mag_name, extinction in cls._expand_and_apply_extinction_coeff(df, extinction_0, extinction_coeff).items():
                extinction_mag_name = cls._extinction_template(mag_name)
                if extinction_mag_name not in df.columns:
                    # assign the column of the extinction values for filter mag_name in the final catalogue output 
                    df[extinction_mag_name] = extinction
                # determine if extinction value has already been added to photometric magnitude
                i_max_ext = np.abs(df[extinction_mag_name] if isinstance(df, pd.DataFrame) else df[extinction_mag_name].to_pandas_series()).argmax()
                max_ext = df[extinction_mag_name][i_max_ext:i_max_ext+1].to_numpy()[0]
                mag_at_max_ext = df[mag_name][i_max_ext:i_max_ext+1].to_numpy()[0]
                unext_mag_at_max_ext = (
                    df[_intrinsic_mag_template(mag_name)][i_max_ext:i_max_ext+1].to_numpy()
                    + df[_dmod][i_max_ext:i_max_ext+1].to_numpy()
                    )[0]
                if np.abs(unext_mag_at_max_ext + max_ext - mag_at_max_ext) > 2*np.abs(np.nextafter(unext_mag_at_max_ext, mag_at_max_ext)-unext_mag_at_max_ext):
                    # add the extinction value to the existing photometric magnitude for filter mag_name
                    df[mag_name] += df[extinction_mag_name]

    @property
    def extinctions(self):  # TODO figure out output typing
        galaxia_output = self.galaxia_output
        print(f"Preparing interpolator")
        coldens_interpolator = self.column_density_interpolator
        extinction_keys = self._extinction_keys
        print(f"Now parallelizing extinctions pipeline")
        galaxia_output.apply_post_process_pipeline_and_flush(self.__pp_pipeline, coldens_interpolator,
                                                             self.q_dust, self.total_to_selective,
                                                             extinction_keys, self.extinction_coeff,
                                                             self.galaxia_output._dmod, self.ananke._intrinsic_mag_template,
                                                             flush_with_columns=self.ananke.galaxia_catalogue_mag_names,
                                                             consolidate_partitions_per_process=True)
        return galaxia_output[list(extinction_keys)]

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters
    
    @property
    def q_dust(self) -> float:
        return self.parameters.get('q_dust', Q_DUST)
        
    @property
    def total_to_selective(self) -> float:
        return self.parameters.get('total_to_selective', TOTAL_TO_SELECTIVE)

    @property
    def mw_model(self) -> float:
        return self.parameters.get('mw_model', None)
    
    @property
    def extinction_coeff(self) -> List[Union[Callable[[utils.PDOrVaexDF], Dict[str, NDArray]], Dict[str, float]]]:
        return self.parameters.get('extinction_coeff', [getattr(psys, 'default_extinction_coeff', self.__missing_default_extinction_coeff_for_photosystem(psys)) for psys in self.ananke.galaxia_photosystems])
    
    @staticmethod
    def __missing_default_extinction_coeff_for_photosystem(photosystem) -> Callable[[utils.PDOrVaexDF], Dict[str, NDArray]]:
        def __return_nan_coeff_and_warn(df):
            warn(f"Method default_extinction_coeff isn't defined for photometric system {photosystem.key}", UserWarning, stacklevel=2)
            return {mag: np.zeros(df.shape[0])*0. + coeff for mag, coeff in zip(photosystem.to_export_keys, universal_extinction_law(photosystem.effective_wavelengths))}
        return __return_nan_coeff_and_warn

    @staticmethod
    def __missing_default_extinction_coeff_for_isochrone(photosystem):
        warn('This static method will be deprecated, please use instead static method __missing_default_extinction_coeff_for_photosystem', DeprecationWarning, stacklevel=2)
        return ExtinctionDriver.__missing_default_extinction_coeff_for_photosystem(photosystem)


if __name__ == '__main__':
    raise NotImplementedError()
