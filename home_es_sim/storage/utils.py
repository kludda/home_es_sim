import numpy as np
import pandas as pd
import pulp

from . import battery
from .. import utils as project

import logging
logger = logging.getLogger(__name__)


def get_frame(year: int, params=None) -> pd.DataFrame:
    df = pd.DataFrame()
    return df


def get_slug() -> str:
    slug = project.get_slug() + '_storage'
    project.add_slug(slug=slug, name='Storages')
    return slug


def get_params() -> dict:
    return project.get_params()['storage']


def do_simulate(year: int, params: dict, data: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()

    # TODO: load modules dynamicaly based on params
    for s in params:
        if s == 'storage':
            df = battery.do_simulate(params=params, year=year, data=data)
        else:
            logger.debug("no battery: " + s)

    return df


if __name__ == "__main__":
    print("can't run like this")