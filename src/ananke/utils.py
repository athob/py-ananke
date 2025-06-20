#!/usr/bin/env python
"""
Module miscellaneous utilities
"""
from typing import Optional, List, Union
import re
import docstring_parser as DS_parser
import numpy as np
from scipy import interpolate
import pandas as pd
import vaex

from galaxia_ananke import utils as Gutils

__all__ = ['classproperty', 'compare_given_and_required', 'confirm_equal_length_arrays_in_dict', 'PDOrVaexDF', 'RecordingDataFrame', 'extract_parameters_from_docstring', 'extract_notes_from_docstring', 'LinearNDInterpolatorExtrapolator']

classproperty = Gutils.classproperty

compare_given_and_required = Gutils.compare_given_and_required

confirm_equal_length_arrays_in_dict = Gutils.confirm_equal_length_arrays_in_dict

PDOrVaexDF = Union[pd.DataFrame, vaex.DataFrame]

class RecordingDataFrame(pd.DataFrame):
    """
    Pandas DataFrame that records all its used keys from getitem
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._record_of_all_used_keys = set()
    def _add_to_record_of_all_used_keys(self, keys):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            self._record_of_all_used_keys.add(key)
    def __getitem__(self, key):
        self._add_to_record_of_all_used_keys(key)
        return super().__getitem__(key)
    # def __setitem__(self, key, value):
    #     self._add_to_record_of_all_used_keys(key)
    #     super().__setitem__(key, value)
    # def __delitem__(self, key):
    #     self._add_to_record_of_all_used_keys(key)
    #     super().__delitem__(key)
    @property
    def record_of_all_used_keys(self):
        return self._record_of_all_used_keys


def extract_parameters_from_docstring(docstring: str, parameters: Optional[List[str]] = None, ignore: Optional[List[str]] = None) -> str:
    input_DS = DS_parser.parse(docstring)
    output_DS = DS_parser.Docstring()
    output_DS.style = input_DS.style
    output_DS.meta = [param
                      for param in input_DS.params
                      if (True if parameters is None else param.arg_name in parameters) and (True if ignore is None else param.arg_name not in ignore)]
    temp_docstring = re.split("\n-*\n",DS_parser.compose(output_DS),maxsplit=1)[1]
    return '\n'.join([line if line[:1] in ['', ' '] else f"\n{line}" for line in temp_docstring.split('\n')])


def extract_notes_from_docstring(docstring: str) -> str:
    input_DS = DS_parser.parse(docstring)
    output_DS = DS_parser.Docstring()
    output_DS.style = input_DS.style
    output_DS.meta = [meta for meta in input_DS.meta if 'notes' in meta.args]
    return re.split("\n-*\n",DS_parser.compose(output_DS),maxsplit=1)[1]


class LinearNDInterpolatorExtrapolator:
    def __init__(self, points: np.ndarray, values: np.ndarray, **kwargs):
        """
        Use ND-linear interpolation over the convex hull of points, and nearest neighbor outside (for
        extrapolation)

        Idea taken from https://stackoverflow.com/questions/20516762/extrapolate-with-linearndinterpolator
        Adapted from https://stackoverflow.com/a/75327466
        """
        self.linear_interpolator = interpolate.LinearNDInterpolator(points, values, **kwargs)
        self.nearest_neighbor_interpolator = interpolate.NearestNDInterpolator(points, values, **kwargs)
        self._calibrating_center = np.mean(points,axis=0)
        self.linear_interpolator(self._calibrating_center)
        from_calibrating_center = points - self._calibrating_center
        self._calibrating_outer = self._calibrating_center + 2*from_calibrating_center[
            np.argmax(np.linalg.norm(from_calibrating_center)
                      if points.ndim == 2
                      else np.abs(from_calibrating_center))
                      ]
        self.nearest_neighbor_interpolator(self._calibrating_outer)

    def __call__(self, *args) -> Union[float, np.ndarray]:
        t = self.linear_interpolator(*args)
        t[np.isnan(t)] = self.nearest_neighbor_interpolator(*args)[np.isnan(t)]  # TODO reduce unnecessary interpolation use?
        if t.size == 1:
            return t.item(0)
        return t


if __name__ == '__main__':
    raise NotImplementedError()
