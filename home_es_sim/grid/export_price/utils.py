import pandas as pd

import logging
logger = logging.getLogger(__name__)

from ... import utils as project
from .. import utils as grid
from . import tibber


def get_params() -> dict:
    return grid.get_params()['export price']


def get_frame(year: int, params=None) -> pd.DataFrame:
    df = pd.DataFrame()
    
    if not isinstance(params, dict):
        params = get_params()

    if len(get_params()) < 1:
        raise ValueError('At least one data source for \'export price\' must be defined.')
    
    # TODO: load modules dynamicaly based on params
    for m in get_params():
        if m == 'tibber':
            logger.debug("Found tibber. Serving tibber DF.")
            df = tibber.get_frame(year=year)
        else:
            logger.debug("not tibber")

    return df


def get_slug() -> str:
    slug = grid.get_slug() + '_export_price'
    return slug



