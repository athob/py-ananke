#!/usr/bin/env python
"""
Contains the definition of default extinction coefficient estimators for
existing photometric systems of Galaxia.

Please note that this module is private.
"""
from Galaxia_ananke import photometry as ph

def _temp(df):
    """
    Default extinction coefficient function for the Gaia DR2 photometric
    system.

    Notes
    -----
    Constants for the empirical extinction model are taken from Table 1 of
    Babusiaux et al. 2018 (ui.adsabs.harvard.edu/abs/2018A%26A...616A..10G)
    with the coefficients determined their Equation 1
    """
    # Constants for the empirical extinction model from Table of Babusiaux et al. 2018
    consts = {
        'gaiadr2_gmag': [0.0, 0.9761,-0.1704,0.0086,0.0011,-0.0438,0.0013,0.0099],
        'gaiadr2_g_bpmag':[0.0, 1.1517,-0.0871,-0.0333,0.0173,-0.0230,0.0006,0.0043],
        'gaiadr2_g_rpmag':[0.0, 0.6104,-0.0170,-0.0026,-0.0017,-0.0078,0.00005,0.0006]
    }
    bp_rp_int = df['gaiadr2_g_bpmag'] - df['gaiadr2_g_rpmag']
    A_0 = df['A_0']
    # Coeffients from Equation 1 of Babusiaux et al. 2018
    return {b: c[1] + c[2]*bp_rp_int + c[3]*bp_rp_int**2 + c[4]*bp_rp_int**3 +c[5]*A_0 +c[6]*A_0**2 +c[7]*bp_rp_int*A_0 for b,c in consts.items()}

ph.available_photo_systems['padova/GAIADR2'].default_extinction_coeff = _temp
