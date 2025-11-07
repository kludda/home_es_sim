import pandas as pd

from .. import utils as load
from ... import utils as project

import logging
logger = logging.getLogger(__name__)


def get_frame(name: str, params: dict, year: int) -> pd.DataFrame:
    df = pd.DataFrame()

    if isinstance(year, int):
        slug=get_slug(name=name, year=year)
        df = project.read_frame(slug=slug)

    return df


def get_slug(year: int, name=None) -> str:
    slug = load.get_slug() + '_tibber_' + str(year)
    project.add_slug(slug=slug, name=name)
    return slug

