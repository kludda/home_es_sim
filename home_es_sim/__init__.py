from . import utils
from . import report as rep

import logging
logger = logging.getLogger(__name__)


# datadir: abs path to folder where generated data can be saved
# projectfile: abs filepath to file where project definition can be found.
def init(datadir: str, projectfile: str, args=None):
    utils.set_projectfile(projectfile)
    utils.set_datadir(datadir)
    utils.set_moduleargs(args)


def cli():
    utils.get_cli()
    
    
def report():
    rep.do_report()
