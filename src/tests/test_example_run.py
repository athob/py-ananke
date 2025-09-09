#!/usr/bin/env python
#
# Author: Adrien CR Thob
# Copyright (C) 2022  Adrien CR Thob
#
# This file is part of py-ananke:
# <https://github.com/athob/py-ananke>.
# 
# The full copyright notice, including terms governing use, modification,
# and redistribution, is contained in the files LICENSE and COPYRIGHT,
# which can be found at the root of the source code distribution tree:
# - LICENSE <https://github.com/athob/py-ananke/blob/main/LICENSE>
# - COPYRIGHT <https://github.com/athob/py-ananke/blob/main/COPYRIGHT>
#
import numpy as np

from .utils import in_tmp_wd

D = 200 # *units.kpc
observer = np.nan*np.ones(3)
while not np.linalg.norm(observer)<1:
    observer = 2*np.random.rand(3)-1

observer *= D/np.linalg.norm(observer)
rshell = [0, 2*D]
fsample = 0.01
photo_sys = 'padova/GAIA__DR2'
cmd_magnames = {'magnitude': 'G',
                'color_minuend': 'Gbp',
                'color_subtrahend': 'Grp'}
cmd_box = {
           'abs_mag_lim_lo': -1000,
           'abs_mag_lim_hi': 1000,
        #    'app_mag_lim_lo' : -1000,
           'app_mag_lim_hi': 30,
        #    'color_lim_lo' : -1000,
        #    'color_lim_hi' : 1000
           }
name = 'sim'


@in_tmp_wd
def test_example_run():
    from .. import ananke as an
    p = an.Ananke.make_dummy_particles_input()
    ananke = an.Ananke(p, name, fsample=fsample,
                       observer=observer, rshell=rshell,
                       photo_sys=photo_sys, cmd_magnames=cmd_magnames,
                       **cmd_box)
    survey = ananke.run()
    print(survey)


if __name__ == '__main__':
    pass
