#!/usr/bin/env python
"""
Contains the Extinction class definition

Please note that this module is private. The Extinction class is
available in the main ``ananke`` namespace - use that instead.
"""
from collections.abc import Iterable
import numpy as np
import scipy as sp
import pandas as pd

from Galaxia_ananke import utils as Gutils

from ._default_extinction_coeff import *
from .constants import *

__all__ = ['Extinction']


class Extinction:
    """
        Proxy to the utilities for given extinction parameters.

        Parameters
        ----------
        ananke : Ananke object
            The Ananke object that utilizes this Extinction object
        **kwargs
            Additional parameters
    """
    _col_density = "log10_NH_dustweighted"
    _part_id = 'partid'  # TODO consolidate with export_keys in Output of Galaxia_ananke
    _galaxia_pos = ['px', 'py', 'pz']
    _reddening = 'E(B-V)'
    _extinction_template = staticmethod(lambda mag_name: f'A_{mag_name}')
    _extinction_0 = _extinction_template(0)
    _extra_output_keys = [_reddening, _extinction_0]

    def __init__(self, ananke, **kwargs) -> None:
        self.__ananke = ananke
        self.__interpolator = None
        self.__extinctions = None
        self.__parameters = kwargs
        self._text_extinction_coeff()
    
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
        self.__interpolator = sp.interpolate.LinearNDInterpolator(xhel_p[sel_interp],lognh[sel_interp],rescale=False)
        return self.__interpolator

    @property
    def ananke(self):
        return self.__ananke

    @property
    def particles(self):
        return self.ananke.particles
    
    @property
    def column_densities(self):
        return self.particles[self._col_density]
    
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
        # TODO split between partid 0 and !=0, needed ?
        return self.column_density_interpolator(self.galaxia_pos)
    
    @property
    def reddening(self):
        if self._reddening not in self.galaxia_output.column_names:
            self.galaxia_output[self._reddening] = self.qdust * 10**self.interpolated_column_densities
        return self.galaxia_output[self._reddening]

    @property
    def extinction_0(self):
        if self._extinction_0 not in self.galaxia_output.column_names:
            self.galaxia_output[self._extinction_0] = self.three_p_one * self.reddening
        return self.galaxia_output[self._extinction_0]

    def _expand_and_apply_extinction_coeff(self, df, A0):
        extinction_coeff = self.extinction_coeff
        if not isinstance(extinction_coeff, Iterable):
            extinction_coeff = [extinction_coeff]
        return {key: A0 * coeff for coeff_dict in [(ext_coeff(df) if callable(ext_coeff) else ext_coeff) for ext_coeff in extinction_coeff] for key,coeff in coeff_dict.items()}  # TODO adapt to dataframe type of output?

    def _text_extinction_coeff(self):
        dummy_df = pd.DataFrame([], columns = self.ananke.galaxia_export_keys + self._extra_output_keys)  # TODO create a DataFrame subclass that intercepts __getitem__ and record every 'key' being used
        dummy_df.loc[0] = np.nan
        try:
            dummy_ext = self._expand_and_apply_extinction_coeff(dummy_df, dummy_df[self._extinction_0])
        except KeyError as KE:
            raise KE  # TODO make it more informative
        Gutils.compare_given_and_required(dummy_ext.keys(), self.ananke.galaxia_export_mag_names, error_message="Given extinction coeff function returns wrong set of keys")
    
    @property
    def _extinction_keys(self):
        return set(map(self._extinction_template, self.ananke.galaxia_export_mag_names))

    @property
    def extinctions(self):
        if self._extinction_keys.difference(self.galaxia_output.columns):
            for mag_name, extinction in self._expand_and_apply_extinction_coeff(self.galaxia_output, self.extinction_0).items():
                self.galaxia_output[self._extinction_template(mag_name)] = extinction
        return self.__extinctions

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def qdust(self):
        return self.parameters.get('q_dust', Q_DUST)
        
    @property
    def three_p_one(self):
        return self.parameters.get('total_to_selective', TOTAL_TO_SELECTIVE)
    
    @property
    def extinction_coeff(self):  # TODO have method that test prior to running ananke if function is well defined using a dummy vaex, capture error and adapt it with instructions
        return self.parameters.get('extinction_coeff', [getattr(iso, 'default_extinction_coeff', self.__missing_default_extinction_coeff_for_isochrone(iso)) for iso in self.ananke.galaxia_isochrones])
    
    @staticmethod
    def __missing_default_extinction_coeff_for_isochrone(isochrone):
        def __raise_error_if_called(df):
            raise Exception(f"Method default_extinction_coeff isn't defined for isochrone {isochrone.key}")
        return __raise_error_if_called
