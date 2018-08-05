# -*- coding: utf8 -*-
from collections import OrderedDict
try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser
from os import makedirs
from os.path import abspath, dirname, exists, expanduser, join, pardir


__all__ = [
    'BANNER',
    'COMMAND_DOCSTRING',
    'CONTIKI_FILES',
    'CONTIKI_FOLDER',
    'COOJA_FOLDER',
    'CRASH_REPORT_DATA',
    'DEBUG_FILES',
    'DEFAULTS',
    'DOCSERVER_PORT',
    'EXPERIMENT_FOLDER',
    'EXPERIMENT_STRUCTURE',
    'FRAMEWORK_FOLDER',
    'MIN_TERM_SIZE',
    'PIDFILE',
    'REPORT_THEME',
    'SHORTCUT_RPLA',
    'SHORTCUT_COOJA',
    'TASK_EXPIRATION',
    'TEMPLATES',
    'TEMPLATES_FOLDER',
]


# configuration parsing and main constants setting
confparser = configparser.ConfigParser()
confparser.read(expanduser('~/.rpl-attacks.conf'))
try:
    CONTIKI_FOLDER = abspath(expanduser(confparser.get("RPL Attacks Framework Configuration", "contiki_folder")))
except (configparser.NoOptionError, configparser.NoSectionError):
    CONTIKI_FOLDER = expanduser('~/contiki')
COOJA_FOLDER = join(CONTIKI_FOLDER, "tools", "cooja")
try:
    EXPERIMENT_FOLDER = abspath(expanduser(confparser.get("RPL Attacks Framework Configuration", "experiments_folder")))
except (configparser.NoOptionError, configparser.NoSectionError):
    EXPERIMENT_FOLDER = expanduser('~/Experiments')
del confparser
if not exists(EXPERIMENT_FOLDER):
    makedirs(EXPERIMENT_FOLDER)
FRAMEWORK_FOLDER = join(dirname(__file__), pardir, pardir)
TEMPLATES_FOLDER = join(FRAMEWORK_FOLDER, "templates")
PIDFILE = '/tmp/rpla.pid'

# Contiki template list of includes for specific mote target compilation (subfolders for 'dev', 'cpu', 'platform'
#  are determined based on the specified target).
# This is used for copying a minimal part of Contiki to an experiment folder for compiling custom malicious mote.
CONTIKI_FILES = [
    "core",
    "dev/{}",
    "platform/{}",
    "cpu/{}",
    "Makefile.include",
    "tools",
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

# This is the list of files to be edited for changing the debug flag at compilation time
#
# WARNING: Interesting debug messages are essentially found in the following files:
#           - rpl.c
#           - rpl-dag.c
#           - rpl-dag-root.c
#           - rpl-icmp6.c
#           - rpl-timers.c
#          If using several of them, memory overflow error can be thrown, e.g. with the Sky mote, and a fix should
#           ba applied in Makefile if more debugging is required.
#          See e.g. http://stackoverflow.com/questions/27818056/contiki-os-rom-partition
#                   http://lists.cetic.be/pipermail/6lbr-dev/2015-April/000478.html
#
DEBUG_FILES = ['rpl-icmp6.c']

# simulation default parameters
MIN_DIST_BETWEEN_MOTES = 20.0
MAX_DIST_BETWEEN_MOTES = 50.0
DEFAULTS = {
    "area-square-side": 200.0,
    "building-blocks": [],
    "duration": 600,
    "external-library": None,
    "goal": "",
    "transmission-range": MAX_DIST_BETWEEN_MOTES,
    "interference-range": None,  # set to 2 * transmission_range at parameter validation
    "minimum-distance-from-root": MIN_DIST_BETWEEN_MOTES,
    "notes": "",
    "number-motes": 10,
    "repeat": 1,
    "target": "z1",
    "malicious-target": None,
    "title": "Default title",
    "root": "dummy",
    "sensor": "dummy",
    "type": "sensor",
    "debug": True,
    "wsn-generation-algorithm": "quadrants",
}

# Note: Cooja simulation file must be the last key in the following ordered dictionary
TEMPLATES = OrderedDict([
    ("report.md", {}),
    ("motes/Makefile", {"contiki": CONTIKI_FOLDER}),
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
    "simulation.conf": False,
    "report.md": False,
    "with-malicious": {
        "Makefile": False,
        "simulation.csc": False,
        "script.js": False,
        "data": {},
        "motes": {
            "Makefile": False,
            "root.*": False,
            "sensor.*": False,
            "malicious.*": False,
        },
        "results": {"*": True},
    },
    "without-malicious": {
        "Makefile": False,
        "simulation.csc": False,
        "script.js": False,
        "data": {},
        "motes": {
            "root.*": False,
            "sensor.*": False,
        },
        "results": {"*": True},
    },
}

BANNER = """   ___  ___  __     ___  __  __           __          ____                                   __
  / _ \/ _ \/ /    / _ |/ /_/ /____ _____/ /__ ___   / __/______ ___ _  ___ _    _____  ____/ /__
 / , _/ ___/ /__  / __ / __/ __/ _ \/ __/  '_/(_-<  / _// __/ _ \/  ' \/ -_) |/|/ / _ \/ __/  '_/
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

# Desktop shortcuts
SHORTCUT_RPLA = """[Desktop Entry]
Comment=Framework for building attack simulations and motes against the Contiki implementation of RPL
Terminal=true
Name=RPL Attacks Framework
Path={path}
Exec=python main.py
Type=Application
Icon=rpla-icon
"""

SHORTCUT_COOJA = """[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Name=Cooja: The Contiki Network Simulator
Icon=cooja-icon
Path={path}
Exec=/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java -Xmx512m -Duser.language=en -classpath %s org.contikios.cooja.Cooja
StartupNotify=false
StartupWMClass=org-contikios-cooja-Cooja
OnlyShowIn=Unity;
X-UnityGenerated=true
""" % ':'.join(join(CONTIKI_FOLDER, "tools", "cooja", p) for p in \
    ["build", "lib/jdom.jar", "lib/log4j.jar", "lib/jsyntaxpane.jar", "lib/swingx-all-1.6.4.jar"])



# PDF report CSS theme
REPORT_THEME = join(TEMPLATES_FOLDER, "report", "default.css")

# Crash report parameters
CRASH_REPORT_DATA = (
    "RPL ATTACKS FRAMEWORK - CRASH REPORT",
    EXPERIMENT_FOLDER,
    "crash-report",
)

# Documentation server parameters
DOCSERVER_PORT = 8123
