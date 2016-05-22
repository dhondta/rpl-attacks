# -*- coding: utf8 -*-
import copy
import json
import logging
import math
import os
import random

from . import CONTIKI_FOLDER, MAX_DIST_BETWEEN_MOTES, MAX_XY_POSITION, MIN_DIST_BETWEEN_MOTES, NBR_MOTES, TEMPLATE_ENV


# **************************************** PROTECTED FUNCTIONS ****************************************
def _generate_mote(motes, mote_id, mote_type, max_xy=MAX_XY_POSITION, dmin=MIN_DIST_BETWEEN_MOTES, dmax=MAX_DIST_BETWEEN_MOTES * 0.9):
    """
    This function generates a dictionary for a mote with its random position taking some criteria into account:
     - the new mote must be at a distance of at least 'dmin' from every other existing motes
     - the new mote must be at a distance of at most 'dmax' from every other existing motes (not to be isolated)

    :param motes: list of existing motes
    :param mote_id: new mote's ID
    :param mote_type: new mote's type
    :param max_xy: maximum (x, y) values ; defines a square of size 2*x
    :param dmin: minimum distance between all motes
    :param dmax: maximum distance between all motes
    :return:
    """
    while True:
        d, r, x = float("Inf"), random.randint(dmin, dmax), random.randint(-max_xy[0], max_xy[0])
        y = math.sqrt(r ** 2 - x ** 2)
        for n in motes:
            d = min(d, math.sqrt((x - n['x'])**2 + (y - n['y'])**2))
        if dmin < d < dmax:
            return {"id": mote_id, "type": mote_type, "x": float(x), "y": float(y), "z": 0}


# ******************************************* GET FUNCTIONS *******************************************
def generate_motes(n=NBR_MOTES):
    """
    This function generates a WSN with 1 root, n legitimate motes and 1 malicious mote

    :param n: the number of legitimate motes to be generated
    :return: the list of motes (formatted as dictionaries like hereafter)
    """
    motes = [{"id": 0, "type": "root", "x": 0, "y": 0, "z": 0}]
    malicious = None
    for i in range(n):
        # this is aimed to randomly add the malicious mote not far from the root
        if malicious is None and random.randint(1, n // (i + 1)) == 1:
            malicious = _generate_mote(motes, n + 1, "malicious")
            motes.append(malicious)
        # now generate a position for the current mote
        motes.append(_generate_mote(motes, i + 1, "sensor"))
    malicious = _generate_mote(motes, n + 1, "malicious") if not malicious else motes.pop(motes.index(malicious))
    motes.append(malicious)
    return motes


def get_constants(blocks):
    """
    This function retrieves the constants to the building blocks provided in input.

    :param blocks: input building blocks
    :return: corresponding constants
    """
    with open('./templates/building-blocks.json') as f:
        available_blocks = json.load(f)
    constants = {}
    for block in blocks:
        try:
            for constant, value in available_blocks[block].items():
                if constant in constants.keys():
                    logging.warning(" > Building-block '{}': '{}' is already set to {}".format(block, constant, value))
                else:
                    constants[constant] = value
        except KeyError:
            logging.error(" > Building-block '{}' does not exist !".format(block))
    return constants


def get_experiments(exp_file):
    """
    This function retrieves the dictionary of experiments with their parameters from a JSON campaign file.

    :param exp_file: input JSON simulation campaign file
    :return: dictionary with the parsed experiments and their parameters
    """
    exp_file = os.path.expanduser(exp_file)
    if not exp_file.endswith(".json"):
        exp_file += ".json"
    if not os.path.exists(exp_file):
        logging.critical("Simulation campaign JSON file does not exist !")
        exit(2)
    with open(exp_file) as f:
        experiments = json.load(f)
    return experiments


def get_path(*args):
    """
    This function joins input arguments to make a path and create it.

    :param args: intermediary subfolder names
    :return: path string
    """
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_available_platforms():
    """
    This function retrieves the list of available platforms from the Contiki directory.

    :return: List of strings representing the available platforms
    """
    platforms = []
    for item in os.listdir(os.path.join(CONTIKI_FOLDER, 'platform')):
        if os.path.isdir(os.path.join(CONTIKI_FOLDER, 'platform', item)):
            platforms.append(item)
    return platforms


def render_templates(path, base_templates, n, blocks, max_range, duration, title, goal, notes):
    """
    This function is aimed to adapt the input templates dictionary with provided parameters.

    :param path: experiment folder path
    :param templates: dictionary of the templates to be deployed
    :param n: number of motes
    :param blocks: build blocks to be included in the current experiment
    :param duration: duration of the simulation
    :param title: title of the simulation
    :param goal: goal description for the simulation
    :param notes: additional notes for the simulation
    """
    templates = copy.deepcopy(base_templates)
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = generate_motes(int(n or NBR_MOTES))
    # fill in the different templates
    templates["motes/malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) \
                                                             for c in get_constants(blocks).items()])
    templates["script.js"]["timeout"] = 1000 * int(duration or templates["script.js"]["timeout"])
    templates["script.js"]["sampling_period"] = templates["script.js"]["timeout"] // 100
    simulation_template = templates.pop("simulation.csc")
    simulation_template["title"] = title or simulation_template["title"]
    simulation_template["goal"] = goal or simulation_template["goal"]
    simulation_template["notes"] = notes or simulation_template["notes"]
    templates["simulation_with_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_with_malicious.csc"]["motes"] = motes
    templates["simulation_without_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_without_malicious.csc"]["motes"] = motes[:-1]
    del templates["simulation_without_malicious.csc"]["mote_types"][-1]  # remove malicious mote
    for template_name, kwargs in templates.items():
        logging.debug(" > Setting template file: {}".format(template_name))
        template = TEMPLATE_ENV.get_template(template_name).render(**kwargs)
        with open(os.path.join(path, template_name), "w") as f:
            f.write(template)


def validated_parameters(dictionary):
    """
    This function validates all parameters coming from a JSON dictionary parsed from the simulation
     campagin file.

    :param dictionary: input parameters
    :return: dictionary of validated parameters
    """
    params = {}
    simulation = dictionary.get("simulation") or {}
    malicious = dictionary.get("malicious") or {}
    # simulation parameters
    params["title"] = simulation.get("title") or ""
    params["goal"] = simulation.get("goal") or ""
    params["notes"] = simulation.get("notes") or ""
    params["duration"] = simulation.get("duration") or 300
    if not isinstance(params["duration"], int) or params["duration"] <= 0:
        logging.warning(" > Parameter [simulation -> duration] must be an integer strictly" \
                        " greater than 0 (set to default: 300)")
        params["duration"] = 300
    params["n"] = simulation.get("number-motes") or NBR_MOTES
    if params["n"] <= 0:
        logging.warning(" > Parameter [simulation -> number_motes] must be an integer strictly" \
                        " greater than 0 (set to default: 10)")
        params["n"] = NBR_MOTES
    params["target"] = simulation.get("target") or "z1"
    if params["target"] not in get_available_platforms():
        logging.error(" > Parameter [simulation -> target] '{}' platform does not exist !" \
                      " (set to default: z1)".format(params["target"]))
        params["target"] = "z1"
    # malicious mote parameters
    params["mtype"] = malicious.get("type") or "sensor"
    if params["mtype"] not in ["root", "sensor"]:
        logging.warning(" > Parameter [malicious -> type] must be 'root' or 'sensor'" \
                        " (set to default: 'sensor')")
        params["mtype"] = "sensor"
    params["max_range"] = malicious.get("maximum-range-from-root") or MAX_XY_POSITION[0]
    if not isinstance(params["max_range"], (int, float)) or params["max_range"] <= MIN_DIST_BETWEEN_MOTES or \
                    params["max_range"] > MAX_XY_POSITION[0]:
        logging.warning(" > Parameter [malicious -> maximum-range-from-root] must be strictly" \
                        " greater than {} and less or equal to {} (set to default: {})" \
                        .format(MIN_DIST_BETWEEN_MOTES, MAX_XY_POSITION[0], MAX_XY_POSITION[0]))
        params["max_range"] = MAX_XY_POSITION[0]
    params["blocks"] = malicious.get("building-blocks") or []
    if not isinstance(params["blocks"], (list, tuple)):
        logging.warning(" > Parameter [malicious -> building-blocks] must be a list (set to default: [])")
        params["blocks"] = []
    if len(params["blocks"]) > 0:
        with open('./templates/building-blocks.json') as f:
            blocks = json.load(f)
        temp_blocks = []
        for block in params["blocks"]:
            if block not in blocks:
                logging.warning(" > Parameter [malicious -> building-blocks] '{}' does not exist !" \
                                " (removed)".format(block))
            else:
                temp_blocks.append(block)
        params["blocks"] = temp_blocks
    params["ext_lib"] = malicious.get("external-library")
    if params["ext_lib"] and not os.path.exists(params["ext_lib"]):
        logging.warning(" > Parameter [malicious -> external-library] '{}' does not exist !" \
                        " (set to default: none)".format(params["ext_lib"]))
        params["ext_lib"] = None
    return params
