#!/usr/bin/env python
"""
Docstring
"""
import os
import pathlib
import subprocess
import numpy as np
import pandas as pd
import h5py as h5
import ebf
import EnBiD
from string import Template

from .constants import *


TO_GALAXIA = 'to_galaxia'


def enbid(pos, vel, name='.', ngb=64):  # TODO: implement ngb
    path = pathlib.Path(name)
    rho_pos = EnBiD.enbid(pos, name=path / POS_TAG)
    rho_vel = EnBiD.enbid(vel, name=path / VEL_TAG)
    return pd.DataFrame.from_dict({POS_TAG: rho_pos, VEL_TAG: rho_vel})


if __name__ == '__main__':
    pass
