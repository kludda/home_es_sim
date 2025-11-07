import pandas as pd

from .. import utils as project

from . import export_price
from . import import_price


import logging
logger = logging.getLogger(__name__)


def get_frame(year: int, params=None) -> pd.DataFrame:
    if not isinstance(params, dict):
        params = get_params()
    
    df = import_price.get_frame(year=year, params=params)
    gep = export_price.get_frame(year=year, params=params)
    df = pd.concat([df, gep], axis=1)
    return df


def get_slug() -> str:
    slug = project.get_slug() + '_grid'
    project.add_slug(slug=slug, name='Grid')
    return slug


def get_params() -> dict:
    return project.get_params()['grid']


def do_simulate(year: int, params: dict, data: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    return df