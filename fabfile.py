#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib import *

# Note: Cooja simulation file must be the last key in the following ordered dictionary
TEMPLATES = OrderedDict([
    ("motes/root.c", {}),
    ("motes/sensor.c", {}),
    ("motes/malicious.c", {}),
    ("Makefile", {"contiki": CONTIKI_FOLDER, "target": "z1"}),
    ("script.js", {"timeout": 300}),  # seconds
    ("simulation.csc", {
        "title": "Simulation",
        "goal": "Not specified",
        "notes": "",
        "target": "Z1",
        "random_seed": "generate",
        "transmitting_range": MAX_DIST_BETWEEN_MOTES,
        "interference_range": 2 * MAX_DIST_BETWEEN_MOTES,
        "success_ratio_tx": 1.0,
        "success_ratio_rx": 1.0,
        "mote_types": [
            {"name": "root", "description": "DODAG root"},
            {"name": "sensor", "description": "Normal sensor"},
            {"name": "malicious", "description": "Malicious node"},
        ],
    }),
])


# ****************************** TASKS ON INDIVIDUAL EXPERIMENT ******************************
@task
def clean(name):
    logging.debug(" > Cleaning folder...")
    with hide(*HIDDEN):
        with lcd(EXPERIMENT_FOLDER):
            local("rm -rf {}".format(name))


@task
def cooja(name, with_malicious=False):
    logging.debug("STARTING COOJA WITH EXPERIMENT '{}'".format(name))
    path = get_path(EXPERIMENT_FOLDER, name)
    with hide(*HIDDEN):
        with lcd(path):
            local("make cooja-with{}-malicious".format("" if with_malicious else "out"))


@task
def launch(name):
    logging.debug(" > Running both simulations (with and without the malicious mote)...")
    path = get_path(EXPERIMENT_FOLDER, name)
    with hide(*HIDDEN):
        get_path(EXPERIMENT_FOLDER, name, 'data')
        with lcd(path):
            local("make run-without-malicious")
            local("make run-with-malicious")
        remove_files(path,
                     'COOJA.log',
                     'COOJA.testlog')


@task
def make(name, target="z1", ext_lib=None):
    logging.debug(" > Making motes...")
    path = get_path(EXPERIMENT_FOLDER, name)
    with hide(*HIDDEN):
        with lcd(path):
            local("make motes/root TARGET=%s" % target)
            local("make motes/sensor TARGET=%s" % target)
            # after compiling, clean artifacts
            remove_files(path,
                         'contiki-{}.a'.format(target),
                         'contiki-{}.map'.format(target),
                         'symbols.c',
                         'symbols.h',
                         'motes/root.c',
                         'motes/sensor.c')
            remove_folder(os.path.join(path, 'obj_{}'.format(target)))
            if ext_lib is not None:
                # backup original RPL library and replace it with attack's library
                get_path('.tmp')
                move_folder(os.path.join(CONTIKI_FOLDER, 'core', 'net', 'rpl'), '.tmp')
                copy_folder(ext_lib, os.path.join(CONTIKI_FOLDER, 'core', 'net', 'rpl'))
            with settings(warn_only=True, abort_exception=Exception):
                try:
                    local("make motes/malicious TARGET=%s" % target)
                except Exception as e:
                    logger.error(str(e))
            if ext_lib is not None:
                # then, clean temporary files
                remove_folder(os.path.join(CONTIKI_FOLDER, 'core', 'net', 'rpl'))
                move_folder('.tmp/rpl', os.path.join(CONTIKI_FOLDER, 'core', 'net'))
                remove_folder('.tmp')
            remove_files(path,
                         'contiki-{}.a'.format(target),
                         'contiki-{}.map'.format(target),
                         'symbols.c',
                         'symbols.h',
                         'motes/malicious.c')
            remove_folder(os.path.join(path, 'obj_{}'.format(target)))
        with lcd(COOJA_FOLDER):
            local("ant clean")
            local("ant jar")


@task
def new(name, n=NBR_MOTES, mtype="sensor", blocks=None, duration=None, title=None, goal=None, notes=None, debug=None):
    logging.debug(" > Creating simulation...")
    # create experiment's directories
    path = get_path(EXPERIMENT_FOLDER, name)
    get_path(EXPERIMENT_FOLDER, name, 'motes')
    # select the right malicious mote template and duplicate the simulation file
    copy_files(TEMPLATES_FOLDER, TEMPLATES_FOLDER,
               ('motes/malicious-{}.c'.format(mtype), 'malicious.c'),
               ('simulation.csc', 'simulation_without_malicious.csc'),
               ('simulation.csc', 'simulation_with_malicious.csc'))
    # create experiment's files from templates
    render_templates(path, TEMPLATES, n, blocks, duration, title, goal, notes, debug)
    # then clean the templates folder from previously created files
    remove_files(TEMPLATES_FOLDER,
                 'motes/malicious.c',
                 'simulation_without_malicious.csc',
                 'simulation_with_malicious.csc')


@task
def parse(name):
    logging.debug(" > Parsing logs...")
    # create parsing folders
    path = get_path(EXPERIMENT_FOLDER, name, 'data')
    get_path(EXPERIMENT_FOLDER, name, 'results')
#    powertracker2csv(path)
    message(path)


@task
def plot(name):
    logging.debug(" > Plotting results...")
    path = get_path(EXPERIMENT_FOLDER, name)
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


# ****************************** TASKS ON EXPERIMENTS CAMPAIGN ******************************
@task
def make_all(exp_file="templates/experiments"):
    for name, params in get_experiments(exp_file).items():
        logging.info("CREATING EXPERIMENT '{}'".format(name))
        clean(name)
        if params.get("simulation") is None or params.get("malicious") is None:
            logging.error("Experiments JSON is not correctly formatted !")
            continue
        new(name,
            title=params.get("simulation").get("title"),
            goal=params.get("simulation").get("goal"),
            notes=params.get("simulation").get("notes"),
            duration=params.get("simulation").get("duration"),
            n=params.get("simulation").get("number_motes"),
            debug=params.get("simulation").get("debug"),
            mtype=params.get("malicious").get("type"),
            blocks=params.get("malicious").get("building-blocks"))
        ext_lib = params.get("malicious").get("external_library")
        if ext_lib and not os.path.exists(ext_lib):
            logging.error("External library does not exist !")
            continue
        make(name,
             target=params.get("simulation").get("target") or "z1",
             ext_lib=ext_lib)


@task
def run_all(exp_file="templates/experiments"):
    make_all(exp_file)
    for name in get_experiments(exp_file).keys():
        logging.info("PROCESSING EXPERIMENT '{}'".format(name))
        launch(name)
        parse(name)


# ****************************** SETUP TASKS FOR CONTIKI AND COOJA ******************************
@task
def config(contiki_folder='~/contiki', experiments_folder='~/Experiments'):
    with open(os.path.expanduser('~/.rpl-attacks.conf'), 'w') as f:
        f.write('[RPL Attacks Framework Configuration]\n')
        f.write('contiki_folder = {}\n'.format(contiki_folder))
        f.write('experiments_folder = {}\n'.format(experiments_folder))


@task
def prepare(exp_file):
    if not exp_file.endswith('.json'):
        exp_file += '.json'
    copy_files(TEMPLATES_FOLDER, EXPERIMENT_FOLDER, ('experiments.json', exp_file))


@task
def setup():
    try:
        with open('.cooja_addons_installed') as f:
            f.read()
        logging.debug("COOJA ADD-ONS ALREADY INSTALLED")
        return
    except IOError:
        with open('.cooja_addons_installed', 'w') as f:
            f.write("")
    logging.debug("INSTALLING COOJA ADD-ONS")
    with hide(*HIDDEN):
        modify_cooja(COOJA_FOLDER)
        update_cooja_build(COOJA_FOLDER)
        update_cooja_user_properties()
        visualizer = os.path.join(COOJA_FOLDER, 'apps', 'visualizer_screenshot')
        if not os.path.exists(visualizer):
            copy_folder('src/visualizer_screenshot', visualizer)
        with lcd(COOJA_FOLDER):
            with settings(warn_only=True):
                local("ant clean")
            local("ant jar")
