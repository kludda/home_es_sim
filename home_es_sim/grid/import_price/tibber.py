import pandas as pd

import logging
logger = logging.getLogger(__name__)

from . import utils as import_price
from ... import utils as project


def get_params() -> dict:
    return import_price.get_params()['tibber']


def get_frame(year: int) -> pd.DataFrame:
    slug = get_slug(year=year)
    df = project.read_frame(slug=slug)
    return df


def get_slug(year: int) -> str:
    slug = import_price.get_slug() + '_tibber_' + str(year)
    project.add_slug(slug=slug, name='Grid import price' + str(year))
    return slug



