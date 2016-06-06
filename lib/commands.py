# -*- coding: utf8 -*-
from fabric.api import hide, lcd, local, settings, sudo
from inspect import getmembers, isfunction
from os import listdir
from os.path import exists, expanduser, join, splitext
from sys import modules
from terminaltables import SingleTable

from .behaviors import MultiprocessedCommand
from .constants import CONTIKI_FOLDER, COOJA_FOLDER, DEFAULTS, EXPERIMENT_FOLDER, FRAMEWORK_FOLDER, TEMPLATES_FOLDER
from .decorators import CommandMonitor, command, stderr
from .helpers import copy_files, copy_folder, move_files, remove_files, remove_folder, \
                     std_input, read_config, write_config
from .install import check_cooja, modify_cooja, register_new_path_in_profile, \
                     update_cooja_build, update_cooja_user_properties
from .logconfig import logger, HIDDEN_ALL
from .parser import parsing_chain
from .utils import apply_debug_flags, apply_replacements, check_structure, generate_motes, \
                   get_contiki_includes, get_experiments, get_path, list_campaigns, list_experiments, \
                   render_campaign, render_templates, validated_parameters

reuse_bin_path = None


def get_commands(include=None, exclude=None):
    commands = []
    for n, f in getmembers(modules[__name__], isfunction):
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
    :param add_console_to_kwargs: boolean indicating if the 'console' object is to be added to kwargs
                                   (for usage inside command's code)
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
         add_console_to_kwargs=True)
def build(name, ask=True, **kwargs):
    """
    Build the malicious mote to its target hardware.

    :param name: experiment name (or absolute path to experiment)
    :param ask: ask confirmation
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand'
    """
    console = kwargs.get('console')
    remake(name, build=True, **kwargs) if console is None else console.do_remake(name, build=True, **kwargs)


@command(autocomplete=lambda: list_experiments(),
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
    """
    logger.debug(" > Cleaning folder...")
    with hide(*HIDDEN_ALL):
        local("rm -rf {}".format(kwargs['path']))


@command(autocomplete=lambda: list_experiments(),
         examples=["my-simulation true"],
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
         start_msg=("STARTING COOJA WITH EXPERIMENT '{}'", 'name'))
def cooja(name, with_malicious=False, **kwargs):
    """
    Start an experiment in Cooja with/without the malicious mote.

    :param name: experiment name
    :param with_malicious: use the simulation WITH the malicious mote or not
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand'
    """
    with hide(*HIDDEN_ALL):
        with lcd(join(kwargs['path'], 'with{}-malicious'.format('' if with_malicious else 'out'))):
            local("make cooja")


def __make(name, ask=True, **kwargs):
    """
    Make a new experiment.

    :param name: experiment name (or path to the experiment, if expanded in the 'command' decorator)
    :param ask: ask confirmation
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand'
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
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
    copy_files((TEMPLATES_FOLDER, 'experiment'), templates, 'motes/root.c', 'motes/sensor.c',
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'),
               'motes/Makefile', 'Makefile', 'simulation.csc', 'script.js')
    # create experiment's files from templates then clean the templates folder
    replacements = render_templates(path, **params)
    remove_folder(templates)
    # now, write the config file without the list of motes
    del params['motes']
    write_config(path, params)
    # now compile
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with_malicious = join(path, 'with-malicious', 'motes')
        without_malicious = join(path, 'without-malicious', 'motes')
        copy_folder(CONTIKI_FOLDER, with_malicious, includes=get_contiki_includes(params["target"]))
        contiki = join(with_malicious, 'contiki')
        contiki_rpl = join(contiki, 'core', 'net', 'rpl')
        apply_debug_flags(contiki_rpl, debug=['NONE', 'PRINT'][params["debug"]])
        with lcd(with_malicious):
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
            # now, handle the malicious mote compilation
            malicious = 'malicious.{}'.format(params["malicious_target"])
            if ext_lib is not None:
                copy_folder(ext_lib, contiki_rpl)
            apply_replacements(contiki_rpl, replacements)
            logger.debug(" > Making '{}'...".format(malicious))
            stderr(local)("make malicious CONTIKI={} TARGET={}"
                          .format(contiki, params["malicious_target"]), capture=True)
            move_files(with_malicious, without_malicious, malicious)
            local('make clean')
            remove_files(with_malicious, 'malicious.c')
            move_files(without_malicious, with_malicious, malicious)
            copy_files(without_malicious, with_malicious, croot, csensor)
            remove_folder(contiki)
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
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand'
    """
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
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'))
    # recreate malicious C file from template and clean the temporary template
    replacements = render_templates(path, only_malicious=True, **params)
    # then clean the temporary folder with templates
    remove_folder(templates)
    # now recompile
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with_malicious = join(path, 'with-malicious', 'motes')
        without_malicious = join(path, 'without-malicious', 'motes')
        with lcd(with_malicious):
            malicious = 'malicious.{}'.format(params["malicious_target"])
            croot, csensor = 'root.{}'.format(params["target"]), 'sensor.{}'.format(params["target"])
            # handle the malicious mote recompilation
            copy_folder(CONTIKI_FOLDER, with_malicious, includes=get_contiki_includes(params["target"]))
            contiki_rpl = join(with_malicious, 'contiki', 'core', 'net', 'rpl')
            if ext_lib is not None:
                copy_folder(ext_lib, contiki_rpl)
            apply_replacements(contiki_rpl, replacements)
            logger.debug(" > Making '{}'...".format(malicious))
            stderr(local)("make malicious{} CONTIKI={}"
                          .format(['', '.upload'][build], join(with_malicious, 'contiki')), capture=True)
            if build:
                build = get_path(path, 'build', create=True)
                move_files(with_malicious, build, 'tmpimage.ihex')
                copy_files(with_malicious, build, malicious)
            move_files(with_malicious, without_malicious, malicious)
            local('make clean')
            remove_files(with_malicious, 'malicious.c')
            move_files(without_malicious, with_malicious, malicious)
            copy_files(without_malicious, with_malicious, croot, csensor)
            remove_folder((with_malicious, 'contiki'))
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


def __run(name, **kwargs):
    """
    Run an experiment.

    :param name: experiment name
    :param path: expanded path of the experiment (dynamically filled in through 'command' decorator with 'expand'
    """
    path = kwargs['path']
    check_structure(path, remove=True)
    with hide(*HIDDEN_ALL):
        for sim in ["without", "with"]:
            sim_path = join(path, "{}-malicious".format(sim))
            data, results = join(sim_path, 'data'), join(sim_path, 'results')
            # the Makefile is at experiment's root ('path')
            with lcd(sim_path):
                logger.debug(" > Running simulation {} the malicious mote...".format(sim))
                local("make run", capture=True)
            # simulations are in their respective folders ('sim_path')
            remove_files(sim_path, 'COOJA.log', 'COOJA.testlog')
            # once the execution is over, gather the screenshots into a single GIF and keep the first and
            #  the last screenshots ; move these to the results folder
            with lcd(data):
                local('convert -delay 10 -loop 0 network*.png wsn-{}-malicious.gif'.format(sim))
            network_images = {int(fn.split('.')[0].split('_')[-1]): fn for fn in listdir(data)
                              if fn.startswith('network_')}
            move_files(data, results, 'wsn-{}-malicious.gif'.format(sim))
            net_start_old = network_images[min(network_images.keys())]
            net_start, ext = splitext(net_start_old)
            net_start_new = 'wsn-{}-malicious_start{}'.format(sim, ext)
            net_end_old = network_images[max(network_images.keys())]
            net_end, ext = splitext(net_end_old)
            net_end_new = 'wsn-{}-malicious_end{}'.format(sim, ext)
            move_files(data, results, (net_start_old, net_start_new), (net_end_old, net_end_new))
            remove_files(data, *network_images.values())
            parsing_chain(sim_path, with_malicious=sim == "with")
_run = CommandMonitor(__run)
run = command(
    autocomplete=lambda: list_experiments(),
    examples=["my-simulation"],
    expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
    not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}),
    start_msg=("PROCESSING EXPERIMENT '{}'", 'name'),
    behavior=MultiprocessedCommand,
    __base__=_run,
)(__run)


# ****************************** COMMANDS ON SIMULATION CAMPAIGN ******************************
@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def clean_all(exp_file):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    for name, params in get_experiments(exp_file).items():
        clean(name, ask=False, silent=True)


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
    """
    remove_files(EXPERIMENT_FOLDER, exp_file)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}),
         add_console_to_kwargs=True)
def make_all(exp_file, **kwargs):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    global reuse_bin_path
    console = kwargs.get('console')
    clean_all(exp_file)
    experiments = get_experiments(exp_file)
    sim_params, motes = None, None
    # if a simulation named 'BASE' is present, use it as a template simulation for all the other simulations
    if 'BASE' in experiments.keys():
        experiments['BASE']['silent'] = True
        sim_params = validated_parameters(experiments['BASE'])
        motes = generate_motes(defaults=DEFAULTS, **sim_params)
        del experiments['BASE']
    for name, params in sorted(experiments.items(), key=lambda x: x[0]):
        exp_params = {}
        if sim_params is not None:
            exp_params.update(sim_params)
        exp_params.update(params)
        if sim_params is not None:
            params['motes'] = motes
        make(name, **exp_params) if console is None else console.do_make(name, **exp_params)


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
    """
    render_campaign(exp_file)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}),
         add_console_to_kwargs=True)
def remake_all(exp_file, **kwargs):
    """
    Remake a campaign of experiments (that is, rebuild the malicious for each experiment).

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    console = kwargs.get('console')
    experiments = {k: v for k, v in get_experiments(exp_file).items() if k != 'BASE'}
    for name, params in sorted(experiments.items(), key=lambda x: x[0]):
        make(name, **params) if console is None else console.do_make(name, **params)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}),
         add_console_to_kwargs=True)
def run_all(exp_file, **kwargs):
    """
    Run a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    console = kwargs.get('console')
    for name in get_experiments(exp_file).keys():
        if name != 'BASE':
            run(name) if console is None else console.do_run(name)


# ************************************** INFORMATION COMMANDS *************************************
@command(autocomplete=["campaigns", "experiments"],
         examples=["experiments", "campaigns"],
         reexec_on_emptyline=True)
def list(item_type):
    """
    List all available items of a specified type.

    :param item_type: experiment/campaign
    """
    data, title = [['Name']], None
    if item_type == 'experiments':
        title = 'Available experiments'
        data.extend([['- {}'.format(x).ljust(25)] for x in list_experiments()])
    elif item_type == 'campaigns':
        title = 'Available campaigns'
        data.extend([['- {}'.format(x).ljust(25)] for x in list_campaigns()])
    if title is not None:
        table = SingleTable(data, title)
        print(table.table)


# ***************************************** SETUP COMMANDS *****************************************
@command(examples=["/opt/contiki", "~/contiki ~/Documents/experiments"],
         start_msg="CREATING CONFIGURATION FILE AT '~/.rpl-attacks.conf'")
def config(contiki_folder='~/contiki', experiments_folder='~/Experiments', silent=False):
    """
    Create a new configuration file at `~/.rpl-attacks.conf`.

    :param contiki_folder: Contiki folder
    :param experiments_folder: experiments folder
    """
    with open(expanduser('~/.rpl-attacks.conf'), 'w') as f:
        f.write('[RPL Attacks Framework Configuration]\n')
        f.write('contiki_folder = {}\n'.format(contiki_folder))
        f.write('experiments_folder = {}\n'.format(experiments_folder))


@command(start_msg="TESTING THE FRAMEWORK")
def test():
    """
    Run framework's tests.
    """
    with settings(warn_only=True):
        with lcd(FRAMEWORK_FOLDER):
            local("python -m unittest tests")


@command(start_msg="SETTING UP OF THE FRAMEWORK")
def setup(silent=False):
    """
    Setup the framework.
    """
    recompile = False
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
        with lcd(COOJA_FOLDER):
            logger.debug(" > Recompiling Cooja...")
            with settings(warn_only=True):
                local("ant clean")
                local("ant jar")
    else:
        logger.debug(" > Cooja is up-to-date")
    # install imagemagick
    with hide(*HIDDEN_ALL):
        imagemagick_apt_output = local('apt-cache policy imagemagick', capture=True)
        if 'Unable to locate package' in imagemagick_apt_output:
            logger.debug(" > Installing imagemagick package...")
            sudo("apt-get install imagemagick -y &")
        else:
            logger.debug(" > Imagemagick is installed")
    # install msp430 (GCC) upgrade
    with hide(*HIDDEN_ALL):
        msp430_version_output = local('msp430-gcc --version', capture=True)
    if 'msp430-gcc (GCC) 4.7.0 20120322' not in msp430_version_output:
        txt = "In order to extend msp430x memory support, it is necessary to upgrade msp430-gcc.\n" \
              "Would you like to upgrade it now ? (yes|no) [default: no] "
        answer = std_input(txt, 'yellow')
        if answer == "yes":
            logger.debug(" > Upgrading msp430-gcc from version 4.6.3 to 4.7.0...")
            logger.warning("If you encounter problems with this upgrade, please refer to:\n"
                           "https://github.com/contiki-os/contiki/wiki/MSP430X")
            with lcd('src/'):
                logger.warning(" > Upgrade now starts, this may take up to 30 minutes...")
                sudo('./upgrade-msp430.sh')
                sudo('rm -r tmp/')
                local('export PATH=/usr/local/msp430/bin:$PATH')
                register_new_path_in_profile()
        else:
            logger.warning("Upgrade of library msp430-gcc aborted")
            logger.warning("You may experience problems of mote memory size at compilation")
    else:
        logger.debug(" > Library msp430-gcc is up-to-date (version 4.7.0)")


# **************************************** MAGIC COMMAND ****************************************
@command(autocomplete=lambda: list_experiments(),
         expand=('name', {'new_arg': 'path', 'into': EXPERIMENT_FOLDER}),
         not_exists=('path', {'loglvl': 'error', 'msg': (" > Experiment '{}' does not exist !", 'name')}))
def rip_my_slip(name, **kwargs):
    """
    Run a demonstration.
    """
    # TODO: prepare 'rpl-attacks' campaign, make all its experiments then run them
    parsing_chain(join(kwargs.get('path'), 'with-malicious'))
