# https://pvlib-python.readthedocs.io/en/stable/user_guide/getting_started/introtutorial.html

import logging
logger = logging.getLogger(__name__)

import pandas as pd
import pvlib

from . import utils as location
from .. import utils as project


def get_slug() -> str:
    slug = location.get_slug() + '_tmy'
    project.add_slug(slug=slug, name='TMY (Typical Meteorological Year)')
    return slug


def get_tmy() -> pd.DataFrame:
    logger.info('Try to read TMY file...')

    tmy = pd.DataFrame()

    try:
        tmy = project.read_frame(get_slug())
    except:
        logger.info('Could not read TMY file. Try to fetch...')

        l = location.get_location()
        tmy = pvlib.iotools.get_pvgis_tmy(latitude=l['latitude'], longitude=l['longitude'])[0]
        tmy.index.name = "time_utc"

        logger.info('Saving tmy file...')        
        project.save_frame(slug=get_slug(), frame=tmy)
    else:
        logger.info('TMY restored from file.')
    
    return tmy

