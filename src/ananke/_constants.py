#!/usr/bin/env python
"""
Contains the ananke module constants.
"""
from ._name import *

__all__ = ['NAME', 'LOG_DIR', 'SRC_DIR', 'PYENBID', 'PYGALAXIA', 'POS_TAG', 'VEL_TAG', 'Q_DUST', 'TOTAL_TO_SELECTIVE']

LOG_DIR = 'log'
SRC_DIR = 'src'
PYENBID = 'py-EnBiD-ananke'
PYGALAXIA = 'py-Galaxia-ananke'

POS_TAG = 'pos'
VEL_TAG = 'vel'

#conversion factor for dust efficiency
# Rachford et al 2009 (FUSE) measure N_H/E(B-V) (N_H=N_HI+2N_H2) = 5.8e21 H/cm^2/mag
# many thanks to Julianne Dalcanton for pointing me to this paper!!
Q_DUST = 2.5e22  #N_H/E(B-V) (N_H=N_HI+2N_H2) ratio of total neutral hydrogen to color excess/reddening
TOTAL_TO_SELECTIVE = 3.1  #R_V total-to-selective extinction ratio value


if __name__ == '__main__':
    raise NotImplementedError()
