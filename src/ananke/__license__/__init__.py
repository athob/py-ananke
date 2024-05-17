#!/usr/bin/env python
"""
Reading LICENSE file
"""
import pathlib

__all__ = ["__license_full__"]

__license_full__ = (pathlib.Path(__file__).parent / 'LICENSE').read_text()
