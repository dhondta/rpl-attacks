# -*- coding: utf8 -*-
from fabric.api import hide, lcd, local, settings
from inspect import getmembers, isfunction
from os import chmod, listdir, makedirs
from os.path import abspath, basename, dirname, exists, expanduser, join, split, splitext
from re import match, IGNORECASE
from sys import modules
from terminaltables import SingleTable
from time import sleep

from core import *


reuse_bin_path = None


def get_commands(include=None, exclude=None):
    commands = []
    for n, f in getmembers(modules[__name__], isfunction):
        if n in [c for c, _ in commands]:
            continue
        if hasattr(f, 'behavior'):
            if f.__name__.startswith('_'):
                shortname = f.__name__.lstrip('_')
                n, f = shortname, getattr(modules[__name__], shortname)
                f.__name__ = shortname
            if (include is None or n in include) and (exclude is None or n not in exclude):
                commands.append((n, f))
    return commands


"""
Important note about command definition
---------------------------------------

For a single task, 3 functions exist :

 __[name]: the real task, with no special mechanism (input validation, exception handling, ...)
 _[name] : the task decorated by 'CommandMonitor', with an exception handling mechanism (pickable for multiprocessing)
 [name]  : the task decorated by 'command', with mechanisms of input validation, confirmation asking, ... (unpickable)

The available parameters of the 'command' decorator are :

    :param autocomplete: list of choices to be displayed when typing 2 x <TAB> (or another key if configured so in the
                          console class)
    :param examples: list of usage examples
    :param expand: a tuple with the name of an argument to be expanded and a dictionary with 2 keys: 'new_arg'
                    (optional) which gives the name of a new keyword-argument to be created with the expanded value
                    and 'into' which is the folder that the value is to be expanded into
    :param behavior: attribute to be associated to the decorated function for handling a particular behavior
                      (default is DefaultCommand ; MultiprocessedCommand is used for handling multi-processing)
    :param not_exists: a tuple with the name of an argument to be checked for non-existence and a dictionary with up to
                        4 keys: 'loglvl' which indicates the log level for the message, 'msg' the message itself, 'ask'
                        for asking the user for confirmation to continue and 'confirm' the message to be displayed
                        when asking for confirmation
    :param exists: same structure as for 'not_exists' but handling existence instead
    :param start_msg: message to be displayed before calling 'f'
    :param reexec_on_emptyline: boolean indicating if the command is to be re-executed when an empty line is
                                 input in the console
    :param __base__: special parameter to be used if the command is to be multi-processed, it holds the
                      "monitored" version of the command (that is, encapsulated inside a try-except)

"""


# ****************************** TASKS ON INDIVIDUAL EXPERIMENT ******************************
@command(autocomplete=lambda: list_experiments(),
         examples=["my-simulation"],
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
         exists=('path', {'on_boolean': 'ask', 'confirm': "Before continuing, please check that your hardware is"
                                                          " plugged.\n Are you ready ? (yes|no) [default: no] "}),
         start_msg=("BUILDING MALICIOUS MOTE BASED ON EXPERIMENT '{}'", 'name'),
         requires_sudo=True)
def build(name, ask=True, **kwargs):
    """
    Build the malicious mote to its target hardware.

    :param name: experiment name (or absolute path to experiment)
    :param ask: ask confirmation
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    def is_device_present():
        with settings(hide(*HIDDEN_ALL), warn_only=True):
            return local("if [ -c /dev/ttyUSB0 ]; then echo 'ok'; else echo 'nok'; fi", capture=True) == 'ok'

    console = kwargs.get('console')
    counter, interval = 0.0, 0.5
    while not is_device_present():
        sleep(interval)
        counter += interval
        if counter % 5 == 0:
            logger.warning("Waiting for mote to be detected...")
        elif counter >= 120:
            logger.error("Something failed with the mote ; check that it mounts to /dev/ttyUSB0")
            return
    remake(name, build=True, **kwargs) if console is None else console.do_remake(name, build=True, **kwargs)
    return "Mote built on /dev/ttyUSB0"


@command(autocomplete=lambda: list_experiments(check=False),
         examples=["my-simulation"],
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
         exists=('path', {'on_boolean': 'ask', 'confirm': "Are you sure ? (yes|no) [default: no] "}),
         start_msg=("CLEANING EXPERIMENT '{}'", 'name'))
def clean(name, ask=True, **kwargs):
    """
    Remove an experiment.

    :param name: experiment name (or absolute path to experiment)
    :param ask: ask confirmation
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    path = kwargs.get('path')
    console = kwargs.get('console')
    if console is None or not console.task_pending(name):
        logger.debug(" > Cleaning folder...")
        with hide(*HIDDEN_ALL):
            local("rm -rf {}".format(path))
    return "Cleaned"


@command(autocomplete=lambda: list_experiments(),
         examples=["my-simulation true"],
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
         start_msg=("STARTING COOJA WITH EXPERIMENT '{}'", 'name'))
def cooja(name, with_malicious=True, **kwargs):
    """
    Start an experiment in Cooja with/without the malicious mote and updates the experiment if motes' positions
     were changed.

    :param name: experiment name
    :param with_malicious: use the simulation WITH the malicious mote or not
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    sim_path = join(kwargs['path'], 'with{}-malicious'.format(['out', ''][with_malicious is True]))
    motes_before = get_motes_from_simulation(join(sim_path, 'simulation.csc'), as_dictionary=True)
    with hide(*HIDDEN_ALL):
        with lcd(sim_path):
            local("make cooja TASK={}".format(kwargs.get('task', "cooja")))
    motes_after = get_motes_from_simulation(join(sim_path, 'simulation.csc'), as_dictionary=True)
    # if there was a change, update the other simulation in this experiment
    if len(set(motes_before.items()) & set(motes_after.items())) > 0:
        other_sim_path = join(kwargs['path'], 'with{}-malicious'.format(['', 'out'][with_malicious is True]))
        set_motes_to_simulation(join(other_sim_path, 'simulation.csc'), motes_after)
    # if this experiment is part of a campaign, update this
    campaign = read_config(kwargs['path']).get('campaign')
    if campaign is not None:
        for experiment in get_experiments(campaign):
            if experiment in ['BASE', name]:
                continue
            exp_path = join(EXPERIMENT_FOLDER, experiment)
            set_motes_to_simulation(join(exp_path, 'with-malicious', 'simulation.csc'), motes_after)
            set_motes_to_simulation(join(exp_path, 'without-malicious', 'simulation.csc'), motes_after)


def __make(name, ask=True, **kwargs):
    """
    Make a new experiment.

    :param name: experiment name (or path to the experiment, if expanded in the 'command' decorator)
    :param ask: ask confirmation
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
    set_logging(kwargs.get('loglevel'))
    path = kwargs['path']
    logger.debug(" > Validating parameters...")
    params = validated_parameters(kwargs)
    ext_lib = params.get("ext_lib")
    if ext_lib and not exists(ext_lib):
        logger.error("External library does not exist !")
        logger.critical("Make aborded.")
        return False
    logger.debug(" > Creating simulation...")
    # create experiment's directories
    check_structure(path, create=True, remove=True)
    templates = get_path(path, 'templates', create=True)
    get_path(templates, 'motes', create=True)
    # select the right malicious mote template and duplicate the simulation file
    copy_files((TEMPLATES_FOLDER, 'experiment'), templates,
               ('motes/{}.c'.format(params["mtype_root"]), 'motes/root.c'),
               ('motes/{}.c'.format(params["mtype_sensor"]), 'motes/sensor.c'),
               ('motes/{}.c'.format(params["mtype_malicious"]), 'motes/malicious.c'),
               'motes/Makefile', 'Makefile', 'simulation.csc', 'script.js', 'report.md')
    # create experiment's files from templates then clean the templates folder
    replacements = render_templates(path, **params)
    # then clean the temporary folder with templates
    remove_folder(templates)
    # move the report.md file (rendered in each simulation folder) to the experiment folder
    move_files(join(path, 'with-malicious'), path, 'report.md')
    remove_files(join(path, 'without-malicious'), 'report.md')
    # now, write the config file without the list of motes
    del params['motes']
    write_config(path, params)
    # now compile
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with_malicious = join(path, 'with-malicious', 'motes')
        without_malicious = join(path, 'without-malicious', 'motes')
        contiki = join(with_malicious, split(CONTIKI_FOLDER)[-1])
        contiki_rpl = join(contiki, 'core', 'net', 'rpl')
        # copy a reduced version of Contiki where the debug flags can be set for RPL files set in DEBUG_FILES
        copy_folder(CONTIKI_FOLDER, with_malicious,
                    includes=get_contiki_includes(params["target"], params["malicious_target"]))
        apply_debug_flags(contiki_rpl, debug=['NONE', 'PRINT'][params["debug"]])
        with lcd(with_malicious):
            # first, compile root and sensor mote types
            croot, csensor = 'root.{}'.format(params["target"]), 'sensor.{}'.format(params["target"])
            if reuse_bin_path is None or reuse_bin_path == with_malicious:
                logger.debug(" > Making '{}'...".format(croot))
                stderr(local)("make root CONTIKI={}".format(contiki), capture=True)
                logger.debug(" > Making '{}'...".format(csensor))
                stderr(local)("make sensor CONTIKI={}".format(contiki), capture=True)
                # here, files are moved ; otherwise, 'make clean' would also remove *.z1
                move_files(with_malicious, without_malicious, croot, csensor)
                # after compiling, clean artifacts
                local('make clean')
                remove_files(with_malicious, 'root.c', 'sensor.c')
            else:
                copy_files(reuse_bin_path, without_malicious, croot, csensor)
            # second, handle the malicious mote compilation
            malicious = 'malicious.{}'.format(params["malicious_target"])
            if ext_lib is not None:
                remove_folder(contiki_rpl)
                copy_folder(ext_lib, contiki_rpl)
            apply_replacements(contiki_rpl, replacements)
            logger.debug(" > Making '{}'...".format(malicious))
            stderr(local)("make malicious CONTIKI={} TARGET={}"
                          .format(contiki, params["malicious_target"]), capture=True)
            # temporary move compiled malicious mote, clean the compilation artifacts, move the malicious mote back
            #  from the temporary location and copy compiled root and sensor motes
            move_files(with_malicious, without_malicious, malicious)
            local('make clean')
            move_files(without_malicious, with_malicious, malicious)
            copy_files(without_malicious, with_malicious, croot, csensor)
            # finally, remove compilation sources
            remove_files(with_malicious, 'malicious.c')
            remove_folder(contiki)
    return "Experiment folder made"
_make = CommandMonitor(__make)
make = command(
    autocomplete=lambda: list_experiments(),
    examples=["my-simulation", "my-simulation target=z1 debug=true"],
    expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
    exists=('path', {'loglvl': 'warning', 'msg': (" > Experiment '{}' already exists !", 'name'),
                     'on_boolean': 'ask', 'confirm': "Proceed anyway ? (yes|no) [default: no] "}),
    start_msg=("CREATING EXPERIMENT '{}'", 'name',),
    behavior=MultiprocessedCommand,
    __base__=_make,
)(__make)


def __remake(name, build=False, **kwargs):
    """
    Remake the malicious mote of an experiment.
     (meaning that it lets all simulation's files unchanged except ./motes/malicious.[target])

    :param name: experiment name
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    set_logging(kwargs.get('loglevel'))
    path = kwargs['path']
    logger.debug(" > Retrieving parameters...")
    params = read_config(path)
    ext_lib = params.get("ext_lib")
    if ext_lib and not exists(ext_lib):
        logger.error("External library does not exist !")
        logger.critical("Make aborted.")
        return False
    logger.debug(" > Recompiling malicious mote...")
    # remove former compiled malicious mote and prepare the template
    templates = get_path(path, 'templates', create=True)
    get_path(templates, 'motes', create=True)
    copy_files((TEMPLATES_FOLDER, 'experiment'), templates,
               ('motes/{}.c'.format(params["mtype_malicious"]), 'motes/malicious.c'))
    # recreate malicious C file from template and clean the temporary template
    replacements = render_templates(path, only_malicious=True, **params)
    # then clean the temporary folder with templates
    remove_folder(templates)
    # move the report.md file (rendered in each simulation folder) to the experiment folder
    move_files(join(path, 'with-malicious'), path, 'report.md')
    remove_files(join(path, 'without-malicious'), 'report.md')
    # now recompile
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with_malicious = join(path, 'with-malicious', 'motes')
        without_malicious = join(path, 'without-malicious', 'motes')
        contiki = join(with_malicious, split(CONTIKI_FOLDER)[-1])
        contiki_rpl = join(contiki, 'core', 'net', 'rpl')
        with lcd(with_malicious):
            malicious = 'malicious.{}'.format(params["malicious_target"])
            croot, csensor = 'root.{}'.format(params["target"]), 'sensor.{}'.format(params["target"])
            # handle the malicious mote recompilation
            copy_folder(CONTIKI_FOLDER, with_malicious, includes=get_contiki_includes(params["malicious_target"]))
            if ext_lib is not None:
                remove_folder(contiki_rpl)
                copy_folder(ext_lib, contiki_rpl)
            apply_replacements(contiki_rpl, replacements)
            if build:
                logger.debug(" > Building '{}'...".format(malicious))
                stderr(local)("sudo make malicious.upload CONTIKI={} TARGET={}".format(contiki,
                                                                                       params["malicious_target"]))
                build = get_path(path, 'build', create=True)
                move_files(with_malicious, build, 'tmpimage.ihex')
                copy_files(with_malicious, build, malicious)
            else:
                logger.debug(" > Making '{}'...".format(malicious))
                stderr(local)("make malicious CONTIKI={} TARGET={}".format(contiki, params["malicious_target"]),
                              capture=True)
            move_files(with_malicious, without_malicious, malicious)
            local('make clean')
            remove_files(with_malicious, 'malicious.c')
            move_files(without_malicious, with_malicious, malicious)
            copy_files(without_malicious, with_malicious, croot, csensor)
            remove_folder(contiki)
    return "Experiment folder remade"
_remake = CommandMonitor(__remake)
remake = command(
    autocomplete=lambda: list_experiments(),
    examples=["my-simulation"],
    expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
    not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
    start_msg=("REMAKING MALICIOUS MOTE FOR EXPERIMENT '{}'", 'name'),
    behavior=MultiprocessedCommand,
    __base__=_remake,
)(__remake)


@command(autocomplete=lambda: list_experiments(),
         examples=["my-simulation"],
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
         start_msg=("MAKING PDF REPORT OF EXPERIMENT '{}'", 'name'))
def report(name, theme=REPORT_THEME, silent=False, **kwargs):
    """
    Make the PDF report of an experiment using a given CSS theme.

    :param name: experiment name
    :param theme: path to a CSS theme
    :param silent: run command silently
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    path = kwargs['path']
    if split(theme)[0] == '':
        theme = join(dirname(REPORT_THEME), theme)
    if not exists(theme):
        logger.warning("The given CSS theme does not exist ; using default.")
        theme = REPORT_THEME
    generate_report(path, theme)
    return "Report created in experiment folder"


def __run(name, **kwargs):
    """
    Run an experiment.

    :param name: experiment name
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand')
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    set_logging(kwargs.get('loglevel'))
    path = kwargs['path']
    check_structure(path, remove=True)
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        for sim in ["without", "with"]:
            sim_path = join(path, "{}-malicious".format(sim))
            data, results = join(sim_path, 'data'), join(sim_path, 'results')
            # the Makefile is at experiment's root ('path')
            logger.debug(" > Running simulation {} the malicious mote...".format(sim))
            task = kwargs.get('task', "run")
            with lcd(sim_path):
                output = local("make run TASK={}".format(task), capture=True)
            remove_files(sim_path, '.{}'.format(task))
            error, interrupt, error_buffer = False, False, []
            for line in output.split('\n'):
                if line.strip().startswith("FATAL") or line.strip().startswith("ERROR"):
                    error, interrupt = True, True
                elif line.strip().startswith("INFO"):
                    error = False
                    if len(error_buffer) > 0:
                        logger.error('Cooja error:\n' + '\n'.join(error_buffer))
                        error_buffer = []
                if error:
                    error_buffer.append(line)
            if interrupt:
                logger.warn("Cooja failed to execute ; 'run' interrupted (no parsing done)")
                raise Exception("Cooja failed to execute")
            # once the execution is over, gather the screenshots into a single GIF and keep the first and
            #  the last screenshots ; move these to the results folder
            logger.debug(" > Gathering screenshots in an animated GIF...")
            with lcd(data):
                local('convert -delay 10 -loop 0 network*.png wsn-{}-malicious.gif'.format(sim), capture=True)
            network_images = {int(fn.split('.')[0].split('_')[-1]): fn for fn in listdir(data)
                              if fn.startswith('network_')}
            move_files(data, results, 'wsn-{}-malicious.gif'.format(sim))
            if len(network_images) > 0:
                net_start_old = network_images[min(network_images.keys())]
                net_start, ext = splitext(net_start_old)
                net_start_new = 'wsn-{}-malicious_start{}'.format(sim, ext)
                net_end_old = network_images[max(network_images.keys())]
                net_end, ext = splitext(net_end_old)
                net_end_new = 'wsn-{}-malicious_end{}'.format(sim, ext)
                move_files(data, results, (net_start_old, net_start_new), (net_end_old, net_end_new))
                remove_files(data, *network_images.values())
            # then start the parsing functions to derive more results
            parsing_chain(sim_path, logger)
            move_files(sim_path, results, 'COOJA.log')
        # finally, generate the PDF report
        generate_report(path, REPORT_THEME)
    return "Both Cooja executions succeeded"
_run = CommandMonitor(__run)
run = command(
    autocomplete=lambda: list_experiments(),
    examples=["my-simulation"],
    expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
    not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
    start_msg=("PROCESSING EXPERIMENT '{}'", 'name'),
    behavior=MultiprocessedCommand,
    __base__=_run,
    logger=logger,
)(__run)


# ****************************** COMMANDS ON SIMULATION CAMPAIGN ******************************
@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def clean_all(exp_file, **kwargs):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    console = kwargs.get('console')
    silent = kwargs.get('silent', False)
    experiments = {k: v for k, v in get_experiments(exp_file).items() if k != 'BASE'}
    for name, params in experiments.items():
        clean(name, ask=False, silent=silent) if console is None else console.do_clean(name, ask=False, silent=silent)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         exists=('exp_file', {'on_boolean': 'ask', 'confirm': "Are you sure ? (yes|no) [default: no] "}),
         start_msg=("REMOVING EXPERIMENT CAMPAIGN AT '{}'", 'exp_file'))
def drop(exp_file, ask=True, **kwargs):
    """
    Remove a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param ask: ask confirmation
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    remove_files(EXPERIMENT_FOLDER, exp_file)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def make_all(exp_file, **kwargs):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
    console = kwargs.get('console')
    clean_all(exp_file, silent=True) if console is None else console.do_clean_all(exp_file, silent=True)
    experiments = get_experiments(exp_file, silent=True)
    sim_json, motes = None, None
    # if a simulation named 'BASE' is present, use it as a template simulation for all the other simulations
    if 'BASE' in experiments.keys():
        experiments['BASE']['silent'] = True
        sim_json = dict(experiments['BASE']['simulation'])
        wsn_gen = eval(sim_json.get('wsn-generation-algorithm', DEFAULTS['wsn-generation-algorithm']))
        motes = wsn_gen(defaults=DEFAULTS, **validated_parameters(experiments['BASE']))
        del experiments['BASE']
    for name, params in sorted(experiments.items(), key=lambda x: x[0]):
        params['campaign'] = splitext(basename(exp_file))[0]
        if sim_json is not None:
            params.setdefault('simulation', {})
            for k, v in sim_json.items():
                if k not in params['simulation'].keys():
                    params['simulation'][k] = v
            params['motes'] = motes
        make(name, ask=False, **params) if console is None else console.do_make(name, ask=False, **params)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         exists=('exp_file', {'loglvl': 'warning', 'msg': (" > Experiment campaign '{}' already exists !", 'exp_file'),
                              'on_boolean': 'ask', 'confirm': "Overwrite ? (yes|no) [default: no] "}),
         start_msg=("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'", 'exp_file'))
def prepare(exp_file, ask=True, **kwargs):
    """
    Create a campaign of experiments from a template.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param ask: ask confirmation
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    render_campaign(exp_file)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def remake_all(exp_file, **kwargs):
    """
    Remake a campaign of experiments (that is, rebuild the malicious for each experiment).

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    console = kwargs.get('console')
    experiments = {k: v for k, v in get_experiments(exp_file).items() if k != 'BASE'}
    for name, params in sorted(experiments.items(), key=lambda x: x[0]):
        remake(name, **params) if console is None else console.do_remake(name, **params)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def run_all(exp_file, **kwargs):
    """
    Run a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    console = kwargs.get('console')
    for name in get_experiments(exp_file).keys():
        if name != 'BASE':
            run(name) if console is None else console.do_run(name)


# ************************************** INFORMATION COMMANDS *************************************
@command(autocomplete=["campaigns", "experiments", "wsn-generation-algorithms"],
         examples=["experiments", "campaigns", "wsn-generation-algorithms"],
         reexec_on_emptyline=True)
def list(item_type, **kwargs):
    """
    List all available items of a specified type.

    :param item_type: experiment/campaign/wsn-generation-algorithm
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    data, title = [['Name']], None
    if item_type == 'experiments':
        title = 'Available experiments'
        data.extend([['- {}'.format(x).ljust(25)] for x in list_experiments()])
    elif item_type == 'campaigns':
        title = 'Available campaigns'
        data.extend([['- {}'.format(x).ljust(25)] for x in list_campaigns()])
    elif item_type == 'wsn-generation-algorithms':
        title = 'Available WSN generation algorithms'
        data.extend([['- {}'.format(x).ljust(25)] for x in list_wsn_gen_algorithms()])
    if title is not None:
        table = SingleTable(data, title)
        print(table.table)


# ***************************************** SETUP COMMANDS ****************************************
@command(examples=["/opt/contiki", "~/contiki ~/Documents/experiments"],
         start_msg="CREATING CONFIGURATION FILE AT '~/.rpl-attacks.conf'")
def config(contiki_folder='~/contiki', experiments_folder='~/Experiments', silent=False, **kwargs):
    """
    Create a new configuration file at ~/.rpl-attacks.conf.

    :param contiki_folder: Contiki folder
    :param experiments_folder: experiments folder
    :param silent: run command silently
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    get_path(experiments_folder, create=True)
    with open(expanduser('~/.rpl-attacks.conf'), 'w+') as f:
        f.write('[RPL Attacks Framework Configuration]\n')
        f.write('contiki_folder = {}\n'.format(contiki_folder))
        f.write('experiments_folder = {}\n'.format(experiments_folder))


@command(start_msg="TESTING THE FRAMEWORK")
def test(**kwargs):
    """
    Run framework's tests.

    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    with settings(warn_only=True):
        print(FRAMEWORK_FOLDER)
        with lcd(FRAMEWORK_FOLDER):
            local("python -m unittest -v tests")


@command(start_msg="SETTING UP OF THE FRAMEWORK", requires_sudo=True)
def setup(silent=False, **kwargs):
    """
    Setup the framework.

    :param silent: run command silently
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    recompile = False
    # adapt RPL debug mode
    modify_rpl_debug(CONTIKI_FOLDER)
    # install Cooja modifications
    if not check_cooja(COOJA_FOLDER):
        logger.debug(" > Installing Cooja add-ons...")
        # modify Cooja.java and adapt build.xml and ~/.cooja.user.properties
        modify_cooja(COOJA_FOLDER)
        update_cooja_build(COOJA_FOLDER)
        update_cooja_user_properties()
        recompile = True
    # install VisualizerScreenshot plugin in Cooja
    visualizer = join(COOJA_FOLDER, 'apps', 'visualizer_screenshot')
    if not exists(visualizer):
        logger.debug(" > Installing VisualizerScreenshot Cooja plugin...")
        copy_folder('src/visualizer_screenshot', visualizer)
        recompile = True
    # recompile Cooja for making the changes take effect
    if recompile:
        with hide(*HIDDEN_ALL):
            with lcd(CONTIKI_FOLDER):
                local('git submodule update --init')
            with lcd(COOJA_FOLDER):
                logger.debug(" > Recompiling Cooja...")
                for cmd in ["clean", "jar"]:
                    output = local("ant {}".format(cmd), capture=True)
                    info, error = False, False
                    for line in output.split('\n'):
                        if line.strip() == "":
                            info, error = False, False
                        elif line.startswith("BUILD"):
                            info, error = "SUCCESSFUL" in line, "FAILED" in line
                        if info or error:
                            getattr(logger, "debug" if info else "error" if error else "warn")(line)
    else:
        logger.debug(" > Cooja is up-to-date")
    # install imagemagick
    with hide(*HIDDEN_ALL):
        imagemagick_apt_output = local('apt-cache policy imagemagick', capture=True)
        if 'Unable to locate package' in imagemagick_apt_output:
            logger.debug(" > Installing imagemagick package...")
            local('sudo apt-get install imagemagick -y &')
        else:
            logger.debug(" > Imagemagick is installed")
    # create a new desktop shortcut for the framework
    desktop = expanduser('~/Desktop')
    shortcut = join(desktop, 'rpl-attacks-framework.desktop')
    if not exists(desktop):
        makedirs(desktop)
    if not exists(shortcut):
        with hide(*HIDDEN_ALL):
            local('sudo cp {} /usr/share/icons/hicolor/scalable/apps/'
                  .format(join(FRAMEWORK_FOLDER, 'src/rpla-icon.png')))
            local('sudo gtk-update-icon-cache /usr/share/icons/hicolor')
        with open(shortcut, 'w+') as f:
            f.write(SHORTCUT_RPLA.format(path=abspath(FRAMEWORK_FOLDER)))
        with hide(*HIDDEN_ALL):  # (Ubuntu 18.04 fix to automatically trust the new shortcut)
            local('gio set {} "metadata::trusted" yes'.format(shortcut))
        chmod(shortcut, int('775', 8))
        logger.debug(" > Desktop shortcut for RPLA created")
    else:
        logger.debug(" > Desktop shortcut for RPLA already exists")
    # create a new desktop shortcut for the Cooja simulator
    shortcut = join(desktop, 'cooja-simulator.desktop')
    if not exists(shortcut):
        with hide(*HIDDEN_ALL):
            local('sudo cp {} /usr/share/icons/hicolor/scalable/apps/'
                  .format(join(FRAMEWORK_FOLDER, 'src/cooja-icon.png')))
            local('sudo gtk-update-icon-cache /usr/share/icons/hicolor')
        with open(shortcut, 'w+') as f:
            f.write(SHORTCUT_COOJA.format(path=join(CONTIKI_FOLDER, "tools", "cooja", "build")))
        with hide(*HIDDEN_ALL):  # (Ubuntu 18.04 fix to automatically trust the new shortcut)
            local('gio set {} "metadata::trusted" yes'.format(shortcut))
        chmod(shortcut, int('775', 8))
        logger.debug(" > Desktop shortcut for Cooja created")
    else:
        logger.debug(" > Desktop shortcut for Cooja already exists")


@command(start_msg="UPDATING CONTIKI-OS AND RPL ATTACKS FRAMEWORK")
def update(silent=False, **kwargs):
    """
    Update Contiki-OS and RPL Attacks Framework.

    :param silent: run command silently
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    updated = False
    for folder, repository in zip([CONTIKI_FOLDER, FRAMEWORK_FOLDER], ["Contiki-OS", "RPL Attacks Framework"]):
        with hide(*HIDDEN_ALL):
            with lcd(folder):
                if "Could not resolve proxy" in local('git fetch --all', capture=True):
                    logger.error("Update failed ; please check your proxy settings")
                    break
                uptodate = "branch is up-to-date" in local('git checkout master', capture=True).strip().split('\n')[-1]
                if not uptodate:
                    req_exists = exists("requirements.txt")
                    if req_exists:
                        req_md5 = hash_file("requirements.txt")
                    logger.warn("You are about to loose any custom change made to {} ;".format(repository))
                    if silent or std_input("Proceed anyway ? (yes|no) [default: no] ", 'yellow') == 'yes':
                        local('git submodule update --init')
                        local('git fetch --all')
                        local('git reset --hard origin/master')
                        local('git pull')
                        if req_exists and hash_file("requirements.txt") != req_md5:
                            local('pip install -r requirements.txt')
                        updated = True
            if repository == "RPL Attacks Framework":
                remove_files(folder, "Vagrantfile")
                remove_folder(join(folder, "provisioning"))
            logger.debug(" > {} {}".format(repository, ["updated", "already up-to-date"][uptodate]))
    if updated:
        setup(silent)
        if not silent:
            logger.warn("Restarting the framework...")
            restart(PIDFILE)


@command(start_msg="CHECKING VERSIONS")
def versions(**kwargs):
    """
    Check versions of Contiki-OS and RPL Attacks Framework.

    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    with hide(*HIDDEN_ALL):
        with lcd(CONTIKI_FOLDER):
            cversion = local('git --git-dir .git describe --tags --always', capture=True)
        logger.warn("Contiki-OS: {}".format(cversion))
        with lcd(FRAMEWORK_FOLDER):
            cversion = local('git --git-dir .git describe --tags --always', capture=True)
        logger.warn("RPL Attacks Framework: {}".format(cversion))


# **************************************** MAGICAL COMMANDS ***************************************
@command(start_msg="STARTING THE DEMO")
def demo(**kwargs):
    """
    Prepare the example campaign 'rpl-attacks.json' contained in the 'examples' folder of the framework.
    """
    console = kwargs.get('console')
    logger.debug(" > Copying 'rpl-attacks.json' to the experiments folder...")
    copy_files((FRAMEWORK_FOLDER, 'examples'), EXPERIMENT_FOLDER, 'rpl-attacks.json')
    logger.debug(" > Making all simulations of 'rpl-attacks.json'...")
    make_all('rpl-attacks', **kwargs) if console is None else console.do_make_all('rpl-attacks', **kwargs)
    if console is not None:
       console.wait_for_task("make")
    experiments = get_experiments('rpl-attacks', silent=True)
    del experiments['BASE']
    for name, params in sorted(experiments.items(), key=lambda x: x[0]):
        sim = params.get('simulation')
        if sim is None:
            continue
        comments = [sim[p] for p in sim.keys() if p.startswith('comment-')]
        report = join(EXPERIMENT_FOLDER, name, 'report.md')
        with open(report) as f:
            content = f.read()
        for comment in comments:
            content = content.replace("Insert your comments here.", comment, 1)
        with open(report, 'w') as f:
            f.write(content)
    logger.debug(" > Running all simulations of 'rpl-attacks.json'...")
    run_all('rpl-attacks', **kwargs) if console is None else console.do_run_all('rpl-attacks', **kwargs)
