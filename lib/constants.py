# -*- coding: utf8 -*-
import os
try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser
from jinja2 import Environment, FileSystemLoader

from collections import OrderedDict


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
MIN_DIST_BETWEEN_MOTES = 15.0
MAX_DIST_BETWEEN_MOTES = 50.0
DEFAULTS = {
    "area-square-side": 200.0,
    "building-blocks": [],
    "duration": 300,
    "external-library": None,
    "goal": "",
    "interference_range": 2 * MAX_DIST_BETWEEN_MOTES,
    "maximum-distance-between-motes": MAX_DIST_BETWEEN_MOTES,
    "maximum-range-from-root": MAX_DIST_BETWEEN_MOTES,
    "minimum-distance-between-motes": MIN_DIST_BETWEEN_MOTES,
    "notes": "",
    "number-motes": 10,
    "repeat": 1,
    "target": "z1",
    "title": "Default title",
    "transmitting_range": MAX_DIST_BETWEEN_MOTES,
    "type": "sensor",
}

# Note: Cooja simulation file must be the last key in the following ordered dictionary
TEMPLATES = OrderedDict([
    ("motes/root.c", {}),
    ("motes/sensor.c", {}),
    ("motes/malicious.c", {}),
    ("Makefile", {"contiki": CONTIKI_FOLDER}),
    ("script.js", {}),
    ("simulation.csc", {
        "random_seed": "generate",
        "success_ratio_tx": 1.0,
        "success_ratio_rx": 1.0,
        "mote_types": [
            {"name": "root", "description": "DODAG root"},
            {"name": "sensor", "description": "Normal sensor"},
            {"name": "malicious", "description": "Malicious node"},
        ],
    }),
])
