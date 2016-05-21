# -*- coding: utf8 -*-
import os
try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser
from jinja2 import Environment, FileSystemLoader


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
