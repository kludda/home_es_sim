import os
import argparse

import logging
logger = logging.getLogger(__name__)

import pandas as pd
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import base64

from ..grid.export_price import tibber as export_price
from ..grid.import_price import tibber as import_price
from ..load import tibber as load

from .. import utils as project


_demo_token = "3A77EECF61BD445F47241A5A36202185C35AF3AF58609E19B53F3A8872AD7BE1-1"

# https://github.com/Danielhiversen/pyTibber/blob/master/tibber/gql_queries.py
_qql_query = ( """
{{
  viewer {{
    homes {{
      consumption(resolution: HOURLY, first: 744, after: "{}") {{
        nodes {{
          from
          unitPrice
          unitPriceVAT
          currency
          consumption
        }}
      }}
    }}
  }}
}}
""" )

_tibber_import_fixed = {
    2024: {
        "202412": 0.069,
        "202411": 0.069,
        "202410": 0.076,
        "202409": 0.08,
        "202408": 0.08,
        "202407": 0.08,
        "202406": 0.08,
        "202405": 0.08,
        "202404": 0.081,
        "202403": 0.0841,
        "202402": 0.094,
        "202401": 0.094
    },
    2023: {
        "202312": 0.0976,
        "202311": 0.0978,
        "202310": 0.0982,
        "202309": 0.0982,
        "202308": 0.083,
        "202307": 0.0849,
        "202306": 0.0789,
        "202305": 0.0795,
        "202304": 0.094,
        "202303": 0.094,
        "202302": 0.094,
        "202301": 0.1096
    }
}




def get_raw_year(year: int, token: str, qql_query: str):
    transport = AIOHTTPTransport(url="https://api.tibber.com/v1-beta/gql", headers={'Authorization': "Bearer " + token})
    client = Client(transport=transport)

    df = pd.DataFrame()
    
    for month in range(12):
        ISOdate = str(year) + "-" + str(month+1).rjust(2, "0") + "-01T00:00:00Z"

        logger.info('Querying for month starting with ' + ISOdate + '...')

        ISOdate = ISOdate.encode("ascii")
        base64date = base64.b64encode(ISOdate)
        base64date = base64date.decode("ascii")

        query = gql(qql_query.format(base64date))
        result = client.execute(query)
        result = result['viewer']['homes'][0]['consumption']

        dfresult = pd.json_normalize(result, "nodes")
        df = pd.concat([df, dfresult])

    # Set 'from' to index
    df['from'] = pd.to_datetime(df['from'], utc=True)
    df.set_index('from', inplace=True, drop=True)
    df.index.name = 'time_utc'

    # Remove duplicate rows for months shorter than 744 hours
    df = df.loc[~df.index.duplicated(), :]
    
    if len(df) < 8700:
        logger.error('Result length < 8700')
        raise ValueError('Result from query wrong length, did you have Tibber subscription full year ' + str(year) + '?')

    return df


def clean_df(df):
    # clean df
    df.drop('unitPriceVAT', axis=1, inplace=True)
    df.drop('unitPrice', axis=1, inplace=True)
    df.drop('currency', axis=1, inplace=True)
    df.drop('consumption', axis=1, inplace=True)

    return df



def get_export_price(df, year):
    global _tibber_import_fixed
    # remove VAT from energy price
    df['grid_export_price'] = df['unitPrice'] - df['unitPriceVAT']

    # remove tibber fixed import fees
    try:
        _tibber_import_fixed[year]
    except:
        logger.warning('No data for Tibber fixed prices for year ' + str(year) + '. Will use 0.1 as an approximate.')
        _tibber_import_fixed[year] = {}
        for m in range(12):
            _tibber_import_fixed[year][str(year) + str(m+1).zfill(2)] = 0.1

    for ym in _tibber_import_fixed[year]:
        df.loc[df.index.strftime('%Y%m') == ym, 'grid_export_price'] = df.loc[df.index.strftime('%Y%m') == ym, 'grid_export_price'] - _tibber_import_fixed[year][ym]


    # add grid costs
    params = export_price.get_params()
    price_fixed = params['transfer price fixed']
    price_vat = params['price vat']

    df['grid_export_price'] = ( df['grid_export_price'] + price_fixed ) * price_vat

    # clean df
    df = clean_df(df)

    return df



def get_import_price(df):
    
    # remove VAT from price
    df['grid_import_price'] = df['unitPrice'] - df['unitPriceVAT']

    # add grid costs
    params = import_price.get_params()
    price_fixed = params['transfer price fixed']
    price_vat = params['price vat']

    df['grid_import_price'] = ( df['grid_import_price'] + price_fixed ) * price_vat

    # clean df
    df = clean_df(df)

    return df


def get_load_home(df):
    df['load'] = df['consumption']

    # clean df
    df = clean_df(df)

    return df




def get(year, token):
    df_raw = get_raw_year(year=year, token=token, qql_query=_qql_query)

    filename = project.save_frame(
        slug=export_price.get_slug(year=year),
        frame=get_export_price(df_raw.copy(), year)
    )
    logger.info('Grid export price saved to: ' + filename)
    
    filename = project.save_frame(
        slug=import_price.get_slug(year=year),
        frame=get_import_price(df_raw.copy())
    )
    logger.info('Grid import price saved to: ' + filename)

    filename = project.save_frame(
        slug=load.get_slug(year), 
        frame=get_load_home(df_raw.copy())
    )
    logger.info('Load home saved to: ' + filename)



if __name__ == "__main__":
    project.get_cli()

    try:
        year = int(project.get_moduleargs()['year'])
    except:
        raise ValueError("Missing argument year=fetchyear. Where fetchyear is the year for which you want to get Tibber data.")
        
    try:
        token = project.get_moduleargs()['tibbertoken']
    except:
        raise ValueError("Missing argument tibbertoken=token. Where token is your Tibber API token or DEMO for demo token.")
    
    if token.upper() == 'DEMO':
        token = _demo_token

    get(year, token)

    print("Data fetched from Tibber.")

