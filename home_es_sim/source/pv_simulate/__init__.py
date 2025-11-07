# https://pvlib-python.readthedocs.io/en/stable/user_guide/getting_started/introtutorial.html

import os
import pandas as pd

import pvlib

from . import sim
from .. import utils as source
from ... import utils as project

import logging
logger = logging.getLogger(__name__)


def get_frame(name: str, params: dict, year=None) -> pd.DataFrame:
    df = pd.DataFrame()

    slug=get_slug(name)

    if project.get_current(slug):
        logger.debug("'" + slug + "' is current. Serving DF.")
        df = project.read_frame(slug=slug)
    else:
        logger.debug("'" + slug + "' is not current. Running simulation.")
        df = sim.run(pv_spec=params).to_frame('source')
        project.save_frame(slug=slug, frame=df)
        project.set_current(slug)

    # if year change to year before return
    if isinstance(year, int):
        logger.debug("Got year. Rolling simulation to: " + str(year))
        # Move to year
        df = project.roll_frame(frame=df, toyear=year)

    return df


def get_slug(name: str, year=None) -> str:
    slug = source.get_slug() + '_pv_' + project.slugify(name)
    
    if isinstance(year, int):
        slug = slug + '_' + str(year)

    project.add_slug(slug=slug, name=name)
    return slug

