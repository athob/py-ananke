#!/usr/bin/env python
"""
Contains the ananke module building utility tools.
"""
import pathlib
import sys
import subprocess
from packaging import version

from .constants import *

__all__ = ['say', 'all_files', 'check_submodules']

ROOT_DIR = pathlib.Path(__file__).parent.parent


# force printing to the terminal even if stdout was redirected
def say(text):
    text += ' '
    sys.stdout.write(text)
    sys.stdout.flush()
    if not sys.stdout.isatty():
        # output was redirected, but we still try to send the message to the terminal
        try:
            with open('/dev/tty', 'w') as out:
                out.write(text)
                out.flush()
        except PermissionError:
            # /dev/tty may not exist or may not be writable!
            pass


# get the list of all files in the given directories (including those in nested directories)
def all_files(*paths, basedir='.'):
    basedir = pathlib.Path(basedir)
    return [str(pathlib.Path(dirpath, f).relative_to(basedir))
            for path in paths
            for dirpath, dirnames, files in pathlib.os.walk(basedir / path)
            for f in files]


def check_submodules(root_dir):
    # if not pathlib.os.listdir(PYENBID) or not pathlib.os.listdir(PYGALAXIA):
    say("\nChecking submodules, running git...")
    subprocess.call(['git', 'submodule', 'update', '--init', '--recursive'], cwd=root_dir)

