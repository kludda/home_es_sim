import pandas as pd

import pvlib
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.location import Location
from pvlib.modelchain import ModelChain

from ... import location
from ...location import weather

import logging
logger = logging.getLogger(__name__)


_modules = None
_inverters = None


def get_module(name):
    # only fetch once for each run
    global _modules
    if not isinstance(_modules, pd.DataFrame):
        logger.info('Fetching PV modules from GitHub/NREL/SAM...')
        # https://github.com/NREL/SAM/tree/develop/deploy/libraries
        _modules = pvlib.pvsystem.retrieve_sam(path="https://raw.githubusercontent.com/NREL/SAM/refs/heads/develop/deploy/libraries/CEC%20Modules.csv")

    return _modules[pvlib.pvsystem._normalize_sam_product_names(name)[0]]


def get_inverter(name):
    # only fetch once for each run
    global _inverters
    if not isinstance(_inverters, pd.DataFrame):
        logger.info('Fetching inverters from GitHub/NREL/SAM...')
        # https://github.com/NREL/SAM/tree/develop/deploy/libraries
        _inverters = pvlib.pvsystem.retrieve_sam(path="https://raw.githubusercontent.com/NREL/SAM/refs/heads/develop/deploy/libraries/CEC%20Inverters.csv")
        #sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

    return _inverters[pvlib.pvsystem._normalize_sam_product_names(name)[0]]


def get_temperature_model(name):
    return pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm'][name]


def parse_array(arrays):
    a  = []    
    for array in arrays:
        a.append(Array(
            mount=FixedMount(surface_tilt=array['tilt'], surface_azimuth=array['azimuth']),
            module_parameters=get_module(array['module']),
            temperature_model_parameters=get_temperature_model(array['mount']),
            modules_per_string=array['modules per string'],
            strings=array['strings'],
        ))

    return a


# Returns one year hourly simulated ac energy from PV system as Pandas.Series
def simulate_pv_energy(
    arrays,
    inverter,
    location,
    tmy
):

    system = PVSystem(arrays=arrays, inverter_parameters=inverter)
    mc = ModelChain(
        system,
        location,
        aoi_model='physical'  # CEC modules don't have data for default https://stackoverflow.com/questions/74118866/modelling-cec-and-sandia-modules-in-pvlib
    )

    logger.info('Running PV system simulation...')
    mc.run_model(tmy)

    # Wh -> kWh
    mc.results.ac  = mc.results.ac / 1000

    return mc.results.ac


#def run(name: str, pv_spec: dict) -> pd.DataFrame:
def run(pv_spec: dict) -> pd.Series:
    sim = pv_spec

    s = simulate_pv_energy(
        arrays = parse_array(sim['arrays']),
        inverter = get_inverter(sim['inverter']),
        location = location.get_pvlib_location(),
        tmy = weather.get_tmy()
    )

    return s