#!/usr/bin/env python
"""
Contains the ErrorModelDriver class definition

Please note that this module is private. The ErrorModelDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from warnings import warn
from collections.abc import Iterable
import numpy as np
import pandas as pd

from Galaxia_ananke import utils as Gutils

from ._default_error_model import *
from .constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke

__all__ = ['ErrorModelDriver']


class ErrorModelDriver:
    """
        Proxy to the utilities for given error model driver parameters.
    """
    _sigma_formatter = '{}_Sig'
    _sigma_template = _sigma_formatter.format
    _error_formatter = '{}_Err'
    _error_template = _error_formatter.format
    _extra_output_keys = []

    def __init__(self, ananke: Ananke, **kwargs) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this ErrorModel object
                
            error_model : function [df --> dict(prop: coefficient)]
                Use to specify a model that returns error's standard deviations
                per property from characterisitics of the mock star given in a
                dataframe format. The function must return the standard deviations
                per property in a dictionary format with keys corresponding to
                the property names returned by Galaxia (use property
                galaxia_catalogue_mag_and_astrometrics of the Ananke object).
                By default, the class will query the chosen photometric system
                to check if it has a default model to use. If it doesn't find one
                it will simply fill errors with nan values.
        """
        self.__ananke = ananke
        self.__parameters = kwargs
        self._test_error_model()
    
    def __getattr__(self, item):
        if (item in self.ananke.__dir__() and item.startswith('particle')):
            return getattr(self.ananke, item)
        else:
            return self.__getattribute__(item)

    @property
    def ananke(self):
        return self.__ananke

    @property
    def galaxia_output(self):
        return self.ananke._galaxia_output

    def _expand_and_apply_error_model(self, df):
        error_model = self.error_model
        if not isinstance(error_model, Iterable):
            error_model = [error_model]
        return {key: error for error_dict in [(err_model(df) if callable(err_model) else err_model) for err_model in error_model] for key,error in error_dict.items()}  # TODO adapt to dataframe type of output?

    def _test_error_model(self):
        dummy_df = pd.DataFrame([], columns = self.ananke.galaxia_catalogue_keys + self._extra_output_keys)  # TODO create a DataFrame subclass that intercepts __getitem__ and record every 'key' being used
        dummy_df.loc[0] = np.nan
        try:
            dummy_err = self._expand_and_apply_error_model(dummy_df)
        except KeyError as KE:
            raise KE  # TODO make it more informative
        Gutils.compare_given_and_required(dummy_err.keys(), self.ananke.galaxia_catalogue_mag_and_astrometrics, set(self.ananke.galaxia_catalogue_keys)-set(self.ananke.galaxia_catalogue_mag_and_astrometrics), error_message="Given error model function returns wrong set of keys")
    
    @property
    def _sigma_keys(self):
        return set(map(self._sigma_template, self.ananke.galaxia_catalogue_mag_names))

    @property
    def _error_keys(self):
        return set(map(self._error_template, self.ananke.galaxia_catalogue_mag_names))

    @property
    def errors(self):
        if self._error_keys.difference(self.galaxia_output.columns):
            magnitudes = self.ananke.galaxia_catalogue_mag_names
            with_columns = []
            for prop_name, error in self._expand_and_apply_error_model(self.galaxia_output).items():
                prop_sig_name, prop_err_name = self._sigma_template(prop_name), self._error_template(prop_name)
                self.galaxia_output[prop_sig_name] = error
                self.galaxia_output[prop_err_name] = error*np.random.randn(self.galaxia_output.shape[0])
                self.galaxia_output[prop_name] += self.galaxia_output[prop_err_name]
                with_columns.append(prop_name)
        self.galaxia_output.flush_extra_columns_to_hdf5(with_columns=with_columns)
        self.galaxia_output._pp_convert_icrs_to_galactic()
        return self.galaxia_output[list(self._error_keys)]

    @property
    def parameters(self):
        return self.__parameters
    
    @property
    def error_model(self):  # TODO design
        return self.parameters.get('error_model', [getattr(iso, 'default_error_model', self.__missing_default_error_model_for_isochrone(iso)) for iso in self.ananke.galaxia_isochrones])
    
    @staticmethod
    def __missing_default_error_model_for_isochrone(isochrone):
        def __return_zero_error_and_warn(df):
            warn(f"Method default_error_model isn't defined for isochrone {isochrone.key}", UserWarning, stacklevel=2)
            return {mag: np.zeros(df.shape[0]) for mag in isochrone.to_export_keys}
        return __return_zero_error_and_warn
