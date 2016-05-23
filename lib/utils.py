# -*- coding: utf8 -*-
import copy
import json
import logging
import math
import os
import random

from .constants import CONTIKI_FOLDER, DEFAULTS, EXPERIMENT_FOLDER, TEMPLATES_FOLDER, TEMPLATE_ENV, TEMPLATES


# **************************************** PROTECTED FUNCTIONS ****************************************
def _generate_mote(motes, mote_id, mote_type,
                   max_x=DEFAULTS["area-square-side"]//2,
                   dmin=DEFAULTS["minimum-distance-between-motes"],
                   dmax=DEFAULTS["maximum-distance-between-motes"] * 0.9,
                   max_from_root=None):
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
        d = float("Inf")
        x = random.randint(-max_x, max_x)
        r = random.randint(abs(x), max_x)
        y = random.choice([-1, 1]) * math.sqrt(r ** 2 - x ** 2)
        for n in motes:
            d = min(d, math.sqrt((x - n['x'])**2 + (y - n['y'])**2))
        if (dmin < d < dmax and max_from_root is not None and d <= max_from_root) or \
                (dmin < d < dmax and max_from_root is None):
            return {"id": mote_id, "type": mote_type, "x": float(x), "y": float(y), "z": 0}


# ******************************************* GET FUNCTIONS *******************************************
def generate_motes(n=DEFAULTS["number-motes"], max_from_root=DEFAULTS["maximum-range-from-root"]):
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
            malicious = _generate_mote(motes, n + 1, "malicious", max_from_root)
            motes.append(malicious)
        # now generate a position for the current mote
        motes.append(_generate_mote(motes, i + 1, "sensor"))
    malicious = _generate_mote(motes, n + 1, "malicious", max_from_root) \
        if not malicious else motes.pop(motes.index(malicious))
    motes.append(malicious)
    return motes


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


def get_building_blocks():
    """
    This function retrieves the list of available building blocks for the malicious mote.

    :return: List of strings representing the available building blocks
    """
    with open(os.path.join(TEMPLATES_FOLDER, 'building-blocks.json')) as f:
        blocks = json.load(f)
    logging.error(blocks.keys())
    print(blocks)
    return blocks.keys()


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
    if os.path.dirname(exp_file) == '':
        exp_file = os.path.join(EXPERIMENT_FOLDER, exp_file)
    exp_file = os.path.expanduser(exp_file)
    if not exp_file.endswith(".json"):
        exp_file += ".json"
    if not os.path.exists(exp_file):
        logging.critical("Simulation campaign JSON file does not exist !")
        logging.warning("Make sure you've generated a JSON simulation campaign file by using 'prepare' fabric command.")
        exit(2)
    with open(exp_file) as f:
        experiments = json.load(f)
    return experiments


def get_parameter(dictionary, section, key, condition, reason=None):
    """
    This function checks and returns a validated value for the given parameter.

    :param dictionary: dictionary of parameters
    :param section: section in the dictionary
    :param key: key of the related parameter
    :param condition: validation condition
    :param message: message to be displayed in case of test failure
    :return: validated parameter
    """
    param = (dictionary.get(section) or {}).get(key) or DEFAULTS.get(key)
    if isinstance(condition, list) and isinstance(param, list):
        buffer = []
        for p in param:
            if not condition[0](p):
                logging.warning("Parameter [{} -> {}] '{}' does not exist (removed)".format(section, key, p))
            else:
                buffer.append(p)
        return buffer
    else:
        if not condition(param):
            print(param)
            logging.warning("Parameter [{} -> {}] {} (set to default: {})".format(section, key, reason, DEFAULTS[key]))
            param = DEFAULTS[key]
        return param


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


# ************************************** TEMPLATE AND PARAMETER FUNCTIONS **************************************
def render_templates(path, **params):
    """
    This function is aimed to adapt and render the base templates dictionary with provided parameters.

    :param path: experiment folder path
    :param templates: dictionary of the templates to be deployed
    :param n: number of motes
    :param blocks: build blocks to be included in the current experiment
    :param duration: duration of the simulation
    :param title: title of the simulation
    :param goal: goal description for the simulation
    :param notes: additional notes for the simulation
    """
    templates = copy.deepcopy(TEMPLATES)
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = generate_motes(params["n"])
    # fill in the different templates with input parameters
    templates["motes/malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) \
        for c in get_constants(params["blocks"]).items()])
    templates["script.js"]["timeout"] = 1000 * params["duration"]
    templates["script.js"]["sampling_period"] = templates["script.js"]["timeout"] // 100
    simulation_template = templates.pop("simulation.csc")
    simulation_template["title"] = params["title"]
    simulation_template["goal"] = params["goal"]
    simulation_template["notes"] = params["notes"]
    simulation_template["interference_range"] = params["int_range"]
    simulation_template["transmitting_range"] = params["tx_range"]
    simulation_template["target"] = params["target"]
    simulation_template["target_capitalized"] = params["target"].capitalize()
    templates["simulation_with_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_with_malicious.csc"]["motes"] = motes
    templates["simulation_without_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_without_malicious.csc"]["motes"] = motes[:-1]
    del templates["simulation_without_malicious.csc"]["mote_types"][-1]  # remove malicious mote
    # render the list of templates
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
    # simulation parameters
    params["title"] = get_parameter(dictionary, "simulation", "title",
        lambda x: isinstance(x, str), "is not a string")
    params["goal"] = get_parameter(dictionary, "simulation", "goal",
        lambda x: isinstance(x, str), "is not a string")
    params["notes"] = get_parameter(dictionary, "simulation", "notes",
        lambda x: isinstance(x, str), "is not a string")
    params["duration"] = get_parameter(dictionary, "simulation", "duration",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["n"] = get_parameter(dictionary, "simulation", "number-motes",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["repeat"] = get_parameter(dictionary, "simulation", "repeat",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["target"] = get_parameter(dictionary, "simulation", "target",
        lambda x: x in get_available_platforms(), "is not a valid platform")
    params["mtype"] = get_parameter(dictionary, "malicious", "type",
        lambda x: x in ["root", "sensor"], "is not 'root' or 'sensor'")
    params["blocks"] = get_parameter(dictionary, "malicious", "building-blocks",
        [lambda x: x in get_available_platforms()])
    params["ext_lib"] = get_parameter(dictionary, "malicious", "external-library",
        lambda x: x is None or os.path.exists(x), "does not exist")
    # area dimensions and limits
    params["dmin"] = get_parameter(dictionary, "simulation", "minimum-distance-between-motes",
        lambda x: isinstance(x, (int, float)) and x > 0, "is not an integer greater than 0")
    params["tx_range"] = get_parameter(dictionary, "simulation", "transmitting_range",
        lambda x: isinstance(x, (int, float)) and x > params["dmin"],
        "is not an integer greater than {}".format(params["dmin"]))
    params["int_range"] = get_parameter(dictionary, "simulation", "interference_range",
        lambda x: isinstance(x, (int, float)) and x >= params["tx_range"],
        "is not an integer greater than or equal to {}".format(params["tx_range"]))
    params["dmax"] = get_parameter(dictionary, "simulation", "maximum-distance-between-motes",
        lambda x: isinstance(x, (int, float)) and params["dmin"] < x <= params["tx_range"],
        "is not an integer between {:.0f} and {:.0f}".format(params["dmin"], params["tx_range"]))
    params["area_side"] = get_parameter(dictionary, "simulation", "area-square-side",
        lambda x: isinstance(x, (int, float)) and x >= math.sqrt(2.0) * params["dmin"],
        "is not an integer or a float greater or equal to sqrt(2)*{:.0f}".format(params["dmin"]))
    params["max_range"] = get_parameter(dictionary, "malicious", "maximum-range-from-root",
        lambda x: isinstance(x, (int, float)) and params["dmin"] <= x <= params["area_side"],
        "is not an integer or a float between {:.0f} and {:.0f}".format(params["dmin"], params["area_side"]))
    return params
