# -*- coding: utf8 -*-
from fabric.api import hide, lcd, local, settings, sudo
from inspect import getmembers, isfunction
from os import listdir
from os.path import dirname, exists, expanduser, isdir, join
from sys import modules

from .constants import CONTIKI_FOLDER, COOJA_FOLDER, EXPERIMENT_FOLDER, FRAMEWORK_FOLDER, TEMPLATES_FOLDER
from .decorators import command, expand_file, report_bad_input, stderr
from .helpers import copy_files, copy_folder, move_folder, read_config, remove_files, remove_folder, \
                     std_input, write_config
from .install import check_cooja, modify_cooja, register_new_path_in_profile, \
                     update_cooja_build, update_cooja_user_properties
from .logconfig import logging, HIDDEN_ALL
from .utils import check_structure, get_experiments, get_path, list_campaigns, list_experiments, \
                   render_templates, validated_parameters

reuse_bin_path = None


def get_commands():
    return [(n, o) for n, o in getmembers(modules[__name__], isfunction) if hasattr(o, 'cmd')]


# ****************************** TASKS ON INDIVIDUAL EXPERIMENT ******************************
@command(examples=["my-simulation"], autocomplete=lambda: list_experiments())
@report_bad_input
def do_clean(name, ask=True):
    """
    Remove an experiment.

    :param name: experiment name (or absolute path to experiment)
    :param ask: ask confirmation
    """
    if not exists(join(EXPERIMENT_FOLDER, name)):
        logging.debug(" > Folder does not exist !")
    elif ask and std_input() == "yes":
        logging.debug(" > Cleaning folder...")
        with hide(*HIDDEN_ALL):
            with lcd(EXPERIMENT_FOLDER):
                local("rm -rf {}".format(name))


@command(examples=["my-simulation true"], autocomplete=lambda: list_experiments())
@report_bad_input
def do_cooja(name, with_malicious=False):
    """
    Start an experiment in Cooja with/without the malicious mote.

    :param name: experiment name
    :param with_malicious: use the simulation WITH the malicious mote or not
    """
    logging.info("STARTING COOJA WITH EXPERIMENT '{}'".format(name))
    path = get_path(EXPERIMENT_FOLDER, name)
    get_path(EXPERIMENT_FOLDER, name, 'data')
    with hide(*HIDDEN_ALL):
        with lcd(path):
            local("make cooja-with{}-malicious".format("" if with_malicious else "out"))


@command(examples=["my-simulation", "my-simulation target=z1 debug=true"], autocomplete=lambda: list_experiments())
@report_bad_input
def do_make(name, **kwargs):
    """
    Make a new experiment.

    :param name: experiment name
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
    if exists(join(EXPERIMENT_FOLDER, name)):
        logging.debug(" > Folder already exists !")
        if std_input("Proceed anyway ? (yes|no) [default: no] ") != "yes":
            return
    logging.info("CREATING EXPERIMENT '{}'".format(name))
    logging.debug(" > Validating parameters...")
    params = validated_parameters(kwargs)
    ext_lib = params.get("ext_lib")
    logging.debug(" > Creating simulation...")
    # create experiment's directories and config file
    path = get_path(EXPERIMENT_FOLDER, name, create=True)
    get_path(EXPERIMENT_FOLDER, name, 'motes', create=True)
    get_path(EXPERIMENT_FOLDER, name, 'data', create=True)
    get_path(EXPERIMENT_FOLDER, name, 'results', create=True)
    write_config(path, params)
    # select the right malicious mote template and duplicate the simulation file
    copy_files(TEMPLATES_FOLDER, TEMPLATES_FOLDER,
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'),
               ('simulation.csc', 'simulation_without_malicious.csc'),
               ('simulation.csc', 'simulation_with_malicious.csc'))
    # create experiment's files from templates
    render_templates(path, **params)
    # then clean the templates folder from previously created files
    remove_files(TEMPLATES_FOLDER,
                 'motes/malicious.c',
                 'simulation_without_malicious.csc',
                 'simulation_with_malicious.csc')
    if ext_lib and not exists(ext_lib):
        logging.error("External library does not exist !")
        logging.critical("Make aborded.")
        exit(2)
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with lcd(path):
            # for every simulation, root and sensor compilation is the same ;
            #  then, if these were not previously compiled, proceed
            if reuse_bin_path is None or reuse_bin_path == path:
                logging.debug(" > Making 'root.{}'...".format(params["target"]))
                stderr(local)("make motes/root TARGET={}".format(params["target"]), capture=True)
                logging.debug(" > Making 'sensor.{}'...".format(params["target"]))
                stderr(local)("make motes/sensor TARGET={}".format(params["target"]), capture=True)
                # after compiling, clean artifacts
                remove_files(path,
                             'contiki-{}.a'.format(params["target"]),
                             'contiki-{}.map'.format(params["target"]),
                             'symbols.c',
                             'symbols.h',
                             'motes/root.c',
                             'motes/sensor.c')
                remove_folder((path, 'obj_{}'.format(params["target"])))
                reuse_bin_path = path
            # otherwise, reuse them by copying the compiled files to the current experiment folder
            else:
                copy_files(reuse_bin_path, path, "motes/root.{}".format(params["target"]),
                           "motes/sensor.{}".format(params["target"]))
            # now, handle the malicious mote compilation
            if ext_lib is not None:
                # backup original RPL library and replace it with attack's library
                get_path('.tmp')
                move_folder((CONTIKI_FOLDER, 'core', 'net', 'rpl'), '.tmp')
                copy_folder(ext_lib, (CONTIKI_FOLDER, 'core', 'net', 'rpl'))
            logging.debug(" > Making 'malicious.{}'...".format(params["target"]))
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


@command(examples=["my-simulation"], autocomplete=lambda: list_experiments())
@report_bad_input
def do_remake(name):
    """
    Remake the malicious mote of an experiment.
     (meaning that it lets all simulation's files unchanged except ./motes/malicious.[target])

    :param name: experiment name
    """
    logging.info("REMAKING MALICIOUS MOTE FOR EXPERIMENT '{}'".format(name))
    logging.debug(" > Retrieving parameters...")
    path = get_path(EXPERIMENT_FOLDER, name)
    params = read_config(path)
    ext_lib = params.get("ext_lib")
    logging.debug(" > Recompiling malicious mote...")
    # remove former compiled malicious mote and prepare the template
    remove_files('motes/malicious.c')
    copy_files(TEMPLATES_FOLDER, TEMPLATES_FOLDER,
               ('motes/malicious-{}.c'.format(params["mtype"]), 'motes/malicious.c'))
    # recreate malicious C file from template and clean the temporary template
    render_templates(path, True, **params)
    remove_files(TEMPLATES_FOLDER, 'motes/malicious.c')
    if ext_lib and not exists(ext_lib):
        logging.error("External library does not exist !")
        logging.critical("Make aborded.")
        exit(2)
    with settings(hide(*HIDDEN_ALL), warn_only=True):
        with lcd(path):
            # handle the malicious mote recompilation
            if ext_lib is not None:
                # backup original RPL library and replace it with attack's library
                get_path('.tmp')
                move_folder((CONTIKI_FOLDER, 'core', 'net', 'rpl'), '.tmp')
                copy_folder(ext_lib, (CONTIKI_FOLDER, 'core', 'net', 'rpl'))
            logging.debug(" > Making 'malicious.{}'...".format(params["target"]))
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


@command(examples=["my-simulation"], autocomplete=lambda: list_experiments())
@report_bad_input
def do_run(name):
    """
    Run an experiment.

    :param name: experiment name
    """
    logging.info("PROCESSING EXPERIMENT '{}'".format(name))
    path = get_path(EXPERIMENT_FOLDER, name)
    with hide(*HIDDEN_ALL):
        with lcd(path):
            logging.debug(" > Running both simulations (with and without the malicious mote)...")
            local("make run-without-malicious")
            local("make run-with-malicious")
        remove_files(path,
                     'COOJA.log',
                     'COOJA.testlog')


# ****************************** COMMANDS ON SIMULATION CAMPAIGN ******************************
@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
@expand_file(EXPERIMENT_FOLDER, 'json')
def do_drop(exp_file='experiments'):
    """
    Remove a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    if std_input() == "yes":
        logging.info("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'".format(exp_file))
        remove_files(EXPERIMENT_FOLDER, exp_file)


@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
@expand_file(EXPERIMENT_FOLDER, 'json')
def do_make_all(exp_file="experiments"):
    """
    Make a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    global reuse_bin_path
    for name, params in get_experiments(exp_file).items():
        do_clean(name, ask=False)
        do_make(name, **params)


@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
@expand_file(EXPERIMENT_FOLDER, 'json')
def do_prepare(exp_file='experiments'):
    """
    Create a campaign of experiments from a template.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    logging.info("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'".format(exp_file))
    copy_files(TEMPLATES_FOLDER, dirname(exp_file), ('experiments.json', exp_file))


@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
@expand_file(EXPERIMENT_FOLDER, 'json')
def do_run_all(exp_file="experiments"):
    """
    Run a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    for name in get_experiments(exp_file).keys():
        do_run(name)


# ************************************** INFORMATION COMMANDS *************************************
@command(examples=["experiments", "campaigns"], autocomplete=["campaigns", "experiments"])
def do_list(item_type=None):
    """
    List all available items of a specified type.

    :param item_type: experiment/campaign
    """
    if item_type == 'experiments':
        print('Available experiments:')
        for e in list_experiments():
            print(' - {}'.format(e))
    elif item_type == 'campaigns':
        print('Available campaigns:')
        for c in list_campaigns():
            print(' - {}'.format(c))


# ***************************************** SETUP COMMANDS *****************************************
@command(examples=["/opt/contiki", "~/contiki ~/Documents/experiments"])
def do_config(contiki_folder='~/contiki', experiments_folder='~/Experiments'):
    """
    Create a new configuration file at `~/.rpl-attacks.conf`.

    :param contiki_folder: Contiki folder
    :param experiments_folder: experiments folder
    """
    logging.info("CREATING CONFIGURATION FILE AT '~/.rpl-attacks.conf'")
    with open(expanduser('~/.rpl-attacks.conf'), 'w') as f:
        f.write('[RPL Attacks Framework Configuration]\n')
        f.write('contiki_folder = {}\n'.format(contiki_folder))
        f.write('experiments_folder = {}\n'.format(experiments_folder))
do_config.description = "Create a configuration file at ~/.rpl-attacks.conf for RPL Attacks Framework."


@command()
def do_test():
    """
    Run framework's tests.
    """
    do_setup()
    do_make("test-simulation")
    with lcd(FRAMEWORK_FOLDER):
        local("python -m unittest tests")


@command()
def do_setup():
    """
    Setup the framework.
    """
    # install Cooja modifications
    if not check_cooja(COOJA_FOLDER):
        logging.info("INSTALLING COOJA ADD-ONS")
        # modify Cooja.java and adapt build.xml and ~/.cooja.user.properties
        modify_cooja(COOJA_FOLDER)
        update_cooja_build(COOJA_FOLDER)
        update_cooja_user_properties()
        # install VisualizerScreenshot plugin in Cooja
        visualizer = join(COOJA_FOLDER, 'apps', 'visualizer_screenshot')
        if not exists(visualizer):
            logging.debug(" > Installing VisualizerScreenshot Cooja plugin...")
            copy_folder('src/visualizer_screenshot', visualizer)
        # recompile Cooja for making the changes take effect
        with lcd(COOJA_FOLDER):
            logging.debug(" > Recompiling Cooja...")
            with settings(warn_only=True):
                local("ant clean")
                local("ant jar")
    else:
        logging.info("COOJA IS UP-TO-DATE")
    # install msp430 (GCC) upgrade
    with hide(*HIDDEN_ALL):
        msp430_version_output = local('msp430-gcc --version', capture=True)
    if 'msp430-gcc (GCC) 4.7.0 20120322' not in msp430_version_output:
        txt = "In order to extend msp430x memory support, it is necessary to upgrade msp430-gcc.\n" \
              "Would you like to upgrade it now ? (yes|no) [default: no] "
        answer = std_input(txt)
        if answer == "yes":
            logging.info("UPGRADING msp430-gcc FROM VERSION 4.6.3 TO 4.7.0")
            logging.warning("If you encounter problems with this upgrade, please refer to:\n"
                            "https://github.com/contiki-os/contiki/wiki/MSP430X")
            with lcd('src/'):
                logging.warning(" > Upgrade now starts, this may take up to 30 minutes...")
                sudo('./upgrade-msp430.sh')
                sudo('rm -r tmp/')
                local('export PATH=/usr/local/msp430/bin:$PATH')
                register_new_path_in_profile()
        else:
            logging.info("UPGRADE OF LIBRARY msp430-gcc ABORTED")
            logging.warning("You may experience problems of mote memory size at compilation")
    else:
        logging.info("LIBRARY msp430-gcc IS UP-TO-DATE (4.7.0)")


# **************************************** MAGIC COMMAND ****************************************
@command()
def do_rip_my_slip():
    """
    Run a demonstration.
    """
    # TODO: prepare 'rpl-attacks' campaign, make all its experiments then run them
    print("yeah, man !")
