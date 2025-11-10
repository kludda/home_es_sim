import os
import pandas as pd
import yaml
import re
import argparse
import pvlib

from . import location

import logging
logger = logging.getLogger(__name__)


# Pandas DataFrame helpers

def read_frame(slug: str) -> pd.DataFrame:
    file = slug + '.pkl'
    file = get_datadir() + file
    logger.debug("Reading file '" + file + "' for slug '" + slug + "'")
    return pd.read_pickle(file)
    

def save_frame(slug: str, frame: pd.DataFrame) -> str:
    file = slug + '.pkl'
    file = get_datadir() + file
    logger.debug("Saving file '" + file + "' for slug '" + slug + "'")
    frame.to_pickle(file)
    return file

def roll_frame(frame: pd.DataFrame, toyear:int) -> pd.DataFrame:
    df = pvlib.iotools.pvgis._coerce_and_roll_tmy(frame, None, toyear)
    return df
    
# Project definition helpers

_project = None
_project_file = None
_datadir = None
_output_file = None

def get_params(file=None) -> dict:
    global _project
    if not isinstance(_project, dict):
        _project = parse_yaml(_project_file)
    return _project


def set_projectfile(file: str) -> str:
    logger.debug("project file set to: " + file)
    global _project_file
    _project_file = file
    return _project_file


def get_projectfile() -> str:
    global _project_file
    return _project_file


def set_datadir(datadir: str) -> str:
    logger.debug("data dir set to: " + datadir)
    global _datadir
    _datadir = datadir
    return _datadir


def get_datadir() -> str:
    global _datadir
    if _datadir is None:
        raise ValueError(__name__ + ": project not set, did you forget to set_datadir()?")
    return _datadir + '/'

def set_outputfile(file: str) -> str:
    logger.debug("output file set to: " + file)
    global _output_file
    _output_file = file
    return _output_file


def get_outputfile() -> str:
    global _output_file
    return _output_file


def get_slug() -> str:
    return slugify(location.get_name())


def parse_yaml(file) -> dict:
    with open(file, encoding='utf-8') as stream:
        return yaml.safe_load(stream)


# Slug helpers

_slugs = {}

def slugify(text) -> str:
    # Removes all special characters except spaces and alphanumeric characters
    text = text.strip()
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9]', '_', text)
    return text


def add_slug(slug: str, name: str):
    global _slugs
    _slugs[slug] = name


def get_slug_for_name(slug: str):
    global _slugs
    return _slugs[slug]



# current helpers. modules can use to determine if e.g. a simlulation shall be run again.

_current = {}

def get_current(slug: str) -> bool:
    global _current
    try:
        _current[slug]
    except:
        return False
    return _current[slug]

def set_current(slug: str, current=True):
    global _current
    _current[slug] = current


# additional args to be forwarded to modules "k=v ..."

_moduleargs = {}

def get_moduleargs() -> dict:
    global _moduleargs
    return _moduleargs


def set_moduleargs(moduleargs):
    global _moduleargs
    for kv in moduleargs:
        k = kv.split('=')[0]
        v = ''.join(kv.split('=')[1:])  # maybe value can contain = so take slice
        _moduleargs[k] = v
    logger.debug("moduleargs set to: " + str(_moduleargs))


# cli helpers

def get_cli():
    parser = argparse.ArgumentParser()

    req_grp = parser.add_argument_group(title='required')
    
    req_grp.add_argument('-p',
                        dest='simulation_file', 
                        help='File path containing project definition. Relative from current folder.', 
                        type=str, 
                        required=True 
                        )

    req_grp.add_argument(
                        '-d',
                        dest='data_dir', 
                        help='Path to folder where data will be saved. Relative from current folder.', 
                        type=str, 
                        required=True 
                        )

    parser.add_argument(
                        '-o',
                        dest='output', 
                        help='Output report filename. Will overwrite if exist. Default: report.pdf', 
                        default='report.pdf', 
                        type=str
                        )
                        
    parser.add_argument(
                        '--log', 
                        dest='loglevel', 
                        default='WARNING', 
                        help='logger loglevel: DEBUG, INFO, WARNING', 
                        type=str 
                        )


    parser.add_argument(
                        'args',
                        nargs=argparse.REMAINDER,
                        help='Optional. Additional args to be passed to sub modules'
                        )


    args = parser.parse_args()
    
    loglevel = args.loglevel

    getattr(logging, loglevel.upper())
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    data_dir = os.getcwd() + '/' + args.data_dir
    project_file = os.getcwd() + '/' + args.simulation_file
    output_file = os.getcwd() + '/' + args.output
    moduleargs = args.args

    set_projectfile(project_file)
    set_datadir(data_dir)
    set_outputfile(output_file)
    set_moduleargs(moduleargs)

    return True