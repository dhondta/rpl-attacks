# -*- coding: utf8 -*-
from fabric.api import hide, lcd, local, settings, sudo
from inspect import getmembers, isfunction
from os import listdir
from os.path import dirname, exists, expanduser, join, splitext
from sys import modules
from terminaltables import SingleTable

from .behaviors import MultiprocessedCommand
from .constants import CONTIKI_FOLDER, COOJA_FOLDER, EXPERIMENT_FOLDER, FRAMEWORK_FOLDER, TEMPLATES_FOLDER
from .decorators import CommandMonitor, command, stderr
from .helpers import copy_files, copy_folder, move_files, move_folder, remove_files, remove_folder, \
                     std_input, read_config, write_config
from .install import check_cooja, modify_cooja, register_new_path_in_profile, \
                     update_cooja_build, update_cooja_user_properties
from .logconfig import logger, HIDDEN_ALL
from .utils import check_structure, get_contiki_includes, get_experiments, get_path, list_campaigns, \
                   list_experiments, render_templates, validated_parameters

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
"""


# ****************************** TASKS ON INDIVIDUAL EXPERIMENT ******************************
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
    """
    with hide(*HIDDEN_ALL):
        with lcd(kwargs['path']):
            local("make cooja-with{}-malicious".format("" if with_malicious else "out"))


def __make(name, ask=True, **kwargs):
    """
    Make a new experiment.

    :param name: experiment name (or path to the experiment, if expanded in the 'command' decorator)
    :param ask: ask confirmation
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
    path = kwargs.pop('path')
    logger.debug(" > Validating parameters...")
    params = validated_parameters(kwargs)
    ext_lib = params.get("ext_lib")
    logger.debug(" > Creating simulation...")
    # create experiment's directories and config file
    get_path(path, create=True)
    get_path(path, 'motes', create=True)
    get_path(path, 'data', create=True)
    get_path(path, 'results', create=True)
    write_config(path, params)
    # select the right malicious mote template and duplicate the simulation file
    copy_folder(TEMPLATES_FOLDER, path)
    tmp = get_path(path, 'templates')
    copy_files(tmp, tmp,
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'),
               ('simulation.csc', 'simulation_without_malicious.csc'),
               ('simulation.csc', 'simulation_with_malicious.csc'))
    # create experiment's files from templates
    render_templates(path, **params)
    # then clean the temporary folder with templates
    remove_folder(tmp)
    if ext_lib and not exists(ext_lib):
        logger.error("External library does not exist !")
        logger.critical("Make aborded.")
        return False
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with lcd(path):
            # for every simulation, root and sensor compilation is the same ;
            #  then, if these were not previously compiled, proceed
            if reuse_bin_path is None or reuse_bin_path == path:
                logger.debug(" > Making 'root.{}'...".format(params["target"]))
                stderr(local)("make motes/root", capture=True)
                logger.debug(" > Making 'sensor.{}'...".format(params["target"]))
                stderr(local)("make motes/sensor", capture=True)
                # after compiling, clean artifacts
                local('make clean')
                remove_files(path, 'motes/root.c', 'motes/sensor.c')
                # save this path (can be reused while creating other simulations)
                reuse_bin_path = path
            # otherwise, reuse them by copying the compiled files to the current experiment folder
            else:
                copy_files(reuse_bin_path, path, "motes/root.{}".format(params["target"]),
                           "motes/sensor.{}".format(params["target"]))
                remove_files(path, 'motes/root.c', 'motes/sensor.c')
            # now, handle the malicious mote compilation
            copy_folder(CONTIKI_FOLDER, path, includes=get_contiki_includes(params["target"]))
            if ext_lib is not None:
                copy_folder(ext_lib, (path, 'contiki', 'core', 'net', 'rpl'))
            logger.debug(" > Making 'malicious.{}'...".format(params["target"]))
            stderr(local)("make motes/malicious TARGET={}".format(params["target"]), capture=True)
            local('make clean')
            remove_files(path, 'motes/malicious.c')
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


def __remake(name, **kwargs):
    """
    Remake the malicious mote of an experiment.
     (meaning that it lets all simulation's files unchanged except ./motes/malicious.[target])

    :param name: experiment name
    """
    logger.debug(" > Retrieving parameters...")
    path = kwargs.pop('path')
    params = read_config(path)
    ext_lib = params.get("ext_lib")
    logger.debug(" > Recompiling malicious mote...")
    # remove former compiled malicious mote and prepare the template
    remove_files('motes/malicious.c')
    copy_files(TEMPLATES_FOLDER, TEMPLATES_FOLDER,
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'))
    # recreate malicious C file from template and clean the temporary template
    render_templates(path, True, **params)
    remove_files(TEMPLATES_FOLDER, 'motes/malicious.c')
    if ext_lib and not exists(ext_lib):
        logger.error("External library does not exist !")
        logger.critical("Make aborded.")
        return False
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with lcd(path):
            # handle the malicious mote recompilation
            if ext_lib is not None:
                # backup original RPL library and replace it with attack's library
                get_path('.tmp')
                move_folder((CONTIKI_FOLDER, 'core', 'net', 'rpl'), '.tmp')
                copy_folder(ext_lib, (CONTIKI_FOLDER, 'core', 'net', 'rpl'))
            logger.debug(" > Making 'malicious.{}'...".format(params["target"]))
            stderr(local)("make motes/malicious TARGET={}".format(params["target"]), capture=True)
            if ext_lib is not None:
                # then, clean temporary files
                remove_folder((CONTIKI_FOLDER, 'core', 'net', 'rpl'))
                move_folder('.tmp/rpl', (CONTIKI_FOLDER, 'core', 'net'))
                remove_folder('.tmp')
            remove_files(path,
                         'contiki-{}.a'.format(params["target"]),
                         'contiki-{}.map'.format(params["target"]),
                         'symbols.c',
                         'symbols.h',
                         'motes/malicious.c')
            remove_folder((path, 'obj_{}'.format(params["target"])))
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
    """
    path = kwargs.pop('path')
    check_structure(path, remove=True)
    data, results = join(path, 'data'), join(path, 'results')
    with hide(*HIDDEN_ALL):
        for sim in ["without", "with"]:
            with lcd(path):
                logger.debug(" > Running simulation {} the malicious mote...".format(sim))
                local("make run-{}-malicious".format(sim), capture=True)
            remove_files(path,
                         'COOJA.log',
                         'COOJA.testlog')
            # once the execution is over, gather the screenshots into a single GIF and keep the first and
            #  the last screenshots ; move these to the results folder
            with lcd(data):
                local('convert -delay 10 -loop 0 network*.png wsn-{}-malicious.gif'.format(sim))
            network_images = {int(fn.split('.')[0].split('_')[-1]): fn for fn in listdir(data) \
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
         exists=('exp_file', {'on_boolean': 'ask', 'confirm': "Are you sure ? (yes|no) [default: no] "}),
         start_msg=("REMOVING EXPERIMENT CAMPAIGN AT '{}'", 'exp_file'))
def drop(exp_file='experiments', ask=True):
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
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def make_all(exp_file="experiments", **kwargs):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    global reuse_bin_path
    console = kwargs.get('console')
    for name, params in sorted(get_experiments(exp_file).items(), key=lambda x: x[0]):
        clean(name, ask=False, silent=True)
        make(name, **params) if console is None else console.do_make(name, **params)


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         exists=('exp_file', {'loglvl': 'warning', 'msg': (" > Experiment campaign '{}' already exists !", 'exp_file'),
                              'on_boolean': 'ask', 'confirm': "Overwrite ? (yes|no) [default: no] "}),
         start_msg=("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'", 'exp_file'))
def prepare(exp_file='experiments', ask=True):
    """
    Create a campaign of experiments from a template.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    copy_files(TEMPLATES_FOLDER, dirname(exp_file), ('experiments.json', exp_file))


@command(autocomplete=lambda: list_campaigns(),
         examples=["my-simulation-campaign"],
         expand=('exp_file', {'into': EXPERIMENT_FOLDER, 'ext': 'json'}),
         not_exists=('exp_file', {'loglvl': 'error',
                                  'msg': (" > Experiment campaign '{}' does not exist !", 'exp_file')}))
def run_all(exp_file="experiments"):
    """
    Run a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    for name in get_experiments(exp_file).keys():
        run(name)


# ************************************** INFORMATION COMMANDS *************************************
@command(autocomplete=["campaigns", "experiments"],
         examples=["experiments", "campaigns"],
         reexec_on_emptyline=True)
def list(item_type=None):
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
@command(examples=["/opt/contiki", "~/contiki ~/Documents/experiments"])
def config(contiki_folder='~/contiki', experiments_folder='~/Experiments'):
    """
    Create a new configuration file at `~/.rpl-attacks.conf`.

    :param contiki_folder: Contiki folder
    :param experiments_folder: experiments folder
    """
    logger.info("CREATING CONFIGURATION FILE AT '~/.rpl-attacks.conf'")
    with open(expanduser('~/.rpl-attacks.conf'), 'w') as f:
        f.write('[RPL Attacks Framework Configuration]\n')
        f.write('contiki_folder = {}\n'.format(contiki_folder))
        f.write('experiments_folder = {}\n'.format(experiments_folder))


@command()
def test():
    """
    Run framework's tests.
    """
    setup()
    make("test-simulation")
    with lcd(FRAMEWORK_FOLDER):
        local("python -m unittest tests")


@command()
def setup():
    """
    Setup the framework.
    """
    logger.info("SETTING UP OF THE FRAMEWORK")
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
        answer = std_input(txt)
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
@command()
def rip_my_slip():
    """
    Run a demonstration.
    """
    # TODO: prepare 'rpl-attacks' campaign, make all its experiments then run them
    print("yeah, man !")
