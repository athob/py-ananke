#!/usr/bin/env python
"""
Contains the definition of default error model estimators for
existing isochrones of Galaxia.

Please note that this module is private.
"""
import numpy as np
from astropy import units
from Galaxia_ananke import photometry as ph

def _temp(df):
    """
    Approximate error model for DR2
    based on Table 3 of release paper
    returns uncertainty estimate in magnitudes, mas, mas/yr, km/s
    """
    GMAG  = 'gaia_gmag'
    RPMAG = 'gaia_g_rpmag'
    BPMAG = 'gaia_g_bpmag'
    PI    = 'pi'
    RA    = 'ra'
    DEC   = 'dec'
    PMRA  = 'mura'
    PMDEC = 'mudec'
    VR    = 'vr'
    TEFF  = 'teff'
    MAS_TO_DEG = (units.mas/units.deg).si.scale
    def grvs_from_g_rp(gmag, rpmag):
        #from equations 2 and 3 of DR2 release paper
        ggrp = gmag - rpmag
        grvs = rpmag + 132.32 - 377.28*ggrp + 402.32*ggrp**2 - 190.97*ggrp**3 + 34.026*ggrp**4
        mask = ggrp < 1.4
        grvs[mask] = rpmag[mask] + 0.042319 - 0.65124*ggrp[mask] + 1.0215*ggrp[mask]**2 - 1.3947*ggrp[mask]**3 + 0.53768*ggrp[mask]**4
        return grvs    
    def _model(prop, errtype):
        coeffs = {'gmag'    : [0.000214143, 1.07523e-7, 1.75147],
                  'bprpmag' : [0.00162729, 2.52848e-8, 1.25981],
                  'pospar'  : [0.0426028, 2.583e-10, 0.923162],
                  'pm'      : [0.0861852,6.0771e-9, 1.05067],
                  'rv'      : [0.278939, 0.0000355589, 1.10179]
        }
        c=coeffs[errtype]
        return c[0] + c[1]*np.exp(prop/c[2])
    gmag  = df[GMAG].to_numpy()
    rpmag = df[RPMAG].to_numpy()
    teff  = df[TEFF].to_numpy()
    errors = {k: np.zeros_like(gmag)*np.nan for k in [GMAG, RPMAG, BPMAG, PI, RA, DEC, PMRA, PMDEC, VR]}
    ################################
    maglims = (gmag>3.0) & (gmag<21.0)
    # error on gmag
    errors[GMAG][maglims] = _model(gmag[maglims], 'gmag')
    # error on rpmag and bpmag
    errors[RPMAG][maglims] = errors[BPMAG][maglims] = _model(gmag[maglims], 'bprpmag')
    # error on astrometrics (in mas)
    errors[PI][maglims] = errors[RA][maglims] = errors[DEC][maglims] = _model(gmag[maglims], 'pospar')
    # error on proper motions (in mas/yr)
    errors[PMRA][maglims] = errors[PMDEC][maglims] = _model(gmag[maglims], 'pm')
    # #change units for ra,dec errors to degrees
    errors[RA][maglims] *= MAS_TO_DEG
    errors[DEC][maglims] *= MAS_TO_DEG
    ################################
    grvs = grvs_from_g_rp(gmag, rpmag)
    maglims = (grvs<14) & (3550<=teff) & (teff<=6900)
    # error on radial velocities
    errors[VR][maglims] = _model(grvs[maglims], 'rv')
    errors[VR][maglims] = np.sqrt(errors[VR][maglims]**2 + 0.11**2) #systematic floor
    return errors

ph.available_photo_systems['padova/GAIA'].default_error_model = _temp
