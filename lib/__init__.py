# -*- coding: utf8 -*-
import logging
import os

try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser

from collections import OrderedDict
from fabric.api import hide, lcd, local, settings, task
from jinja2 import Environment, FileSystemLoader

from makesense import plot as pt
from makesense.analyze import depth, strobes, strobes_depth
from makesense.graph import rpl_graph
from makesense.parser import message, format_pcap_csv

from .analyze import dashboard
from .helpers import copy_files, copy_folder, move_folder, remove_files, remove_folder, render_templates
from .install import modify_cooja, update_cooja_build, update_cooja_user_properties
from .parser import powertracker2csv, pcap2csv
from .utils import get_experiments, get_path


# logging configuration
LOG_LEVEL = logging.INFO
logging.basicConfig(format=' %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s', level=LOG_LEVEL)
HIDDEN = ['warnings', 'stdout', 'stderr', 'running']
try:
    import coloredlogs
    coloredlogs.install(logging.DEBUG)
except:
    print("(Install 'coloredlogs' for colored logging)")
logger = logging.getLogger('sh.command')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.streamreader')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.stream_bufferer')
logger.setLevel(level=logging.WARNING)

# configuration parsing and main constants setting
confparser = configparser.ConfigParser()
confparser.read(os.path.expanduser('~/.rpl-attacks.conf'))
try:
    CONTIKI_FOLDER = os.path.expanduser(confparser.get("RPL Attacks Framework Configuration", "contiki_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    CONTIKI_FOLDER = os.path.abspath(os.path.expanduser('~/contiki'))
COOJA_FOLDER = os.path.join(CONTIKI_FOLDER, "tools", "cooja")
try:
    EXPERIMENT_FOLDER = os.path.expanduser(confparser.get("RPL Attacks Framework Configuration", "experiments_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    EXPERIMENT_FOLDER = os.path.expanduser('~/Experiments')
del confparser
if not os.path.exists(EXPERIMENT_FOLDER):
    os.makedirs(EXPERIMENT_FOLDER)
FRAMEWORK_FOLDER = os.path.join(os.path.dirname(__file__), os.path.pardir)
TEMPLATES_FOLDER = os.path.join(FRAMEWORK_FOLDER, "templates")
TEMPLATE_ENV = Environment(loader=FileSystemLoader(TEMPLATES_FOLDER))

# simulation default parameters
NBR_MOTES = 10
MAX_XY_POSITION = [100, 100]
MIN_DIST_BETWEEN_MOTES = 15.0
MAX_DIST_BETWEEN_MOTES = 50.0
