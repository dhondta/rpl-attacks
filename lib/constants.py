# -*- coding: utf8 -*-
try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser
from os import makedirs
from os.path import abspath, dirname, exists, expanduser, join, pardir

from collections import OrderedDict


VERSION = '1.2'

# configuration parsing and main constants setting
confparser = configparser.ConfigParser()
confparser.read(expanduser('~/.rpl-attacks.conf'))
try:
    CONTIKI_FOLDER = expanduser(confparser.get("RPL Attacks Framework Configuration", "contiki_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    CONTIKI_FOLDER = abspath(expanduser('~/contiki'))
COOJA_FOLDER = join(CONTIKI_FOLDER, "tools", "cooja")
try:
    EXPERIMENT_FOLDER = expanduser(confparser.get("RPL Attacks Framework Configuration", "experiments_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    EXPERIMENT_FOLDER = expanduser('~/Experiments')
del confparser
if not exists(EXPERIMENT_FOLDER):
    makedirs(EXPERIMENT_FOLDER)
FRAMEWORK_FOLDER = join(dirname(__file__), pardir)
TEMPLATES_FOLDER = join(FRAMEWORK_FOLDER, "templates")

# simulation default parameters
MIN_DIST_BETWEEN_MOTES = 20.0
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

EXPERIMENT_STRUCTURE = {
    "Makefile": False,
    "simulation_with_malicious.csc": False,
    "simulation_without_malicious.csc": False,
    "script.js": False,
    ".simulation.conf": False,
    "data": {},
    "motes": {
        "root.*": False,
        "sensor.*": False,
        "malicious.*": False,
    },
    "results": {},
}

BANNER = """   ___  ___  __     ___  __  __           __          ____                                   __
  / _ \/ _ \/ /    / _ |/ /_/ /____ _____/ /__ ___   / __/______ ___ _  ___ _    _____  ____/ /__
 / , _/ ___/ /__  / __ / __/ __/ _ `/ __/  '_/(_-<  / _// __/ _ `/  ' \/ -_) |/|/ / _ \/ __/  '_/
/_/|_/_/  /____/ /_/ |_\__/\__/\_,_/\__/_/\_\/___/ /_/ /_/  \_,_/_/_/_/\__/|__,__/\___/_/ /_/\_\.
                                                                                                 """

COMMAND_DOCSTRING = {
    "description": """
    {}
""",
    "arguments": """
Arguments:
{}
""", "examples": """
Examples:
{}
"""
}

MIN_TERM_SIZE = (40, len(BANNER.split('\n')[0]) + 10)

# Multi-processing constants
TASK_EXPIRATION = 60  # seconds
CONTIKI_FILES = [
    "core",
    "dev/{}",
    "platform/{}",
    "cpu/{}",
    "tools",
    "Makefile.include",
    "-tools/code-style",
    "-tools/coffee-manager",
    "-tools/collect-view",
    "-tools/cooja",
    "-tools/csc",
    "-tools/cygwin",
    "-tools/mspsim",
    "-tools/powertrace",
    "-tools/release-tools",
    "-tools/wpcapslip",
    "-tools/avr-makecoffeedata",
    "-tools/avr-makefsdata",
    "-tools/avr-make-symbols",
]