# -*- coding: utf8 -*-
from copy import deepcopy
from jinja2 import Environment, FileSystemLoader
from math import sqrt
from os import listdir, makedirs, rename
from os.path import basename, dirname, exists, expanduser, isdir, isfile, join, split, splitext
from re import findall, finditer, search, sub, DOTALL, MULTILINE
from six import string_types

from core.common.helpers import *
from core.common.wsngenerator import *
from core.conf.constants import *
from core.conf.logconfig import logger


__all__ = [
    'apply_debug_flags',
    'apply_replacements',
    'check_structure',
    'get_motes_from_simulation',
    'set_motes_to_simulation',
    'get_contiki_includes',
    'get_experiments',
    'get_path',
    'list_campaigns',
    'list_experiments',
    'list_wsn_gen_algorithms',
    'render_campaign',
    'render_templates',
    'validated_parameters',
]


# *********************************************** GET FUNCTIONS ************************************************
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
    return is_valid_commented_json(join(TEMPLATES_FOLDER, 'building-blocks.json'),
                                   return_json=True, logger=logger) or {}


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


def get_contiki_includes(target, malicious_target=None):
    """
    This function is aimed to compute the list of includes from the contiki folder based on a given list
     (CONTIKI_FILES) and the current target by parsing its (potentially existing) Makefile's.

    :param target: the mote's platform to be used for compilation
    :param malicious_target: the malicious mote's platform to be used for compilation
    :return: the list of includes from Contiki for the specified target
    """
    files = [f.format(target) if f.startswith('platform') else f for f in CONTIKI_FILES]
    targets = [target]
    if malicious_target is not None and malicious_target != target:
        files += [f.format(malicious_target) if 'platform' in f else f for f in CONTIKI_FILES]
        targets += [malicious_target]
    # separate includes and excludes based on the heading '-'
    includes = [x for x in set(files) if not x.startswith('-')]
    excludes = [x[1:] for x in list(set(files) - set(includes))]
    # collect the cpu's and dev's to be included based on the target(s) to be used
    matches = {'cpu': [], 'dev': []}
    for target in targets:
        # search for cpu's and dev's in Makefile's for the selected target(s)
        for makefile in ['Makefile.{}'.format(target), 'Makefile.common']:
            try:
                with open(join(CONTIKI_FOLDER, 'platform', target, makefile)) as f:
                    for line in f.readlines():
                        for item in matches.keys():
                            if item in line:
                                matches[item].extend(findall(item + r'/([a-zA-Z0-9]+)(?:\s+|/)', line))
            except IOError:
                pass
    # then, for the cpu's and dev's matched, add these to the includes
    for item in matches.keys():
        if len(matches[item]) == 0:
            includes = [f.format('').rstrip('/') if item in f else f for f in includes]
        else:
            includes = [f for f in includes if item not in f]
            for match in set(matches[item]):
                if exists(join(CONTIKI_FOLDER, item, match)):
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


def get_experiments(exp_file, silent=False):
    """
    This function retrieves the dictionary of experiments with their parameters from a JSON campaign file.

    :param exp_file: input JSON simulation campaign file
    :param silent: specify whether an eventual error is to be raised or not
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
    return is_valid_commented_json(exp_file, return_json=True, logger=logger if not silent else None) or {}


def get_motes_from_simulation(simfile, as_dictionary=True):
    """
    This function retrieves motes data from a simulation file (.csc).

    :param simfile: path to the simulation file
    :param as_dictionary: flag to indicate that the output has to be formatted as a dictionary
    :return: the list of motes formatted as dictionaries with 'id', 'x', 'y' and 'motetype_identifier' keys if
              short is False or a dictionary with each mote id as the key and its tuple (x, y) as the value
    """
    motes = []
    with open(simfile) as f:
        content = f.read()
    iterables, fields = [], ['mote_id']
    for it in ['id', 'x', 'y', 'motetype_identifier']:
        iterables.append(finditer(r'^\s*<{0}>(?P<{0}>.*)</{0}>\s*$'.format(it), content, MULTILINE))
    for matches in zip(*iterables):
        mote = {}
        for m in matches:
            mote.update(m.groupdict())
        motes.append(mote)
    if as_dictionary:
        motes = {int(m['id']): (float(m['x']), float(m['y'])) for m in motes}
    return motes


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
    path = expanduser(join(*args))
    if create and not exists(path):
        makedirs(path)
    return path


# *********************************************** LIST FUNCTIONS ***********************************************
def list_campaigns():
    """
    This function gets the list of existing simulation campaign JSON files.

    :return: list of JSON files
    """
    return sorted([basename(f) for f in listdir(EXPERIMENT_FOLDER)
                   if isfile(join(EXPERIMENT_FOLDER, f)) and f.endswith('.json') and
                   is_valid_commented_json(join(EXPERIMENT_FOLDER, f))])


def list_experiments(check=True):
    """
    This function gets the list of existing experiments.

    :return: list of experiments
    """
    return sorted([d for d in listdir(EXPERIMENT_FOLDER)
                   if isdir(join(EXPERIMENT_FOLDER, d)) and not d.startswith('.') and (not check or
                   check_structure(join(EXPERIMENT_FOLDER, d)))])


def list_mote_types(mote_type, strip=True):
    """
    This function gets the list of existing non-malicious mote types.

    :return: list of non-malicious mote types
    """
    return sorted([basename(f).replace('.c', '').replace(mote_type + '-', '') if strip else basename(f)
                   for f in listdir(join(TEMPLATES_FOLDER, 'experiment', 'motes'))
                   if f.endswith('.c') and f.startswith(mote_type)])


def list_wsn_gen_algorithms():
    """
    This function gets all WSN generation functions from the WSN generation library.
    """
    from core.common.wsngenerator import __all__
    return __all__


# ************************************** TEMPLATE AND PARAMETER FUNCTIONS **************************************
def apply_debug_flags(contiki_rpl, debug='NONE'):
    """
    This function replaces debug flags in ContikiRPL files.

    :param contiki_rpl: path to ContikiRPL custom library
    :param debug: the new value to be set for the debug flag
    """
    for filename in DEBUG_FILES:
        replace_in_file(join(contiki_rpl, filename), (r'^#define DEBUG DEBUG_([A-Z]+)$', debug))


def apply_replacements(contiki_rpl, replacements):
    """
    This function replaces lines in specified ContikiRPL files. Each replacement is formatted as follows:
        {"ContikiRPL_filename": ["source_line", "destination_line"]}

    :param contiki_rpl: path to ContikiRPL custom library
    :param replacements: dictionary of replacement entries
    """
    for filename, replacement in replacements.items():
        replace_in_file(join(contiki_rpl, filename), replacement, logger=logger)


def check_structure(path, files=None, create=False, remove=False):
    """
    This function checks if the file structure given by the dictionary files exists at the input path.

    :param path: path to be checked for the file structure
    :param files: file structure as a dictionary
    :param create: create subfolders if they do not exist
    :param remove: if this flag is True, non-matching files are removed
    :return: True if the file structure is respected, otherwise False
    """
    if create and not exists(path):
        makedirs(path)
    files = deepcopy(EXPERIMENT_STRUCTURE) if files is None else files
    if files.get('*'):
        return True
    items = listdir(path)
    if create:
        items = [i for i, f in files.items() if not isinstance(f, bool)] + items
    for item in items:
        wildcard = '{}.*'.format(splitext(item)[0])
        match = item if item in files.keys() else (wildcard if wildcard in files.keys() else None)
        if match is None:
            if remove:
                remove_files(path, item)
            continue
        files[match] = True if isinstance(files[match], bool) else \
            check_structure(join(path, match), deepcopy(files[match]), create, remove)
    return all(files.values())


def render_campaign(exp_file):
    """
    This function is aimed to render a campaign JSON file with the list of available building blocks for
     helping the user to tune its experiments.

    :param exp_file: path to the experiment file to be created
    """
    def list_of(t, a=None):
        return [' - {}'.format(m) + ['', ' [default]'][m == DEFAULTS[a or t]] for m in list_mote_types(t)]

    path = dirname(exp_file)
    write_template(path, Environment(loader=FileSystemLoader(TEMPLATES_FOLDER)), 'experiments.json',
                   available_building_blocks='\n'.join([' - {}'.format(b) for b in get_building_blocks()]),
                   available_root_mote_types='\n'.join(list_of('root')),
                   available_sensor_mote_types='\n'.join(list_of('sensor')),
                   available_malicious_mote_types='\n'.join(list_of('malicious', 'type')),
                   area_side=DEFAULTS["area-square-side"], tx_range=DEFAULTS["transmission-range"])
    rename(join(path, 'experiments.json'), exp_file)


def render_templates(path, only_malicious=False, **params):
    """
    This function is aimed to adapt and render the base templates dictionary with provided parameters.

    :param path: experiment folder path
    :param only_malicious: flag to indicate if all the templates have to be deployed or only malicious' one
    :param params: dictionary with all the parameters for the experiment
    :return: eventual replacements to be made in ContikiRPL files
    """
    templates = deepcopy(TEMPLATES)
    env = Environment(loader=FileSystemLoader(join(path, 'templates')))
    # fill in the different templates with input parameters
    constants, replacements = get_constants_and_replacements(params["blocks"])
    templates["motes/malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) for c in constants.items()])
    if only_malicious:
        template_malicious = "motes/malicious.c"
        write_template(join(path, "with-malicious"), env, template_malicious, **templates[template_malicious])
        return replacements
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = params['motes']
    if motes is None:
        # strictly check for WSN generation function (for avoiding code injection in 'eval')
        from core.common.wsngenerator import __all__ as wsn_algos
        wsn_algo = params["wsn_gen_algo"]
        if wsn_algo in wsn_algos:
            motes = eval(wsn_algo)(defaults=DEFAULTS, **params)
        else:
            logger.error("Bad list of motes")
            return
    # fill in simulation file templates
    templates["report.md"] = deepcopy(params)
    templates["motes/Makefile"]["target"] = params["target"]
    # important note: timeout is milliseconds in the simulation script
    templates["script.js"]["timeout"] = 1000 * params["duration"]
    # important note: sampling period is relative to the measured time in the simulation, which is in microseconds ;
    #                  the '10 * ' thus means that we take 100 measures regardless the duration of the simulation
    templates["script.js"]["sampling_period"] = templates["script.js"]["timeout"] * 10
    templates["simulation.csc"]["title"] = params["title"] + ' (with the malicious mote)'
    templates["simulation.csc"]["goal"] = params["goal"]
    templates["simulation.csc"]["notes"] = params["notes"]
    templates["simulation.csc"]["interference_range"] = params["int_range"]
    templates["simulation.csc"]["transmitting_range"] = params["tx_range"]
    templates["simulation.csc"]["target"] = params["target"]
    templates["simulation.csc"]["target_capitalized"] = params["target"].capitalize()
    templates["simulation.csc"]["malicious_target"] = params["malicious_target"]
    templates["simulation.csc"]["malicious_target_capitalized"] = params["malicious_target"].capitalize()
    templates["simulation.csc"]["motes"] = motes
    for mote_type in templates["simulation.csc"]["mote_types"]:
        mote_type["target"] = params["target"] if mote_type["name"] != "malicious" else params["malicious_target"]
    # render the templates for the simulation with the malicious mote
    for name, kwargs in templates.items():
        write_template(join(path, 'with-malicious'), env, name, **kwargs)
    # now, adapt the title and mote source template
    del templates["motes/Makefile"]
    del templates["motes/root.c"]
    del templates["motes/sensor.c"]
    del templates["motes/malicious.c"]
    templates["simulation.csc"]["title"] = params["title"] + ' (without the malicious mote)'
    templates["simulation.csc"]["motes"] = motes[:-1]
    del templates["simulation.csc"]["mote_types"][-1]
    # render the templates for the simulation without the malicious mote
    for name, kwargs in templates.items():
        write_template(join(path, 'without-malicious'), env, name, **kwargs)
    return replacements


def set_motes_to_simulation(simfile, motes):
    """
    This function replaces motes data from a list of motes (formatted as dictionaries with 'id', 'x', 'y' and
     'motetype_identifier' keys) into a simulation file (.csc).

    :param simfile: path to the simulation file
    :param motes: list or dictionary of motes
    """
    if isinstance(motes, list):
        motes = {int(m['id']): (float(m['x']), float(m['y'])) for m in motes}
    tmp = simfile + '.tmp'
    with open(simfile) as of:
        content = of.read()
    for m in finditer(r'^\s*<mote>(?P<block>.*?)</mote>\s*$', content, DOTALL | MULTILINE):
        block = m.groups('block')[0]
        idmatch = search(r'^\s*<id>(?P<mote_id>\d+?)</id>\s*$', block, MULTILINE)
        if idmatch is None:
            continue
        mote_id = int(idmatch.groups('mote_id')[0])
        # e.g. occurs when modifying the simulation without malicious and the simulation with malicious has to be
        #  update ; id of malicious mote is found in the simulation file but not in the dictionary of motes
        if mote_id not in motes.keys():
            continue
        mote_pos = motes[mote_id]
        block = sub(r'<x>(.*?)</x>', '<x>{}</x>'.format(mote_pos[0]), block, flags=MULTILINE)
        block = sub(r'<y>(.*?)</y>', '<y>{}</y>'.format(mote_pos[1]), block, flags=MULTILINE)
        content = content.replace(m.groups('block')[0], block)
    with open(tmp, 'w+') as nf:
        nf.write(content)
    move_files('', '', (tmp, simfile))


def validated_parameters(dictionary):
    """
    This function validates all parameters coming from a JSON dictionary parsed from the simulation
     campaign file.

    :param dictionary: input parameters
    :return: dictionary of validated parameters
    """
    params = dict(motes=dictionary.get('motes'), campaign=dictionary.get('campaign'))
    # simulation parameters
    params["debug"] = get_parameter(dictionary, "simulation", "debug",
                                    lambda x: isinstance(x, bool), "is not a boolean")
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
                                               lambda x: x in get_available_platforms(), "is not a valid platform",
                                               default=params["target"])
    params["mtype_root"] = "root-{}".format(get_parameter(dictionary, "simulation", "root",
                                            lambda x: x in list_mote_types("root"),
                                            "is not an available root mote type"))
    params["mtype_sensor"] = "sensor-{}".format(get_parameter(dictionary, "simulation", "sensor",
                                                lambda x: x in list_mote_types("sensor"),
                                                "is not an available sensor mote type"))
    params["mtype_malicious"] = "malicious-{}".format(get_parameter(dictionary, "malicious", "type",
                                                      lambda x: x in list_mote_types("malicious"),
                                                      "is not an available malicious mote type"))
    params["blocks"] = get_parameter(dictionary, "malicious", "building-blocks",
                                     [lambda x: x in get_building_blocks()])
    params["ext_lib"] = get_parameter(dictionary, "malicious", "external-library",
                                      lambda x: x is None or exists(x), "does not exist")
    params["wsn_gen_algo"] = get_parameter(dictionary, "simulation", "wsn-generation-algorithm",
                                      lambda x: x in list_wsn_gen_algorithms(), "is not an available WSN generation algorithm")
    # area dimensions and limits
    params["min_range"] = get_parameter(dictionary, "simulation", "minimum-distance-from-root",
                                        lambda x: isinstance(x, (int, float)) and x > 0,
                                        "is not an integer greater than 0")
    params["tx_range"] = get_parameter(dictionary, "simulation", "transmission-range",
                                       lambda x: isinstance(x, (int, float)) and x > params["min_range"],
                                       "is not an integer greater than {}".format(params["min_range"]))
    params["int_range"] = get_parameter(dictionary, "simulation", "interference-range",
                                        lambda x: isinstance(x, (int, float)) and x >= params["tx_range"],
                                        "is not an integer greater than or equal to {}".format(params["tx_range"]),
                                        default=2*params["tx_range"])
    params["area_side"] = get_parameter(dictionary, "simulation", "area-square-side",
                                        lambda x: isinstance(x, (int, float)) and x >= sqrt(2.0) * params["min_range"],
                                        "is not an integer or a float greater or equal to sqrt(2)*{:.0f}"
                                        .format(params["min_range"]))
    params["max_range"] = get_parameter(dictionary, "simulation", "area-square-side",
                                        lambda x: isinstance(x, (int, float)) and x >= params["min_range"],
                                        "is not an integer or a float greater or equal to {:.0f}"
                                        .format(params["min_range"]))
    return params


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
