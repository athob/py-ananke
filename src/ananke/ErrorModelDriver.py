#!/usr/bin/env python
"""
Contains the ErrorModelDriver class definition

Please note that this module is private. The ErrorModelDriver class is
available in the main ``ananke`` namespace - use that instead.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union, Set, List, Dict, Callable
from numpy.typing import ArrayLike, NDArray
from warnings import warn
from collections.abc import Iterable
import numpy as np
import pandas as pd

from . import utils
from ._default_error_model import *
from ._constants import *

if TYPE_CHECKING:
    from .Ananke import Ananke
    import Galaxia_ananke as Galaxia

__all__ = ['ErrorModelDriver']


class ErrorModelDriver:
    """
        Proxy to the utilities for given error model driver parameters.
    """
    _sigma_formatter = '{}_Sig'
    _sigma_template = _sigma_formatter.format
    _error_formatter = '{}_Err'
    _error_template = _error_formatter.format
    _extra_output_keys = ()

    def __init__(self, ananke: Ananke, **kwargs: Dict[str, Any]) -> None:
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
        self.__ananke: Ananke = ananke
        self.__parameters: Dict[str, Any] = kwargs
        self._test_error_model()
    
    def __getattr__(self, item):
        if (item in self.ananke.__dir__() and item.startswith('particle')):
            return getattr(self.ananke, item)
        else:
            return self.__getattribute__(item)

    @property
    def ananke(self) -> Ananke:
        return self.__ananke

    @property
    def galaxia_output(self) -> Galaxia.Output:
        return self.ananke._galaxia_output

    @staticmethod
    def _expand_and_apply_error_model(df, error_model) -> Dict[str, ArrayLike]:
        if not isinstance(error_model, Iterable):
            error_model = [error_model]
        return {key: error for error_dict in [(err_model(df) if callable(err_model) else err_model) for err_model in error_model] for key,error in error_dict.items()}  # TODO adapt to dataframe type of output?

    def _test_error_model(self) -> None:
        dummy_df = utils.RecordingDataFrame([], columns = self.ananke.galaxia_catalogue_keys + self._extra_output_keys)  # TODO make use of dummy_df.record_of_all_used_keys
        dummy_df.loc[0] = np.nan
        try:
            dummy_err = self._expand_and_apply_error_model(dummy_df, self.error_model)
        except KeyError as KE:
            raise KE  # TODO make it more informative
        utils.compare_given_and_required(dummy_err.keys(), set(), self.ananke.galaxia_catalogue_mag_and_astrometrics, error_message="Given error model function returns wrong set of keys")
    
    @property
    def _sigma_keys(self) -> Set[str]:
        return set(map(self._sigma_template, self.ananke.galaxia_catalogue_mag_names))

    @property
    def _error_keys(self) -> Set[str]:
        return set(map(self._error_template, self.ananke.galaxia_catalogue_mag_names))

    @classmethod
    def __pp_pipeline(cls, df: pd.DataFrame, error_keys: Set[str],
                           error_model: List[Union[Callable[[pd.DataFrame],
                                                            Dict[str, NDArray]],
                                                   Dict[str, float]]]) -> None:
        if error_keys.difference(df.columns):
            for prop_name, error in cls._expand_and_apply_error_model(df, error_model).items():
                # pre-generate the keys to use for the standard error and its actual gaussian drawn error of property prop_name
                prop_sig_name, prop_err_name = cls._sigma_template(prop_name), cls._error_template(prop_name)
                # assign the column of the standard error values for property prop_name in the final catalogue output 
                df[prop_sig_name] = error
                # assign the column of the actual gaussian drawn error values for property prop_name in the final catalogue output 
                df[prop_err_name] = error*np.random.randn(df.shape[0])
                # add the drawn error value to the existing quantity for property prop_name
                df[prop_name] += df[prop_err_name]
                # with_columns.append(prop_name)

    @property
    def errors(self):  # TODO figure out output typing
        galaxia_output = self.galaxia_output
        error_keys = self._error_keys
        galaxia_output.apply_post_process_pipeline_and_flush(self.__pp_pipeline, error_keys, self.error_model, flush_with_columns=tuple(self._error_prop_names))
        galaxia_output._pp_convert_icrs_to_galactic()
        return galaxia_output[list(error_keys)]

    @property
    def _error_prop_names(self) -> Set[str]:
        dummy_df = utils.RecordingDataFrame([], columns = self.ananke.galaxia_catalogue_keys + self._extra_output_keys)  # TODO make use of dummy_df.record_of_all_used_keys
        dummy_df.loc[0] = np.nan
        return set(self._expand_and_apply_error_model(dummy_df, self.error_model).keys())

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters
    
    @property
    def ignore(self) -> bool:
        return self.parameters.get('ignore', False)
    
    @property
    def error_model(self) -> List[Union[Callable[[pd.DataFrame], Dict[str, NDArray]], Dict[str, float]]]:  # TODO design
        return self.parameters.get('error_model', [getattr(psys, 'default_error_model', self.__missing_default_error_model_for_photosystem(psys)) for psys in self.ananke.galaxia_photosystems])
    
    @staticmethod
    def __missing_default_error_model_for_photosystem(photosystem) -> Callable[[pd.DataFrame], Dict[str, NDArray]]:
        def __return_zero_error_and_warn(df):
            warn(f"Method default_error_model isn't defined for photometric system {photosystem.key}", UserWarning, stacklevel=2)
            return {mag: np.zeros(df.shape[0]) for mag in photosystem.to_export_keys}
        return __return_zero_error_and_warn

    @staticmethod
    def __missing_default_error_model_for_isochrone(photosystem):
        warn('This static method will be deprecated, please use instead static method __missing_default_error_model_for_photosystem', DeprecationWarning, stacklevel=2)
        return ErrorModelDriver.__missing_default_error_model_for_photosystem(photosystem)


if __name__ == '__main__':
    raise NotImplementedError()
