import pandas as pd

from .. import utils as project
from . import pv_simulate

import logging
logger = logging.getLogger(__name__)


def get_list(params=None) -> list:
    try: 
        return project.get_params()['source']
    except:
        return []


def get_frames(year=None, params=None) -> dict:
    if not isinstance(params, list):
        params = get_list()

    retv = {}

    # TODO: load modules dynamicaly based on params
    for s in params:
        try:
            s['pv simulate']
        except:
            pass
        else:
            retv[s['name']] = pv_simulate.get_frame(name=s['name'], params=s['pv simulate'], year=year)

    return retv


def get_frame(year=None, params=None) -> pd.DataFrame:
    df = pd.DataFrame()
    first = True

    if not isinstance(params, list):
        params = get_list()

    # TODO: load modules dynamicaly based on params
    for s in params:
        try:
            s['pv simulate']
        except:
            logger.debug("no pv sim: ")
        else:
            df_s = pv_simulate.get_frame(name=s['name'], params=s['pv simulate'], year=year)
            if first == True:
                first = False
                df = df_s
            else:
                df['source'] += df_s['source']

    return df


def get_slug() -> str:
    slug = project.get_slug() + '_source'
    project.add_slug(slug=slug, name='Sources')
    return slug


def do_prepare() -> dict:
    pv_simulate.do_prepare()


def do_simulate(year: int, params: dict, data: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    return df