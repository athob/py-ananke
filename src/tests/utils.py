#!/usr/bin/env python
import os
import sys
import io
import tempfile
import random
import string
import pathlib
import contextlib
import functools

import numpy as np


FOURTHIRDPI = 4*np.pi/3

def make_random_string(length=10):
    return "".join([
        random.choice(string.ascii_letters+string.digits)
        for i in range(length)
        ])

@contextlib.contextmanager
def tmp_wd():
    """
    Changes working directory to a temporary one
    and returns to previous on exit.
    Credit to https://stackoverflow.com/a/42441759
    """
    prev_cwd = pathlib.Path.cwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

def in_tmp_wd(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        with tmp_wd():
            func(*args, **kwargs)
    return wrapped_func

class list_stdout(list):
    """
    Credit to https://stackoverflow.com/a/16571630
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


if __name__ == '__main__':
    pass
