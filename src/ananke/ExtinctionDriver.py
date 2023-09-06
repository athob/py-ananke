#!/usr/bin/env python
"""
Contains the ExtinctionDriver class definition

Please note that this module is private. The ExtinctionDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from warnings import warn
from collections.abc import Iterable
import numpy as np
import scipy as sp
import scipy.interpolate  # needed for python==3.7
import pandas as pd

from Galaxia_ananke import utils as Gutils

from ._default_extinction_coeff import *
from .constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

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
    _extra_output_keys = [_reddening, _extinction_0]

    def __init__(self, ananke: Ananke, **kwargs) -> None:
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

            extinction_coeff : function [df --> dict(band: coefficient)]
                Use to specify a function that returns extinction coefficients per
                band from characterisitics of the extinguished star given in a
                dataframe format. The function must return the coefficients per
                band in a dictionary format with keys corresponding to the band
                names returned by Galaxia (use property galaxia_export_mag_names
                of the Ananke object). By default, the class will query the chosen
                photometric system to check if it has a default function to use.
                If it doesn't find one it will simply fill extinction with nan
                values.
        """
        self.__ananke = ananke
        self.__interpolator = None
        self.__parameters = kwargs
        self._test_extinction_coeff()
    
    __init__.__doc__ = __init__.__doc__.format(Q_DUST=Q_DUST, TOTAL_TO_SELECTIVE=TOTAL_TO_SELECTIVE)
    
    def _make_interpolator(self):  # TODO to review
        xvsun = self.ananke.observer_position
        pos_pa = self.ananke.particle_positions
        xhel = pos_pa - xvsun[:3]
        # TODO coordinates.SkyCoord(**dict(zip([*'uvw'], xhel.T)), unit='kpc', representation_type='cartesian', frame='galactic') ?
        # phi = np.pi + np.arctan2(xvsun[1], xvsun[0])
        # rot = np.array([
        #     [np.cos(phi), np.sin(phi), 0.0],
        #     [-np.sin(phi), np.cos(phi), 0.0],
        #     [0.0, 0.0, 1.0]
        #     ])
        xhel_p = xhel  # np.dot(xhel,rot.T)
        dhel_p = np.linalg.norm(xhel_p, axis=1)
        rmin, rmax = self.ananke.universe_rshell
        rmin *= 0.9
        rmax *= 1.1
        sel_interp = (rmin<dhel_p) & (dhel_p<rmax)
        lognh = self.column_densities
        self.__interpolator = sp.interpolate.LinearNDInterpolator(xhel_p[sel_interp],lognh[sel_interp],rescale=False)  # TODO investigate NaN outputs from interpolator
        return self.__interpolator

    def __getattr__(self, item):
        if (item in self.ananke.__dir__() and item.startswith('particle')):
            return getattr(self.ananke, item)
        else:
            return self.__getattribute__(item)

    @property
    def ananke(self):
        return self.__ananke

    @property
    def column_densities(self):
        return self.particles[self._col_density] if self._col_density in self.particles else np.nan*self.particle_masses
    
    @property
    def galaxia_output(self):
        return self.ananke._galaxia_output
    
    @property
    def galaxia_pos(self):
        return np.array(self.galaxia_output[self._galaxia_pos])
    
    @property
    def column_density_interpolator(self):
        if self.__interpolator is None:
            return self._make_interpolator()
        else:
            return self.__interpolator

    @property
    def interpolated_column_densities(self):
        if self._interp_col_dens not in self.galaxia_output.column_names:
            self.galaxia_output[self._interp_col_dens] = self.column_density_interpolator(self.galaxia_pos)
        return self.galaxia_output[self._interp_col_dens]
    
    @property
    def reddening(self):
        if self._reddening not in self.galaxia_output.column_names:
            self.galaxia_output[self._reddening] = self.q_dust * 10**self.interpolated_column_densities
        return self.galaxia_output[self._reddening]

    @property
    def extinction_0(self):
        if self._extinction_0 not in self.galaxia_output.column_names:
            self.galaxia_output[self._extinction_0] = self.total_to_selective * self.reddening
        return self.galaxia_output[self._extinction_0]

    def _expand_and_apply_extinction_coeff(self, df, A0):
        extinction_coeff = self.extinction_coeff
        if not isinstance(extinction_coeff, Iterable):
            extinction_coeff = [extinction_coeff]
        return {key: A0 * coeff for coeff_dict in [(ext_coeff(df) if callable(ext_coeff) else ext_coeff) for ext_coeff in extinction_coeff] for key,coeff in coeff_dict.items()}  # TODO adapt to dataframe type of output?

    def _test_extinction_coeff(self):
        dummy_df = pd.DataFrame([], columns = self.ananke.galaxia_catalogue_keys + self._extra_output_keys)  # TODO create a DataFrame subclass that intercepts __getitem__ and record every 'key' being used
        dummy_df.loc[0] = np.nan
        try:
            dummy_ext = self._expand_and_apply_extinction_coeff(dummy_df, dummy_df[self._extinction_0])
        except KeyError as KE:
            raise KE  # TODO make it more informative
        Gutils.compare_given_and_required(dummy_ext.keys(), self.ananke.galaxia_catalogue_mag_names, error_message="Given extinction coeff function returns wrong set of keys")
    
    @property
    def _extinction_keys(self):
        return set(map(self._extinction_template, self.ananke.galaxia_catalogue_mag_names))

    @property
    def extinctions(self):
        if self._extinction_keys.difference(self.galaxia_output.columns):
            for mag_name, extinction in self._expand_and_apply_extinction_coeff(self.galaxia_output, self.extinction_0).items():
                self.galaxia_output[self._extinction_template(mag_name)] = extinction
                self.galaxia_output[mag_name] += extinction
        self.galaxia_output.flush_extra_columns_to_hdf5(with_columns=self.ananke.galaxia_catalogue_mag_names)
        return self.galaxia_output[list(self._extinction_keys)]

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def q_dust(self):
        return self.parameters.get('q_dust', Q_DUST)
        
    @property
    def total_to_selective(self):
        return self.parameters.get('total_to_selective', TOTAL_TO_SELECTIVE)
    
    @property
    def extinction_coeff(self):
        return self.parameters.get('extinction_coeff', [getattr(iso, 'default_extinction_coeff', self.__missing_default_extinction_coeff_for_isochrone(iso)) for iso in self.ananke.galaxia_isochrones])
    
    @staticmethod
    def __missing_default_extinction_coeff_for_isochrone(isochrone):
        def __return_nan_coeff_and_warn(df):
            warn(f"Method default_extinction_coeff isn't defined for isochrone {isochrone.key}", UserWarning, stacklevel=2)
            return {mag: np.zeros(df.shape[0])*0. for mag in isochrone.to_export_keys}
        return __return_nan_coeff_and_warn
