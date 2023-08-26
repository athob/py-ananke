#!/usr/bin/env python
"""
Contains the ErrorModelDriver class definition

Please note that this module is private. The ErrorModelDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from warnings import warn
from collections.abc import Iterable
import numpy as np
import pandas as pd

from Galaxia_ananke import utils as Gutils

from .constants import *

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

    def __init__(self, ananke, **kwargs) -> None:
        """
            Parameters
            ----------
            ananke : Ananke object
                The Ananke object that utilizes this ErrorModel object
                
            error_model : function [df --> dict(band: coefficient)]  # TODO rewrite this
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
        dummy_df = pd.DataFrame([], columns = self.ananke.galaxia_export_keys + self._extra_output_keys)  # TODO create a DataFrame subclass that intercepts __getitem__ and record every 'key' being used
        dummy_df.loc[0] = np.nan
        try:
            dummy_err = self._expand_and_apply_error_model(dummy_df)
        except KeyError as KE:
            raise KE  # TODO make it more informative
        Gutils.compare_given_and_required(dummy_err.keys(), self.ananke.galaxia_export_mag_names, set(self.ananke.galaxia_export_keys)-set(self.ananke.galaxia_export_mag_names), error_message="Given error model function returns wrong set of keys")
    
    @property
    def _sigma_keys(self):
        return set(map(self._sigma_template, self.ananke.galaxia_export_mag_names))

    @property
    def _error_keys(self):
        return set(map(self._error_template, self.ananke.galaxia_export_mag_names))

    @property
    def errors(self):
        if self._error_keys.difference(self.galaxia_output.columns):
            with_columns = []
            for prop_name, error in self._expand_and_apply_error_model(self.galaxia_output).items():
                self.galaxia_output[self._sigma_template(prop_name)] = error
                self.galaxia_output[self._error_template(prop_name)] = error*np.random.randn(self.galaxia_output.shape[0])
                self.galaxia_output[prop_name] += self.galaxia_output[self._error_template(prop_name)]
                with_columns.append(prop_name)
        self._write_extra_columns_to_hdf5(with_columns=with_columns)
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

    def _write_extra_columns_to_hdf5(self, with_columns=[]):  # temporary until vaex supports it
        import h5py as h5
        import vaex
        hdf5_file = self.galaxia_output._hdf5
        old_column_names = set(vaex.open(hdf5_file).column_names)
        with h5.File(hdf5_file, 'r+') as f5:
            extra_columns = [k for k in set(self.galaxia_output.column_names)-old_column_names if not k.startswith('__')]
            for k in extra_columns:
                f5.create_dataset(name=k, data=self.galaxia_output[k].to_numpy())
            if extra_columns:
                print(f"Exported the following quantities to {hdf5_file}")
                print(extra_columns)
            for k in with_columns:
                f5[k][...] = self.galaxia_output[k].to_numpy()
            if with_columns:
                print(f"Overwritten the following quantities to {hdf5_file}")
                print(with_columns)
        self.galaxia_output.__vaex = vaex.open(hdf5_file)
