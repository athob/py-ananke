#!/usr/bin/env python
"""
Contains the ananke module building utility tools. Credit to
https://github.com/GalacticDynamics-Oxford/Agama/blob/master/setup.py.
"""
import os
import importlib.util
import sys
import pathlib
import subprocess
# from packaging import version

from ._constants import *
from .__metadata__ import *
from . import versioneer

__all__ = ['make_package_data', 'check_submodules', 'append_install_requires_with_submodules', 'make_cmdclass']

ROOT_DIR = pathlib.Path(__file__).parent.parent


# force printing to the terminal even if stdout was redirected
def say(text):
    text += ' '
    sys.stdout.write(text)
    sys.stdout.flush()
    if not sys.stdout.isatty():
        # output was redirected, but we still try to send the message to the terminal
        try:
            if pathlib.Path('/dev/tty').exists():
                with open('/dev/tty', 'w') as out:
                    out.write(text)
                    out.flush()
        except (OSError, PermissionError):
            # /dev/tty may not exist or may not be writable!
            pass


# get the list of all files in the given directories (including those in nested directories)
def all_files(*paths, basedir='.'):
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in os.walk(basedir / path)
            for f in files]


def make_package_data():
    for_all_files = ('__license__', )
    return {NAME: all_files(*for_all_files,
                            basedir=pathlib.Path(SRC_DIR, NAME))}


def import_source_file(module_name, file_path):
    # based on https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def check_submodules(root_dir):
    # if not pathlib.os.listdir(PYENBID) or not pathlib.os.listdir(PYGALAXIA):
    say("\nChecking submodules, running git...")
    try:
        _temp = subprocess.call(['git', 'submodule', 'update', '--init', '--recursive'], cwd=root_dir)
    except FileNotFoundError:
        raise OSError("Your system does not have git installed. Please install git before proceeding")
    if _temp == 128:
        raise OSError(f"The repository from which you are attempting to install this package is not a git repository.\nPlease follow the online instructions for proper installation ({__url__}/#installation).")
    #
    EnBiD_src_root = root_dir / PYENBID / SRC_DIR
    EnBiD_src = import_source_file("EnBiD_src", EnBiD_src_root / '__init__.py')
    EnBiD_meta = import_source_file("EnBiD_src.__metadata__", EnBiD_src_root / '__metadata__.py')
    #
    Galaxia_src_root = root_dir / PYGALAXIA / SRC_DIR
    Galaxia_src = import_source_file("Galaxia_src", Galaxia_src_root / '__init__.py')
    Galaxia_meta = import_source_file("Galaxia_src.__metadata__", Galaxia_src_root / '__metadata__.py')
    #### TODO: below's fix is ugly, there must be something better to do!
    if pathlib.Path(sys.argv[0]).name == 'setup.py' and (sys.argv[1] == 'egg_info' if len(sys.argv)>1 else False) and 'pip' in sys.argv[-1]:
        subprocess.call(['pip', 'cache', 'remove', '*_ananke'])
    ####
    return EnBiD_meta, Galaxia_meta


def append_install_requires_with_submodules(install_requires):
    EnBiD_meta, Galaxia_meta = check_submodules(ROOT_DIR)
    return install_requires + [
        f"EnBiD_ananke @ file://{pathlib.Path(EnBiD_meta.__file__).parent.parent}",
        f"Galaxia_ananke @ file://{pathlib.Path(Galaxia_meta.__file__).parent.parent}"
        ]


make_cmdclass = versioneer.get_cmdclass
