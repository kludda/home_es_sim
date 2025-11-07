import os
import pandas as pd

from ... import utils as project
from ... import grid as grid
from .. import utils as storage
from . import simulate

import logging
logger = logging.getLogger(__name__)


def do_simulate(params: dict, year: int, data: pd.DataFrame):

    batt = params['storage']['battery']

    # drop leap day if present
    data.drop(data.loc[data.index.strftime('%m%d') == '0229'].index, inplace=True)

    args = {
        'df': data,
        'b_capacity': batt['capacity'],
        'b_c_rate': batt['rate'],
        'b_d_rate': batt['rate']
    }

    try:
        args['g_cap'] = grid.get_params()['capacity']
    except:
        pass

    try:
        args['c_deg'] = batt['degradation cost']
    except:
        pass

    try:
        args['b_c_eff'] = batt['charge efficiency']
    except:
        pass

    try:
        args['b_d_eff'] = batt['discharge efficiency']
    except:
        pass        
    
        b_c_eff=batt['rate'],
        b_d_eff=batt['rate'],


    try:
        args['b_soc_min'] = params['soc min']
    except:
        pass        
    
        b_c_eff=batt['rate'],
        b_d_eff=batt['rate'],

    try:
        args['b_soc_max'] = params['soc max']
    except:
        pass        
    
        b_c_eff=batt['rate'],
        b_d_eff=batt['rate'],

    df = simulate.optimize_battery(**args)
    return df


def get_slug(name: str, year=None) -> str:
    slug = storage.get_slug() + '_battery_' + project.slugify(name)
    
    if isinstance(year, int):
        slug = slug + '_' + str(year)

    project.add_slug(slug=slug, name=name)
    return slug
