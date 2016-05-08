#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
import sh
from collections import OrderedDict
from fabric.api import env, get, hide, lcd, local, task
from jinja2 import Environment, FileSystemLoader
from makesense import parser, analyze, plot as pt
from makesense.graph import rpl_graph
from makesense.run import run_experiment
from os.path import join, expanduser
from remakesense import NBR_MOTES, MAX_DIST_BETWEEN_MOTES, _render_save_template, announce, generate_motes
from remakesense import parser as reparser, analyze as reanalyze
try:  # for Python2
    import ConfigParser as configparser
except ImportError:  # for Python3
    import configparser
try:
    import coloredlogs
    colored_logs_present = True
except:
    print("(Install 'coloredlogs' for colored logging)")
    colored_logs_present = False

LOG_LEVEL = logging.INFO
logging.basicConfig(format=' %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s', level=LOG_LEVEL)
if colored_logs_present:
    coloredlogs.install(LOG_LEVEL)

confparser = configparser.ConfigParser()
confparser.read(join(expanduser('~'), ".rpl-attacks.conf"))
try:
    CONTIKI_FOLDER = expanduser(confparser.get("RPL Attacks Framework Configuration", "contiki_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    CONTIKI_FOLDER = os.path.abspath(join(expanduser('~'), "contiki"))
COOJA_DIR = join(CONTIKI_FOLDER, "tools", "cooja")
try:
    EXPERIMENT_FOLDER = expanduser(confparser.get("RPL Attacks Framework Configuration", "experiments_folder"))
except (configparser.NoOptionError, configparser.NoSectionError):
    EXPERIMENT_FOLDER = join(expanduser('~'), "Experiments")
del confparser
if not os.path.exists(EXPERIMENT_FOLDER):
    os.makedirs(EXPERIMENT_FOLDER)
TEMPLATE_ENV = Environment(loader=FileSystemLoader(join(os.path.dirname(__file__), "templates")))

# Note: Cooja simulation file must be the last key in the following ordered dictionary
TEMPLATES = OrderedDict([
    ("root.c", {"debug": 0}),
    ("sensor.c", {"debug": 0}),
    ("malicious.c", {"debug": 0, "constants": None}),
    ("Makefile", {"contiki": CONTIKI_FOLDER, "target": "z1"}),
    ("script.js", {"timeout": 300}),  # seconds
    ("simulation.csc", {
        "title": "Simulation",
        "goal": "Not specified",
        "notes": "",
        "random_seed": 12345,
        "transmitting_range": MAX_DIST_BETWEEN_MOTES,
        "interference_range": 2 * MAX_DIST_BETWEEN_MOTES,
        "success_ratio_tx": 1.0,
        "success_ratio_rx": 1.0,
        "mote_types": [
            {"name": "root", "description": "DODAG root"},
            {"name": "sensor", "description": "Normal sensor"},
            {"name": "malicious", "description": "Malicious node"},
        ],
        "motes": None,
        "script": None,
    }),
])


@task
def clean(name):
    with lcd(EXPERIMENT_FOLDER):
        local("rm -rf {}".format(name))


@task
def cooja(name):
    with lcd(join(EXPERIMENT_FOLDER, name)):
        local("make cooja")


@task
def launch(name):
    with lcd(join(EXPERIMENT_FOLDER, name)):
        local("make run")


@task
def make(name, target="z1", ext_lib=None):
    with lcd(join(EXPERIMENT_FOLDER, name)):
        with hide("output"):
            local("make root TARGET=%s" % target)
            local("make sensor TARGET=%s" % target)
            if ext_lib is not None:
                # backup original RPL library and replace it with attack's library
                sh.mkdir('-p', '.tmp')
                try:
                    sh.mv(join(CONTIKI_FOLDER, 'core', 'net', 'rpl'), './.tmp')
                except:  # occurs when folder was already moved (i.e. if this task failed previously)
                    pass
                sh.cp('-R', ext_lib, join(CONTIKI_FOLDER, 'core', 'net', 'rpl'))
                input()
            local("make malicious TARGET=%s" % target)
            if ext_lib is not None:
                # then, clean temporary files
                sh.rm('-r', join(CONTIKI_FOLDER, 'core', 'net', 'rpl'))
                sh.mv('./.tmp/rpl', join(CONTIKI_FOLDER, 'core', 'net'))
                sh.rmdir('.tmp')
    with lcd(COOJA_DIR):
        with hide("output"):
            local("ant clean")
            local("ant jar")


@task
def new(name, n=NBR_MOTES, mtype="sensor", constants=None, duration=None, title=None, goal=None, notes=None, debug=None):
    for sim_key in TEMPLATES.keys():
        pass  # this is used to retrieve the last key as keys() does not give a sliceable object for OrderedDict
    path = join(EXPERIMENT_FOLDER, name)
    if not os.path.exists(path):
        os.makedirs(path)
    # select the right C template to prepare source 'malicious.c'
    sh.cp('./templates/malicious-{}.c'.format(mtype), './templates/malicious.c')
    TEMPLATES["root.c"]["debug"] = ["DEBUG_NONE", "DEBUG_PRINT"][debug or 0]
    TEMPLATES["sensor.c"]["debug"] = ["DEBUG_NONE", "DEBUG_PRINT"][debug or 0]
    TEMPLATES["malicious.c"]["debug"] = ["DEBUG_NONE", "DEBUG_PRINT"][debug or 0]
    TEMPLATES["malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) for c in constants.items()]) or ""
    TEMPLATES["script.js"]["timeout"] = 1000 * int(duration or TEMPLATES["script.js"]["timeout"])
    TEMPLATES["script.js"]["powertracker_frequency"] = TEMPLATES["script.js"]["timeout"] // 100
    TEMPLATES["simulation.csc"]["title"] = title or TEMPLATES["simulation.csc"]["title"]
    TEMPLATES["simulation.csc"]["goal"] = goal or TEMPLATES["simulation.csc"]["goal"]
    TEMPLATES["simulation.csc"]["notes"] = notes or TEMPLATES["simulation.csc"]["notes"]
    TEMPLATES["simulation.csc"]["motes"] = generate_motes(int(n or NBR_MOTES))
    rendered_template = None
    for template_name, kwargs in TEMPLATES.items():
        logging.debug(" > Setting template file: {}".format(template_name))
        if template_name == sim_key:
            kwargs["script"] = rendered_template  # this of the Javascript to be rendered into the simulation file
        rendered_template = _render_save_template(path, TEMPLATE_ENV, template_name, **kwargs)
    # then, clean temporary file 'malicious.c'
    sh.rm('./templates/malicious.c')


@task
def parse(name):
    path = join(EXPERIMENT_FOLDER, name)
    reparser.powertracker2csv(path)
    parser.message(path)
    reparser.pcap2csv(path)
    parser.format_pcap_csv(path)
    analyze.depth(path)
    rpl_graph(path)
    reanalyze.dashboard(path)
    analyze.strobes(path)
    analyze.strobes_depth(path)


@task
def plot(name):
    path = join(EXPERIMENT_FOLDER, name)
    pt.overhead(path)
    pt.dashboard(path)
    pt.protocol_repartition_depth(path)
    pt.protocol_repartition_aggregated(path)
    pt.protocol_repartition(path)
    pt.pdr(path)
    pt.pdr_depth(path)
    pt.strobes(path)
    pt.strobes_depth(path)
    pt.energy(path)
    pt.energy_depth(path)


@task
def run_all(exp_file="templates/experiments"):
    exp_file = expanduser(exp_file)
    if not exp_file.endswith(".json"):
        exp_file += ".json"
    if not os.path.exists(exp_file):
        logging.critical("Simulation campaign JSON file does not exist !")
        exit(2)
    with open(exp_file) as f:
        experiments = json.load(f)
    for name, params in experiments.items():
        logging.info("PROCESSING EXPERIMENT '{}'".format(name))
        clean(name)
        if params.get("simulation") is None or params.get("malicious") is None:
            logging.error("Experiments JSON is not correctly formatted !")
            exit(2)
        new(name,
            title=params.get("simulation").get("title"),
            goal=params.get("simulation").get("goal"),
            notes=params.get("simulation").get("notes"),
            duration=params.get("simulation").get("duration"),
            n=params.get("simulation").get("number_motes"),
            debug=params.get("simulation").get("debug"),
            mtype=params.get("malicious").get("type"),
            constants=params.get("malicious").get("constants"))
        ext_lib = params.get("malicious").get("external_library")
        if ext_lib and not os.path.exists(ext_lib):
            logging.error("External library does not exist !")
            exit(2)
        make(name,
            target=params.get("simulation").get("target") or "z1",
            ext_lib=ext_lib)
        launch(name)
        parse(name)
        #plot(name)

