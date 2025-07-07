#!/usr/bin/env python
"""
Module utilities using built-in implementation
"""
import sys
from types import ModuleType
import importlib.util

__all__ = ['import_source_file']


def import_source_file(module_name, file_path) -> ModuleType:
    # based on https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    raise NotImplementedError()
