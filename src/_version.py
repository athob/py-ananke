#!/usr/bin/env python
"""
"""
import pathlib

from ._name import *
from ._builtin_utils import import_source_file

__all__ = ['get_versions']


get_versions = import_source_file("_version", pathlib.Path(__file__).parent / NAME / '_version.py').get_versions


if __name__ == '__main__':
    raise NotImplementedError()
