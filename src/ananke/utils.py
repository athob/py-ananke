#!/usr/bin/env python
"""
Module miscellaneous utilities
"""
from typing import Optional, List
import re
import docstring_parser as DS_parser
import pandas as pd

from Galaxia_ananke import utils as Gutils

__all__ = ['compare_given_and_required', 'confirm_equal_length_arrays_in_dict', 'RecordingDataFrame', 'extract_parameters_from_docstring', 'extract_notes_from_docstring']


compare_given_and_required = Gutils.compare_given_and_required

confirm_equal_length_arrays_in_dict = Gutils.confirm_equal_length_arrays_in_dict


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
