import pandas as pd

from .. import utils as project
from . import tibber
from . import eon

import logging
logger = logging.getLogger(__name__)


def get_list() -> list:
    try: 
        return project.get_params()['load']
    except:
        return []

def get_frame(year=None, params=None) -> pd.DataFrame:
    df = pd.DataFrame()
    first = True
    
    if not isinstance(params, list):
        params = get_list()
    
    # TODO: load modules dynamicaly based on params
    for m in get_list():
        try:
            m['tibber']
        except:
            pass
        else:
            df_m = tibber.get_frame(name=m['name'], params=m['tibber'], year=year)
            if first == True:
                first = False
                df = df_m
            else:
                df['load'] += df_m['load']

        try:
            m['eon']
        except:
            pass
        else:
            df_m = eon.get_frame(name=m['name'], params=m['eon'], year=year)
            if first == True:
                first = False
                df = df_m
            else:
                df['load'] += df_m['load']
                
                
                

    return df


def get_slug() -> str:
    slug = project.get_slug() + '_load'
    project.add_slug(slug=slug, name='Load')
    return slug


def do_simulate(year: int, params: dict, data: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    return df