from pvlib.location import Location
from .. import utils as project

import logging
logger = logging.getLogger(__name__)


def get_location(pvlib=False) -> dict:
    return dict(project.get_params()['location'])


def get_pvlib_location() -> Location:
    l = get_location()
    _pvlib_location = Location(
        latitude=l['latitude'],
        longitude=l['longitude'],
        name=l['name'],
        altitude=l['altitude'],
        tz=l['timezone']
    )
    return _pvlib_location


def get_name() -> dict:
    return get_location()['name']


def get_slug() -> str:
    return project.get_slug() + '_location'
