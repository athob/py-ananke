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
Q_DUST = 4.0e-23 #1.0/5.8e21
TOTAL_TO_SELECTIVE = 3.1  #R_V value


if __name__ == '__main__':
    raise NotImplementedError()
