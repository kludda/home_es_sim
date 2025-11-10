import pandas as pd

from ... import utils as project
from ... import location
from .. import utils as load


import logging
logger = logging.getLogger(__name__)


#def get_params() -> dict:
    #return load.get_list()['from_csv']


def get_frame(name: str, params: dict, year: int) -> pd.DataFrame:
    file = params['from csv']
    tz = location.get_location()['timezone']

    # read CSV
    file = project.get_datadir() + file
    df = pd.read_csv(file, sep=';', decimal=',', header=2, usecols=['Starttidpunkt', 'Energiriktning', 'Kvantitet'])

    # convert to tz naive datetime
    df['Starttidpunkt'] = pd.to_datetime(df['Starttidpunkt'], utc=False)

    # set time to index
    df.set_index('Starttidpunkt', inplace=True, drop=True)
    df.index.name = 'time_utc'

    # localize time to location.timezone
    df = df.tz_localize(tz=tz, ambiguous='infer')

    # convert to UTC
    df = df.tz_convert('UTC')

    # change sign if data is not 'förbrukning'
    df.loc[~df["Energiriktning"].str.contains("Förbrukning"),['Kvantitet']] = df['Kvantitet'] * -1

    # clean df
    df.drop('Energiriktning', axis=1, inplace=True)
    df.rename(columns={'Kvantitet': 'load'}, inplace=True)

    # only return the requested year
    df = df.loc[df.index.strftime('%Y') == str(year)]

    return df


def get_slug(year: int, name=None) -> str:
    slug = load.get_slug() + '_tibber_' + str(year)
    project.add_slug(slug=slug, name=name)
    return slug

