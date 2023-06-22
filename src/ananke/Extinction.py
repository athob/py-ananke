#!/usr/bin/env python
"""
Contains the Extinction class definition

Please note that this module is private. The Extinction class is
available in the main ``ananke`` namespace - use that instead.
"""
import numpy as np
import scipy as sp

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

    def __init__(self, ananke, **kwargs) -> None:
        self.__ananke = ananke
        self.__interpolator = None
        self.__reddening = None
        self.__extinction = None
        self.__parameters = kwargs
    
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
        if self.__reddening is None:
            self.__reddening = self.qdust * 10**self.interpolated_column_densities
        return self.__reddening

    @property
    def extinction(self):
        if self.__extinction is None:
            self.__extinction = self.three_p_one * self.reddening
        return self.__extinction


        # #calculate intrinsic colors
        # data['bp_rp_int'] = data['gaia_g_bpmag'] - data['gaia_g_rpmag']
        # data['bp_g_int'] = data['gaia_g_bpmag'] - data['gaia_gmag']
        # data['g_rp_int'] = data['gaia_gmag'] - data['gaia_g_rpmag']


        # #calculate extinction in Gaia bands
        # return [data['A0'] * kX(data['bp_rp_int'], data['A0'], b) for b in ['gaia_gmag', 'gaia_g_bpmag', 'gaia_g_rpmag']]

    @property
    def extinctions(self):
        return self.extinction

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def qdust(self):
        return self.parameters.get('qdust', QDUST)
        
    @property
    def three_p_one(self):
        return self.parameters.get('three_p_one', THREE_P_ONE)
    