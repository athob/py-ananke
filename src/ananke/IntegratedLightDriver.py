#!/usr/bin/env python
"""
Contains the IntegratedLightDriver class definition

Please note that this module is private. The IntegratedLightDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Tuple, List, Dict, Callable
from numpy.typing import ArrayLike, NDArray
from functools import cached_property
import numpy as np
import pandas as pd
from scipy import integrate, interpolate
from astropy import constants, units, table

import galaxia_ananke as Galaxia
from galaxia_ananke.Output import vaex
from galaxia_ananke.photometry.Formatting import Formatting as Galaxia_photo_Formatting
from galaxia_ananke._templates import FTTAGS

from ._constants import *
from .utils import classproperty


if TYPE_CHECKING:
    from .Ananke import Ananke
    from galaxia_ananke.photometry.PhotoSystem import PhotoSystem

__all__ = ['IntegratedLightDriver']


def make_truncated_kroupa_imf(m_min: float = 0.01, m_max: float = 120) -> Tuple[Callable[[ArrayLike], NDArray], float]:
    # Check given mass range
    if m_min >= 0.08 or m_max <= 0.5:
        raise ValueError("Mass range should have a lower bound below 0.08, and a upper bound above 0.5")
    # Compute normalization constant
    normalization_constant = (
          10/7*(0.08**0.7-m_min**0.7)
        + 8/30*(0.08**-0.3-0.5**-0.3)
        + 4/130*(0.5**-1.3-m_max**-1.3)
        )
    # Compute average mass over mass range
    average_mass = (
          10/17*(0.08**1.7-m_min**1.7)
        + 8/70*(0.5**0.7-0.08**0.7)
        + 4/30*(0.5**-0.3-m_max**-0.3)
    ) / normalization_constant
    # Vectorized Kroupa IMF
    def __kroupa_piecewise_imf(m):
        m = np.atleast_1d(m)  # Ensure input is an array (even if single value)
        result = np.zeros_like(m)  # Create an array to store the results
        # Define piecewise conditions
        lower_mask = (m >= m_min) & (m < 0.08)
        result[lower_mask] = m[lower_mask] ** -0.3
        middle_mask = (m >= 0.08) & (m < 0.5)
        result[middle_mask] = 0.08*m[middle_mask] ** -1.3
        upper_mask = (m >= 0.5) & (m <= m_max)
        result[upper_mask] = 0.04*m[upper_mask] ** -2.3
        # Truncate upper/lower bounds
        truncation_mask = (m < m_min) | (m > m_max)
        result[truncation_mask] = 0*m[truncation_mask]
        return result if result.size > 1 else result[0]  # Return scalar if input was scalar
    # Define normalized IMF
    def imf(m: ArrayLike) -> NDArray:
        return __kroupa_piecewise_imf(m) / normalization_constant
    return imf, average_mass, m_min, m_max


class IntegratedLightDriver:
    """
        TODO
    """
    _mini = Galaxia_photo_Formatting._mini
    _mact = Galaxia_photo_Formatting._mact
    _lum = Galaxia_photo_Formatting._lum
    _teff = Galaxia_photo_Formatting._teff
    _grav = Galaxia_photo_Formatting._grav
    _label = Galaxia_photo_Formatting._label
    _ms_labels = [0,1]
    _default_imf_utils: Tuple[Callable[[ArrayLike], NDArray], float, float, float] = make_truncated_kroupa_imf()
    _zero_imf: Callable[[ArrayLike], NDArray] = lambda m: 0*m
    # _hydrogen_burning_limit = table.QTable({ # https://ui.adsabs.harvard.edu/abs/2023A%26A...671A.119C
    #     Galaxia_photo_Formatting._mini: [(0.075*units.Msun).to(Galaxia_photo_Formatting._unit_mass)],
    #     Galaxia_photo_Formatting._lum: [(-4.19*units.LogUnit(units.Lsun)).to(Galaxia_photo_Formatting._unit_lum)],
    #     Galaxia_photo_Formatting._teff: [(1800*units.Kelvin).to(Galaxia_photo_Formatting._unit_temp)],
    #     Galaxia_photo_Formatting._radi: [(0.083*units.Rsun).to(Galaxia_photo_Formatting._unit_radi)]
    #     })
    def __init__(self, ananke: Ananke, **kwargs: Dict[str, Any]) -> None:
        """
        Parameters
        ----------
        ananke : Ananke object
            The Ananke object that utilizes this IntegratedLightDriver object
        **kwargs
            Additional parameters
        """
        self.__ananke: Ananke = ananke
        self.__parameters: Dict[str, Any] = kwargs

    @classproperty
    def _default_imf(cls):
        return cls._default_imf_utils[0]

    @classproperty
    def _default_imf_average(cls):
        return cls._default_imf_utils[1]

    @classproperty
    def _default_imf_m_min(cls):
        return cls._default_imf_utils[2]

    @classproperty
    def _default_imf_m_max(cls):
        return cls._default_imf_utils[3]

    @property
    def ananke(self) -> Ananke:
        return self.__ananke

    @property
    def galaxia_output(self) -> Galaxia.Output:
        return self.ananke._galaxia_output

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters

    @cached_property
    def particle_mass_factors(self) -> NDArray:
        return self.ananke.particle_masses / self._default_imf_average  # TODO remember to replace with particles initial mass 

    @cached_property
    def particle_total_star_numbers(self) -> NDArray:
        return np.round(self.galaxia_output.survey.fsample*self.particle_mass_factors).astype(int)

    @cached_property
    def particle_nearest_isochrone_tracks(self) -> List[List[table.QTable]]:
        return [
            photo_sys.get_nearest_isochrone_track_for_age_and_metallicity(self.ananke.particle_ages,
                                                                          self.ananke.particle_metallicities)
            for photo_sys in self.ananke.galaxia_photosystems
        ]

    @cached_property
    def particle_nearest_isochrone_mass_ranges(self) -> List[List[Tuple[float,float]]]:
        isochrone_tracks: List[List[table.QTable]] = self.particle_nearest_isochrone_tracks
        return [[tuple(qtable[self._mini][[0,-1]].value) for qtable in qtables ] for qtables in isochrone_tracks]

    @cached_property
    def particle_output_mass_ranges(self) -> List[Tuple[float,float]]:
        magnitude_name = self.galaxia_output.parameter_magnitude_name
        magnitude_highs = 0.6+np.minimum(
            self.galaxia_output.parameter_abs_mag_hi,
            self.galaxia_output.parameter_app_mag_hi-self.ananke.particle_nearest_observed_distmod
            )
        return [
            (interpolate.interp1d(*(lambda qt: (qt[magnitude_name].physical,qt[self._mini]))(track[np.where(track[magnitude_name].value<=mag_hi)[0][0]-1+np.arange(2)]))(units.Magnitude(mag_hi).physical),
             interpolate.interp1d(*(lambda qt: (qt[magnitude_name].physical,qt[self._mini]))(track[np.where(track[magnitude_name].value<=mag_hi)[0][-1]+np.arange(2)]))(units.Magnitude(mag_hi).physical) if track[magnitude_name][-1].value>mag_hi else track[magnitude_name][-1].value)
            for track, mag_hi in zip(self.particle_nearest_isochrone_tracks[0], magnitude_highs)
            ]

    @cached_property
    def particle_dimensionless_flux_interpolators_of_nearest_isochrone_tracks(self) -> pd.DataFrame:  # TODO could typing hint to DataFrame[interpolate.interp1d] ? pandera?
        isochrone_tracks: List[List[table.QTable]] = self.particle_nearest_isochrone_tracks
        unique_tracks_index_and_inverse: List[Tuple[NDArray,NDArray]] = [
            np.unique(list(map(id, qtables)), return_inverse=True, return_index=True)[1:]
            for qtables in isochrone_tracks
        ]
        unique_dimensionless_flux_interpolators: List[pd.DataFrame] = [  # TODO could typing hint to DataFrame[interpolate.interp1d] ? pandera?
            pd.DataFrame([
                self.make_dimensionless_flux_interpolators_from_qtable(qtables[i], photo_sys)
                for i in index
                ])
            for (index,_), qtables, photo_sys
            in zip(unique_tracks_index_and_inverse, isochrone_tracks, self.ananke.galaxia_photosystems)
        ]
        return pd.concat([
            flux_interpolators.loc[inverse].reset_index(drop=True)
            for (_,inverse),flux_interpolators
            in zip(unique_tracks_index_and_inverse, unique_dimensionless_flux_interpolators)
        ], axis=1)

    @cached_property
    def __particle_integrated_photometry(self) -> table.QTable:
        dimensionless_flux_interpolators: pd.DataFrame = self.particle_dimensionless_flux_interpolators_of_nearest_isochrone_tracks
        imf: Callable[[ArrayLike], NDArray] = self._default_imf
        particle_mass_factor: NDArray = self.particle_mass_factors
        dimensionless_integrated_fluxes: pd.DataFrame = dimensionless_flux_interpolators.apply(
            lambda series: particle_mass_factor*series.map(
                lambda interp1d: self.integrate_flux_interpolator(interp1d, imf)
                )
            )
        return table.QTable({key: series.to_numpy()*zeropoint
                             for (key,series),zeropoint
                             in zip(dimensionless_integrated_fluxes.items(),self.ananke.photosystems_zeropoints)})

    @cached_property
    def particle_residual_distribution_functions(self) -> List[Callable[[ArrayLike], NDArray]]:
        actual_magnames: List[str] = list(self.ananke.galaxia_catalogue_mag_names)
        sub_vaex: vaex.DataFrame = self.galaxia_output[~self.galaxia_output['|'.join(map(lambda c: f"({c}!={c})", actual_magnames))]][[self.galaxia_output._parentid, self.galaxia_output._mini]]
        sub_vaex_groupby_parentid: vaex.GroupBy = sub_vaex.groupby(self.galaxia_output._parentid)
        imf: Callable[[ArrayLike], NDArray] = self._default_imf
        sample_number_imfs: List[Callable[[ArrayLike], NDArray]] = [  # TODO this step may be highly inefficient, and vaex may have better tools
            self.estimate_number_distribution_function(
                sub_vaex_groupby_parentid.get_group(i)[self.galaxia_output._mini].to_numpy(),
                mass_range,
                lambda m: total_star_number*imf(m),
                (self._default_imf_m_min, self._default_imf_m_max)
                ) if (i,) in sub_vaex_groupby_parentid.groups else self._zero_imf
            for i, mass_range, total_star_number
            in zip(self.ananke.particle_parentids, self.particle_output_mass_ranges, self.particle_total_star_numbers)
        ]
        return [lambda m: np.clip(imf(m) - sample_number_imf(m)/total_star_number, 0, np.inf)
                for sample_number_imf, total_star_number
                in zip(sample_number_imfs, self.particle_total_star_numbers)]

    @cached_property
    def particle_residual_photometry(self) -> table.QTable:
        dimensionless_flux_interpolators: pd.DataFrame = self.particle_dimensionless_flux_interpolators_of_nearest_isochrone_tracks
        residual_imfs: List[Callable[[ArrayLike], NDArray]] = self.particle_residual_distribution_functions
        particle_mass_factor: NDArray = self.particle_mass_factors
        dimensionless_integrated_fluxes: pd.DataFrame = dimensionless_flux_interpolators.transform(
            lambda series: list(zip(series, residual_imfs))
            ).apply(
            lambda series: particle_mass_factor*series.map(
                lambda interp1d_imf: self.integrate_flux_interpolator(*interp1d_imf)
                )
            )
        return table.QTable({key: series.to_numpy()*zeropoint
                             for (key,series),zeropoint
                             in zip(dimensionless_integrated_fluxes.items(),self.ananke.photosystems_zeropoints)})

    @cached_property
    def particle_integrated_photometry(self) -> table.QTable:
        isochrone_tracks: List[List[table.QTable]] = self.particle_nearest_isochrone_tracks
        unique_tracks_index_and_inverse: List[Tuple[NDArray,NDArray]] = [
            np.unique(list(map(id, qtables)), return_inverse=True, return_index=True)[1:]
            for qtables in isochrone_tracks
        ]
        unique_tracks: List[List[table.QTable]] = [
            [qtables[i] for i in index]
            for (index,_),qtables in zip(unique_tracks_index_and_inverse, isochrone_tracks)
        ]
        imf: Callable[[ArrayLike], NDArray] = self._default_imf
        imf_average: float = self._default_imf_average
        unique_integrated_photometry: List[table.QTable] = [
            table.vstack([self.integrate_qtable(qtable, photo_sys, imf) for qtable in qtables])
            for qtables, photo_sys in zip(unique_tracks, self.ananke.galaxia_photosystems)
        ]
        particle_mass_factor = self.particle_mass_factors
        return table.hstack([
            table.QTable({key: particle_mass_factor * column for key,column in qtable[inverse].items()})
            for (_,inverse),qtable in zip(unique_tracks_index_and_inverse, unique_integrated_photometry)
        ])

    @cached_property
    def __particle_residual_photometry(self) -> table.QTable:
        intrinsic_magnames: List[str] = list(self.ananke.intrinsic_catalogue_mag_names)
        actual_magnames: List[str] = list(self.ananke.galaxia_catalogue_mag_names)
        sub_vaex = self.galaxia_output[~self.galaxia_output['|'.join(map(lambda c: f"({c}!={c})", actual_magnames))]][[self.galaxia_output._parentid]+intrinsic_magnames]
        lambda_function = lambda m: units.Magnitude(m).physical
        for i_mag, a_mag in zip(intrinsic_magnames, actual_magnames):
            sub_vaex[a_mag] = sub_vaex[i_mag].apply(lambda_function, vectorize=True)
        summed_df_per_parentid = sub_vaex.groupby(self.galaxia_output._parentid).agg(
            dict(zip(actual_magnames, len(actual_magnames)*['sum']))
            ).to_pandas_df().set_index(self.galaxia_output._parentid)
        summed_df_per_parentid = pd.concat([
            summed_df_per_parentid,
            pd.DataFrame({},index=list(set(self.ananke.particle_parentids)-set(summed_df_per_parentid.index)))
        ]).fillna(0).loc[self.ananke.particle_parentids]
        particle_catalogue_photometry =  table.QTable({
            magname: summed.to_numpy()*zeropoint for (magname,summed),zeropoint in zip(summed_df_per_parentid.items(), self.ananke.photosystems_zeropoints)
        })
        fsample = self.galaxia_output.survey.fsample
        return table.QTable({
            magname: fsample*integrated-catalogue for (magname,integrated),(_,catalogue) in zip(self.particle_integrated_photometry.items(),particle_catalogue_photometry.items())
        })

    @classmethod
    def integrate_qtable(cls, qtable: table.QTable, photo_sys: PhotoSystem,
                              imf: Callable[[ArrayLike], NDArray]) -> table.QTable:
        flux_interpolators = cls.make_dimensionless_flux_interpolators_from_qtable(qtable, photo_sys)
        return table.QTable({mag_name: zeropoint*[cls.integrate_flux_interpolator(flux_interpolator, imf)]
                             for (mag_name,flux_interpolator),zeropoint in zip(flux_interpolators.items(), photo_sys.zeropoints)})

    @classmethod
    def make_dimensionless_flux_interpolators_from_qtable(
        cls, qtable: table.QTable, photo_sys: PhotoSystem
        ) -> Dict[str,interpolate.interp1d]:
        return {photo_sys.mag_names_to_export_keys_mapping[mag_name]: 
                interpolate.interp1d(qtable[cls._mini].to(units.Msun).value,
                                     magnitude.physical[np.newaxis])
                for mag_name, magnitude in qtable[photo_sys.mag_names].items()}

    @staticmethod
    def integrate_flux_interpolator(flux_interpolator: interpolate.interp1d,
                                    imf: Callable[[ArrayLike], NDArray]) -> float:
        return integrate.quad(lambda m: imf(m)*flux_interpolator(m),
                              flux_interpolator.x[0],
                              flux_interpolator.x[-1])[0]

    @staticmethod
    def estimate_number_distribution_function(masses: NDArray, mass_range: Tuple[float, float],
                                              number_imf: Callable[[ArrayLike], NDArray],
                                              imf_range: Tuple[float, float], n_windows: int = 20) -> interpolate.interp1d:
        # clean up mass range
        mass_range = np.sort(mass_range)
        masses = np.sort(masses)
        mass_range[0] = min(mass_range[0], np.nextafter(masses[0],0))
        mass_range[1] = max(mass_range[1], np.nextafter(masses[-1],np.inf))
        # make initial stepwise distribution function estimate
        window = int(np.ceil(masses.shape[0]/n_windows))
        indices = np.unique(np.clip(masses.shape[0]//2 + window*(np.arange(n_windows+1) - n_windows//2), 0, masses.shape[0]-1))
        distribution_masses = np.hstack([mass_range[0], masses[indices], mass_range[1]])
        mass_diff = np.diff(distribution_masses)
        distribution = np.hstack([0.5,np.diff(indices),0.5])/mass_diff
        # get steps centroids and find number IMF values
        distribution_mass_centroids = (distribution_masses[:-1]+distribution_masses[1:])/2
        number_imf_at_centroids = number_imf(distribution_mass_centroids)
        # from peak to trough, assure estimate at centroids is under number IMF
        peak_to_trough = np.argsort((np.log10(number_imf_at_centroids) - np.log10(distribution))*mass_diff)
        for i in range(peak_to_trough.shape[0]-1):
            current = peak_to_trough[i]
            nextone = peak_to_trough[i+1]
            residual = number_imf_at_centroids[current]-distribution[current]
            if residual < 0:  # TODO redistribution could take into account proximity of remaining mass bins
                distribution[current] -= np.abs(residual)
                distribution[nextone] += np.abs(residual)*mass_diff[current]/mass_diff[nextone]
        # refine estimate by shifting from stepwise to linear, conserving integral
        masses = distribution_masses[1:-1]
        distribution_masses = np.hstack([distribution_masses[[0,-1]], distribution_mass_centroids, masses])
        temp = np.argsort(distribution_masses)
        distribution_masses = np.hstack([mass_range[0],distribution_masses[temp],mass_range[1]])
        distribution = np.hstack([0,np.hstack([distribution[[0,-1]],distribution,((masses-distribution_mass_centroids[:-1])*distribution[:-1] + (distribution_mass_centroids[1:]-masses)*distribution[1:])/np.diff(distribution_mass_centroids)])[temp],0])
        # filling zeros and applying interpolation
        distribution_masses = np.hstack([imf_range[0], distribution_masses, imf_range[1]])
        distribution = np.hstack([0, distribution, 0])
        return interpolate.interp1d(distribution_masses, distribution)


if __name__ == '__main__':
    raise NotImplementedError()
