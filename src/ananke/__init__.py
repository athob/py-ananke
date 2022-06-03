#!/usr/bin/env python
"""
Docstring
"""
import pandas as pd
import EnBiD


def enbid_double(*args, **kwargs):
    pos, vel = args[0], args[1]
    name = kwargs.get('name', None)
    rho_pos = EnBiD.enbid(pos, name=name)
    rho_vel = EnBiD.enbid(vel, name=name)
    return pd.DataFrame.from_dict({'pos': rho_pos, 'vel': rho_vel})


if __name__ == '__main__':
    pass
