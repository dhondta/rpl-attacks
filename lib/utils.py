# -*- coding: utf8 -*-
from copy import deepcopy
from json import dump, loads
from math import sqrt
from os import listdir, makedirs, rename
from os.path import basename, dirname, exists, expanduser, isdir, isfile, join, split, splitext
from random import randint
from re import findall

from jinja2 import Environment, FileSystemLoader
from jsmin import jsmin
from numpy import average, cos, pi, sign, sin, sqrt
from numpy.random import randint
from six import string_types

from tmp.netgen import Network, NetworkGenerator
from .constants import CONTIKI_FILES, CONTIKI_FOLDER, DEFAULTS, EXPERIMENT_STRUCTURE, TEMPLATES, \
                       EXPERIMENT_FOLDER, TEMPLATES_FOLDER, WSN_DENSITY_FACTOR
from .helpers import remove_files, replace_in_file
from .logconfig import logger


# ************************************** NETWORK GENERATION FUNCTION ****************************************
def generate_motes(**kwargs):
    """
    This function generates a WSN with 1 root, n legitimate motes and 1 malicious mote

    :return: the list of motes (formatted as dictionaries like hereafter)
    """
    nodes = [{"id": 0, "type": "root", "x": 0, "y": 0, "z": 0}]
    n = kwargs.pop('n', DEFAULTS["number-motes"])
    min_range = kwargs.pop()
    max_range = kwargs.pop('area_side', DEFAULTS["area-square-side"])
    tx_range = kwargs.pop('tx_range', DEFAULTS["communication_range"])
    # determine 'i', the number of steps for the algorithm
    # at step i, the newtork must be filled with at most sum(f * 2 ** i)
    #   e.g. if f = 3, with 10 nodes, root's proximity will hold 6 nodes then the 4 ones remaining in the next ring
    i, s, nid = 1, 0, 1
    while s <= n:
        s += WSN_DENSITY_FACTOR * 2 ** i
        i += 1
    # now, generate the nodes
    # first, the range increment is defined ; it will provide the interval of ranges for the quadrants
    range_inc = min(tx_range, max_range / (i - 1))
    for ns in range(1, i):
        n_step = WSN_DENSITY_FACTOR * 2 ** ns
        # determine the angle increment for the quadrants
        angle_inc = 360 // min(n_step, n - nid)
        # then, divide the ring in quadrants and generate 1 node per quadrant with a 10% margin either
        #  for the angle or for the range
        range_min, range_max = int((ns - 0.8) * range_inc), int((ns - 0.2) * range_inc)
        for j in range(0, n_step):
            angle_min, angle_max = int((j + 0.2) * angle_inc), int((j + 0.8) * angle_inc)
            d, k = 0, 0
            while d < min_range and k < 1000:
                node_angle = randint(angle_min, angle_max) * pi / 180
                node_range = randint(max(range_min, min_range), min(range_max, max_range))
                # compute the coordinates and append the new node to the list
                x, y = node_range * cos(node_angle), node_range * sin(node_angle)
                for node in nodes:
                    d = min(d, sqrt((x - node['x'])**2 + (y - node['y'])**2))
                k += 1
            nodes.append({'id': nid, 'type': 'sensor', 'x': x, 'y': y, 'z': 0})
            if nid == n:
                break
            nid += 1
        range_inc *= 0.7
    # finally, add the malicious mote in the middle of the network
    x, y = 0, 0
    for i in range(0, 1):
        # get the average of the squared x and y deltas
        avg_x = average([sign(n['x'] - x) * (n['x'] - x) ** 2 for n in nodes])
        x = sign(avg_x) * sqrt(abs(avg_x))
        avg_y = average([sign(n['y'] - y) * (n['y'] - y) ** 2 for n in nodes])
        y = sign(avg_y) * sqrt(abs(avg_y))
    nodes.append({'id': len(nodes), 'type': 'malicious', 'x': x, 'y': y, 'z': 0})
    return nodes


# *********************************************** GET FUNCTIONS ************************************************
def generate_motes(**kwargs):
    """
    This function generates a WSN with 1 root, n legitimate motes and 1 malicious mote

    :return: the list of motes (formatted as dictionaries like hereafter)
    """
    n = kwargs.pop('n', DEFAULTS["number-motes"])
    max_from_root = kwargs.pop('max_from_root', DEFAULTS["maximum-range-from-root"])
    area_side = kwargs.pop('area_side', DEFAULTS["area-square-side"])
    comm_range = kwargs.pop('comm_range', DEFAULTS["communication_range"])
    # create the network with only the root
    net = Network((area_side, ) * 2)
    net.add_node(pos=(area_side // 2,)*2, comm_range=comm_range)
    # now, create the generator and generate the sensors
    gen = NetworkGenerator(n_count=n+1, connected=True, comm_range=comm_range, logger=logger,
                           method='homogeneous_network')  #neighborhood_network
    for i in range(n):
        net = gen.generate(net)
    net.savefig()
    exit(0)
    # then, add the malicious mote
    net.add_node(comm_range=comm_range)
    motes = []
    for node, pos in sorted(net.pos.items(), key=lambda x: x[0].id):
        motes.append({"id": node.id, "x": pos[0], "y": pos[1], "z": 0,
                      "type": "root" if node.id == 0 else ("malicious" if node.id == len(net.pos) - 1 else "sensor")})
    # motes = list({"id": 0, "type": "root", "x": 0, "y": 0, "z": 0})
    # for i in range(n):
    #     motes.append(_generate_mote(motes, i + 1, "sensor"))
    # motes.append(_generate_mote(motes, n + 1, "malicious", max_from_root))
    # net = gen.generate()
    # TODO:
    #  - reframe network on environment
    #  - center network on (0, 0)
    #  - retrieve motes
    return motes


def get_available_platforms():
    """
    This function retrieves the list of available platforms from the Contiki directory.

    :return: List of strings representing the available platforms
    """
    platforms = []
    for item in listdir(join(CONTIKI_FOLDER, 'platform')):
        if isdir(join(CONTIKI_FOLDER, 'platform', item)):
            platforms.append(item)
    return platforms


def get_building_blocks():
    """
    This function retrieves the list of available building blocks for the malicious mote.

    :return: List of strings representing the available building blocks
    """
    with open(join(TEMPLATES_FOLDER, 'building-blocks.json')) as f:
        blocks = loads(jsmin(f.read()))
    return blocks


def get_constants_and_replacements(blocks):
    """
    This function retrieves the constants and replacements corresponding to the building blocks provided in input.

    :param blocks: input building blocks
    :return: corresponding constants and replacements to be made in ContikiRPL files
    """
    available_blocks = get_building_blocks()
    constants, replacements = {}, {}
    for block in blocks:
        for key, value in available_blocks[block].items():
            # e.g. {"RPL_CONF_MIN_HOPRANKINC": 128} will be collected in constants
            if key.upper() == key and not (key.endswith('.c') or key.endswith('.h')):
                if key in constants.keys():
                    logger.warning(" > Building-block '{}': '{}' is already set to {}".format(block, key, value))
                else:
                    constants[key] = value
            # else, it is a replacement in a file, e.g. {"rpl-icmp6.c": ["dag->version", "dag->version++"]}
            else:
                if key in replacements.keys() and value[0] in [srcl for srcl, dstl in replacements.values()]:
                    logger.warning(" > Building-block '{}': line '{}' is already replaced in {}"
                                   .format(block, value[0], key))
                else:
                    replacements[key] = value
    return constants, replacements


def get_contiki_includes(target):
    """
    This function is aimed to compute the list of includes from the contiki folder based on a given list
     (CONTIKI_FILES) and the current target by parsing its (potentially existing) Makefile's.

    :param target: the mote's platform to be used for compilation
    :return: the list of includes from Contiki for the specified target
    """
    files = [f.format(target) if 'platform' in f else f for f in CONTIKI_FILES]
    includes = [x for x in set(files) if not x.startswith('-')]
    excludes = [x[1:] for x in list(set(files) - set(includes))]
    matches = {'cpu': [], 'dev': []}
    for makefile in ['Makefile.{}'.format(target), 'Makefile.common']:
        try:
            with open(join(CONTIKI_FOLDER, 'platform', target, makefile)) as f:
                for line in f.readlines():
                    for item in matches.keys():
                        if item in line:
                            matches[item].extend(findall(item + r'\/([a-zA-Z0-9]+)(?:\s+|\/)', line))
        except IOError:
            pass
    for item in matches.keys():
        if len(matches[item]) == 0:
            includes = [f.format('').rstrip('/') if item in f else f for f in includes]
        else:
            includes = [f for f in includes if item not in f]
            for match in set(matches[item]):
                includes.append(join(item, match))
    folders = {}
    for exclude in excludes:
        folder, fn = split(exclude)
        folders.setdefault(folder, [])
        folders[folder].append(fn)
    for folder, excluded_files in folders.items():
        if folder not in includes:
            continue
        includes.remove(folder)
        for item in listdir(join(CONTIKI_FOLDER, folder)):
            if item not in excluded_files:
                includes.append(join(folder, item))
    return includes


def get_experiments(exp_file):
    """
    This function retrieves the dictionary of experiments with their parameters from a JSON campaign file.

    :param exp_file: input JSON simulation campaign file
    :return: dictionary with the parsed experiments and their parameters
    """
    if dirname(exp_file) == '':
        exp_file = join(EXPERIMENT_FOLDER, exp_file)
    exp_file = expanduser(exp_file)
    if not exp_file.endswith(".json"):
        exp_file += ".json"
    if not exists(exp_file):
        logger.critical("Simulation campaign JSON file does not exist !")
        logger.warning("Make sure you've generated a JSON simulation campaign file by using 'prepare' fabric command.")
        return
    with open(exp_file) as f:
        experiments = loads(jsmin(f.read()))
    return experiments


def get_parameter(dictionary, section, key, condition, reason=None, default=None):
    """
    This function checks and returns a validated value for the given parameter.

    :param dictionary: dictionary of parameters
    :param section: section in the dictionary
    :param key: key of the related parameter
    :param condition: validation condition
    :param reason: message to be displayed in case of test failure
    :param default: default value to be used in last resort
    :return: validated parameter
    """
    silent = dictionary.pop('silent', False)
    param = (dictionary.get(section) or {}).get(key) or DEFAULTS.get(key)
    if param is None and default is not None:
        param = default
    if isinstance(condition, list) and isinstance(param, list):
        buffer = []
        for p in param:
            if not condition[0](p):
                if not silent:
                    logger.warning("Parameter [{} -> {}] '{}' does not exist (removed)"
                                   .format(section, key, p))
            else:
                buffer.append(p)
        return buffer
    else:
        if not condition(param):
            if not silent:
                logger.warning("Parameter [{} -> {}] {} (set to default: {})"
                               .format(section, key, reason, DEFAULTS[key]))
            param = DEFAULTS[key]
        return param


def get_path(*args, **kwargs):
    """
    This function joins input arguments to make a path and create it.

    :param args: intermediary subfolder names
    :return: path string
    """
    create = kwargs.get('create')
    path = join(*args)
    if create and not exists(path):
        makedirs(path)
    return path


# *********************************************** LIST FUNCTIONS ***********************************************
def list_campaigns():
    """
    This function gets the list of existing simulation campaign JSON files.

    :return: list of JSON files
    """
    return sorted([basename(f) for f in listdir(EXPERIMENT_FOLDER) \
                   if isfile(join(EXPERIMENT_FOLDER, f)) and f.endswith('.json') and \
                   is_valid_campaign(join(EXPERIMENT_FOLDER, f))])


def list_experiments():
    """
    This function gets the list of existing experiments.

    :return: list of experiments
    """
    return sorted([d for d in listdir(EXPERIMENT_FOLDER) \
                   if isdir(join(EXPERIMENT_FOLDER, d)) and not d.startswith('.') and \
                   check_structure(join(EXPERIMENT_FOLDER, d))])


# ************************************** TEMPLATE AND PARAMETER FUNCTIONS **************************************
def apply_replacements(contiki_rpl, replacements):
    """
    This function replaces lines in specified ContikiRPL files. Each replacement is formatted as follows:
        {"ContikiRPL_filename": ["source_line", "destination_line"]}

    :param replacements: dictionary of replacement entries
    """
    for filename, replacement in replacements.items():
        replace_in_file(join(contiki_rpl, filename), replacement)


def check_structure(path, files=None, remove=False):
    """
    This function checks if the file structure given by the dictionary files exists at the input path.

    :param path: path to be checked for the file structure
    :param files: file structure as a dictionary
    :param remove: if this flag is True, non-matching files are removed
    :return: True if the file structure is respected, otherwise False
    """
    files = deepcopy(EXPERIMENT_STRUCTURE) if files is None else files
    for item in listdir(path):
        wildcard = '{}.*'.format(splitext(item)[0])
        match = item if item in files.keys() else (wildcard if wildcard in files.keys() else None)
        if match is None:
            if remove:
                remove_files(path, item)
            continue
        files[match] = True if isinstance(files[match], bool) else \
            check_structure(join(path, match), deepcopy(files[match]), remove)
    return all(files.values())


def is_valid_campaign(path):
    """
    This function checks if the given JSON file is a valid campaign file.

    :param path: JSON file to be checked
    :return: True if valid file, otherwise False
    """
    try:
        # TODO: check JSON file structure
        with open(path) as f:
            loads(jsmin(f.read()))
        return True
    except ValueError:
        return False


def render_campaign(exp_file):
    """
    This function is aimed to render a campaign JSON file with the list of available building blocks for
     helping the user to tune its experiments.

    :param exp_file: path to the experiment file to be created
    """
    path = dirname(exp_file)
    write_template(path, Environment(loader=FileSystemLoader(TEMPLATES_FOLDER)), 'experiments.json',
                   available_building_blocks='\n'.join([' - {}'.format(b) for b in get_building_blocks()]))
    rename(join(path, 'experiments.json'), exp_file)


def render_templates(path, only_malicious=False, **params):
    """
    This function is aimed to adapt and render the base templates dictionary with provided parameters.

    :param path: experiment folder path
    :param only_malicious: flag to indicate if all the templates have to be deployed or only malicious's one
    :param params: dictionary with all the parameters for the experiment
    :return: eventual replacements to be made in ContikiRPL files
    """
    templates = deepcopy(TEMPLATES)
    env = Environment(loader=FileSystemLoader(join(path, 'templates')))
    # fill in the different templates with input parameters
    constants, replacements = get_constants_and_replacements(params["blocks"])
    templates["motes/malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) \
        for c in constants.items()])
    if only_malicious:
        template_malicious = "motes/malicious.c"
        write_template(path, env, template_malicious, **templates[template_malicious])
        return
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = params['motes'] or generate_motes(**params)
    # fill in and render malicious mote template directly in the simulation with malicious mote
    write_template(join(path, 'with-malicious'), env, "motes/malicious.c", **templates.pop("motes/malicious.c"))
    # fill in and render templates shared by both simulations
    shared_templates = dict()
    shared_templates["Makefile"] = templates.pop("Makefile")
    shared_templates["Makefile"]["target"] = params["target"]
    shared_templates["motes/root.c"] = templates.pop("motes/root.c")
    shared_templates["motes/sensor.c"] = templates.pop("motes/sensor.c")
    for name, kwargs in shared_templates.items():
        write_template(path, env, name, **kwargs)
    # fill in simulation file templates
    templates["script.js"]["timeout"] = 1000 * params["duration"]
    templates["script.js"]["sampling_period"] = templates["script.js"]["timeout"] // 100
    templates["simulation.csc"]["title"] = params["title"] + ' (with the malicious mote)'
    templates["simulation.csc"]["goal"] = params["goal"]
    templates["simulation.csc"]["notes"] = params["notes"]
    templates["simulation.csc"]["interference_range"] = params["int_range"]
    templates["simulation.csc"]["transmitting_range"] = params["tx_range"]
    templates["simulation.csc"]["target"] = params["target"]
    templates["simulation.csc"]["target_capitalized"] = params["target"].capitalize()
    templates["simulation.csc"]["malicious_target"] = params["malicious_target"]
    templates["simulation.csc"]["malicious_target_capitalized"] = params["malicious_target"].capitalize()
    for mote_type in templates["simulation.csc"]["mote_types"]:
        mote_type["target"] = params["target"] if mote_type["name"] != "malicious" else params["malicious_target"]
    # render the templates for the simulation with the malicious mote
    for name, kwargs in templates.items():
        write_template(join(path, 'with-malicious'), env, name, **kwargs)
    with open(join(path, 'with-malicious', 'data', 'motes.json'), 'w') as f:
        dump({m['id']: (m['x'], m['y']) for m in motes}, f, sort_keys=True, indent=4)
    # now, adapt the title, remove the malicious mote from the list and from the mote types
    templates["simulation.csc"]["title"] = params["title"] + ' (without the malicious mote)'
    templates["simulation.csc"]["motes"] = motes[:-1]
    del templates["simulation.csc"]["mote_types"][-1]
    # render the templates for the simulation with the malicious mote
    for name, kwargs in templates.items():
        write_template(join(path, 'without-malicious'), env, name, **kwargs)
    with open(join(path, 'without-malicious', 'data', 'motes.json'), 'w') as f:
        dump({m['id']: (m['x'], m['y']) for m in motes[:-1]}, f, sort_keys=True, indent=4)
    return replacements


def write_template(path, env, name, **kwargs):
    """
    This function fills in a template and copy it to its destination.

    :param path: folder where the template is to be copied
    :param env: template environment
    :param name: template's key in the templates dictionary
    :param kwargs: parameters associated to this template
    """
    logger.debug(" > Setting template file: {}".format(name))
    template = env.get_template(name).render(**kwargs)
    with open(join(path, name), "w") as f:
        f.write(template)


def validated_parameters(dictionary, silent=False):
    """
    This function validates all parameters coming from a JSON dictionary parsed from the simulation
     campagin file.

    :param dictionary: input parameters
    :return: dictionary of validated parameters
    """
    params = dict(motes=dictionary.get('motes'))
    # simulation parameters
    params["title"] = get_parameter(dictionary, "simulation", "title",
        lambda x: isinstance(x, string_types), "is not a string")
    params["goal"] = get_parameter(dictionary, "simulation", "goal",
        lambda x: isinstance(x, string_types), "is not a string")
    params["notes"] = get_parameter(dictionary, "simulation", "notes",
        lambda x: isinstance(x, string_types), "is not a string")
    params["duration"] = get_parameter(dictionary, "simulation", "duration",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["n"] = get_parameter(dictionary, "simulation", "number-motes",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["repeat"] = get_parameter(dictionary, "simulation", "repeat",
        lambda x: isinstance(x, int) and x > 0, "is not an integer greater than 0")
    params["target"] = get_parameter(dictionary, "simulation", "target",
        lambda x: x in get_available_platforms(), "is not a valid platform")
    params["malicious_target"] = get_parameter(dictionary, "malicious", "target",
        lambda x: x in get_available_platforms(), "is not a valid platform", default=params["target"])
    params["mtype"] = get_parameter(dictionary, "malicious", "type",
        lambda x: x in ["root", "sensor"], "is not 'root' or 'sensor'")
    params["blocks"] = get_parameter(dictionary, "malicious", "building-blocks",
        [lambda x: x in get_building_blocks()])
    params["ext_lib"] = get_parameter(dictionary, "malicious", "external-library",
        lambda x: x is None or exists(x), "does not exist")
    # area dimensions and limits
    params["tx_range"] = get_parameter(dictionary, "simulation", "transmission-range",
        lambda x: isinstance(x, (int, float)) and x > params["dmin"],
        "is not an integer greater than {}".format(params["dmin"]))
    params["int_range"] = get_parameter(dictionary, "simulation", "interference-range",
        lambda x: isinstance(x, (int, float)) and x >= params["tx_range"],
        "is not an integer greater than or equal to {}".format(params["tx_range"]), default=2*params["tx_range"])
    params["area_side"] = get_parameter(dictionary, "simulation", "area-square-side",
        lambda x: isinstance(x, (int, float)) and x >= sqrt(2.0) * params["dmin"],
        "is not an integer or a float greater or equal to sqrt(2)*{:.0f}".format(params["dmin"]))
    params["min_range"] = get_parameter(dictionary, "simulation", "minimum-distance-between-motes",
        lambda x: isinstance(x, (int, float)) and x > 0, "is not an integer greater than 0")
    params["max_range"] = get_parameter(dictionary, "simulation", "maximum-range-from-root",
        lambda x: isinstance(x, (int, float)) and params["dmin"] <= x <= params["area-side"],
        "is not an integer or a float between {:.0f} and {:.0f}".format(params["dmin"], params["area_side"]))
    return params
