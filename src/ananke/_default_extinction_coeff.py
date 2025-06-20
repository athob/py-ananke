#!/usr/bin/env python
"""
Contains the definition of default extinction coefficient estimators for
existing photometric systems of Galaxia.

Please note that this module is private.
"""
import numpy as np
import pyvo
from astropy import units, table, coordinates

from galaxia_ananke import photometry as ph


__all__ = ['universal_extinction_law', 'marshall2006']


def _wang_and_chen_2019_eq_9(lambda_eff):
    # for optical 0.3 to 1 micron
    lambda_eff = units.Quantity(lambda_eff, unit='micron').value
    coefficients = np.array([[1.0, 0.7499, -0.1086, -0.08909, 0.02905, 0.01069, 0.001707, -0.001002]]).T
    Y = 1/lambda_eff - 1.82
    return np.matmul(Y[...,np.newaxis]**np.arange(coefficients.shape[0])[np.newaxis], coefficients)[...,0]


def _wang_and_chen_2019_eq_10(lambda_eff):
    # for near IR 1 to 3.33 micron
    lambda_eff = units.Quantity(lambda_eff, unit='micron').value
    coefficient = 0.3722
    exponent = -2.070
    return coefficient * lambda_eff**exponent


def universal_extinction_law(lambda_eff):
    # return extinction coefficient A_lambda/A_V at lambda effective
    lambda_eff = units.Quantity(lambda_eff, unit='micron').value
    choose = np.vstack([
        np.zeros(lambda_eff.shape[0]),
        _wang_and_chen_2019_eq_9(lambda_eff),
        _wang_and_chen_2019_eq_10(lambda_eff)
        ]).T
    choice = choose[:,0].astype('int')
    choice[(0.3 < lambda_eff) & (lambda_eff < 1)] = 1  # optical
    choice[(1 < lambda_eff) & (lambda_eff < 3.33)] = 2  # NIR
    return choose[np.arange(choose.shape[0]), choice]


def __remove_description_from_quantity(quantity):
    quantity.info.description = ""
    return quantity


voresource = pyvo.registry.search(ivoid="ivo://CDS.VizieR/J/A+A/453/635")[0]
marshall2006 = voresource.get_service("tap").run_sync(f'select * from "{list(voresource.get_tables().keys())[0]}"').to_qtable()
marshall2006.sort('nb')
marshall2006 = table.vstack([
        table.vstack([
            table.QTable({
                k.replace(f'{i}',''): __remove_description_from_quantity(t[k])
                for k in ['GLON', 'GLAT', f'r{i}', f'ext{i}']})
            for i in range(1,t['nb'][0]+1)])
        for t in marshall2006.group_by('nb').groups])
marshall2006 = table.hstack([marshall2006, table.QTable(dict(zip(['x','y','z'], coordinates.Galactic(l=marshall2006['GLON'], b=marshall2006['GLAT'], distance=marshall2006['r']).cartesian.xyz.to('kpc'))))])
marshall2006['ext'] /= universal_extinction_law([dict(zip(ph.available_photo_systems['padova/GAIA__0+TYCHO+2MASS'].mag_names, ph.available_photo_systems['padova/GAIA__0+TYCHO+2MASS'].effective_wavelengths))['Ks'].to('micron').value])[0]


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
        'gaia__dr2_g': [0.0, 0.9761,-0.1704,0.0086,0.0011,-0.0438,0.0013,0.0099],
        'gaia__dr2_gbp':[0.0, 1.1517,-0.0871,-0.0333,0.0173,-0.0230,0.0006,0.0043],
        'gaia__dr2_grp':[0.0, 0.6104,-0.0170,-0.0026,-0.0017,-0.0078,0.00005,0.0006]
    }
    bp_rp_int = df['gaia__dr2_gbp'] - df['gaia__dr2_grp']
    A_0 = df['A_0']
    # Coeffients from Equation 1 of Babusiaux et al. 2018
    return {b: c[1] + c[2]*bp_rp_int + c[3]*bp_rp_int**2 + c[4]*bp_rp_int**3 +c[5]*A_0 +c[6]*A_0**2 +c[7]*bp_rp_int*A_0 for b,c in consts.items()}

ph.available_photo_systems['padova/GAIA__DR2'].default_extinction_coeff = _temp

# def _temp():
#     """
#     Default extinction coefficient function for the JWST NIRCam photometric
#     system.

#     Notes
#     -----
#     Extinction coefficients are adapted from Table 2 of Wang et al. 2024
#     (ui.adsabs.harvard.edu/abs/2024ApJ...964L...3W) assuming an average alpha
#     value of 1.98, and using the V-band to F200W relative extinction
#     coefficient showcased in Table 5 of Wang et al. 2019
#     (ui.adsabs.harvard.edu/abs/2019ApJ...877..116W)
#     """
#     # Extinction coefficients from Table 2 of Wang et al. 2024
#     coeffs_vs_f200w = {
#         'jwst__nircam_f070w': 7.321,
#         'jwst__nircam_f090w': 4.791,
#         'jwst__nircam_f115w': 2.965,
#         'jwst__nircam_f150w': 1.75,
#         'jwst__nircam_f200w': 1.0,
#         'jwst__nircam_f277w': 0.524,
#         'jwst__nircam_f356w': 0.306,
#         'jwst__nircam_f444w': 0.193,
#         'jwst__nircam_f150w2': 1.772,
#         'jwst__nircam_f322w2': 0.422,
#         'jwst__nircam_f140m': 1.972,
#         'jwst__nircam_f162m': 1.48,
#         'jwst__nircam_f182m': 1.154,
#         'jwst__nircam_f210m': 0.874,
#         'jwst__nircam_f250m': 0.623,
#         'jwst__nircam_f300m': 0.45,
#         'jwst__nircam_f335m': 0.349,
#         'jwst__nircam_f360m': 0.288,
#         'jwst__nircam_f410m': 0.225,
#         'jwst__nircam_f430m': 0.199,
#         'jwst__nircam_f460m': 0.18,
#         'jwst__nircam_f480m': 0.166
#     }
#     # V-band to F200W coefficient from Table 5 of Wang et al. 2019
#     V_to_f200w_coeff = 0.0919
#     return {b: V_to_f200w_coeff*c for b,c in coeffs_vs_f200w.items()}

# ph.available_photo_systems['padova/JWST__NIRCam'].default_extinction_coeff = _temp()


if __name__ == '__main__':
    raise NotImplementedError()
