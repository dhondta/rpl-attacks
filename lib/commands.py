# -*- coding: utf8 -*-
from fabric.api import hide, lcd, local, settings, sudo
from inspect import getmembers, isfunction
from os import listdir
from os.path import dirname, exists, expanduser, join, splitext
from sys import modules

from .behaviors import MultiprocessedCommand
from .constants import CONTIKI_FOLDER, COOJA_FOLDER, EXPERIMENT_FOLDER, FRAMEWORK_FOLDER, TEMPLATES_FOLDER
from .decorators import command, expand_file, report_bad_input, stderr
from .helpers import copy_files, copy_folder, move_files, move_folder, remove_files, remove_folder, \
                     std_input, read_config, write_config
from .install import check_cooja, modify_cooja, register_new_path_in_profile, \
                     update_cooja_build, update_cooja_user_properties
from .logconfig import logging, HIDDEN_ALL
from .utils import check_structure, get_experiments, get_path, list_campaigns, list_experiments, \
                   render_templates, validated_parameters

reuse_bin_path = None


def get_commands():
    return [(n, o) for n, o in getmembers(modules[__name__], isfunction) if hasattr(o, 'cmd')]


# ****************************** TASKS ON INDIVIDUAL EXPERIMENT ******************************
@report_bad_input
@command(examples=["my-simulation"], autocomplete=lambda: list_experiments())
def do_clean(name, ask=True):
    """
    Remove an experiment.

    :param name: experiment name (or absolute path to experiment)
    :param ask: ask confirmation
    """
    if not exists(join(EXPERIMENT_FOLDER, name)):
        logging.warning(" > Folder does not exist !")
    elif ask and std_input() == "yes":
        logging.debug(" > Cleaning folder...")
        with hide(*HIDDEN_ALL):
            with lcd(EXPERIMENT_FOLDER):
                local("rm -rf {}".format(name))


@report_bad_input
@command(examples=["my-simulation true"], autocomplete=lambda: list_experiments())
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


@report_bad_input
@command(examples=["my-simulation", "my-simulation target=z1 debug=true"], autocomplete=lambda: list_experiments())
def do_make(name, **kwargs):
    """
    Make a new experiment.

    :param name: experiment name
    :param kwargs: simulation keyword arguments (see the documentation for more information)
    """
    global reuse_bin_path
    if exists(join(EXPERIMENT_FOLDER, name)):
        logging.warning(" > Folder already exists !")
        if std_input("Proceed anyway ? (yes|no) [default: no] ") != "yes":
            exit(0)
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


@report_bad_input
@command(examples=["my-simulation"], autocomplete=lambda: list_experiments())
def do_remake(name):
    """
    Remake the malicious mote of an experiment.
     (meaning that it lets all simulation's files unchanged except ./motes/malicious.[target])

    :param name: experiment name
    """
    path = get_path(EXPERIMENT_FOLDER, name)
    if not exists(path):
        logging.error("Experiment '{}' does not exist !".format(name))
        exit(2)
    logging.info("REMAKING MALICIOUS MOTE FOR EXPERIMENT '{}'".format(name))
    logging.debug(" > Retrieving parameters...")
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


@report_bad_input
@command(examples=["my-simulation"], autocomplete=lambda: list_experiments(), behavior=MultiprocessedCommand)
def do_run(name):
    """
    Run an experiment.

    :param name: experiment name
    """
    path = get_path(EXPERIMENT_FOLDER, name)
    if not exists(path):
        logging.error("Experiment '{}' does not exist !".format(name))
        return False
    logging.info("PROCESSING EXPERIMENT '{}'".format(name))
    check_structure(path, remove=True)
    data, results = join(path, 'data'), join(path, 'results')
    with hide(*HIDDEN_ALL):
        for sim in ["without", "with"]:
            with lcd(path):
                logging.debug(" > Running simulation {} the malicious mote...".format(sim))
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


# ****************************** COMMANDS ON SIMULATION CAMPAIGN ******************************
@expand_file(EXPERIMENT_FOLDER, 'json')
@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
def do_drop(exp_file='experiments'):
    """
    Remove a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    if std_input() == "yes":
        logging.info("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'".format(exp_file))
        remove_files(EXPERIMENT_FOLDER, exp_file)


@expand_file(EXPERIMENT_FOLDER, 'json')
@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
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


@expand_file(EXPERIMENT_FOLDER, 'json')
@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
def do_prepare(exp_file='experiments'):
    """
    Create a campaign of experiments from a template.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    logging.info("CREATING NEW EXPERIMENT CAMPAIGN AT '{}'".format(exp_file))
    copy_files(TEMPLATES_FOLDER, dirname(exp_file), ('experiments.json', exp_file))


@expand_file(EXPERIMENT_FOLDER, 'json')
@command(examples=["my-simulation-campaign"], autocomplete=lambda: list_campaigns())
def do_run_all(exp_file="experiments"):
    """
    Run a campaign of experiments.

    :param exp_file: experiments JSON filename or basename (absolute or relative path ; if no path provided,
                     the JSON file is searched in the experiments folder)
    """
    for name in get_experiments(exp_file).keys():
        do_run(name)


# ************************************** INFORMATION COMMANDS *************************************
@command(examples=["experiments", "campaigns"], autocomplete=["campaigns", "experiments"], reexec_on_emptyline=True)
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
    logging.info("SETTING UP OF THE FRAMEWORK")
    recompile = False
    # install Cooja modifications
    if not check_cooja(COOJA_FOLDER):
        logging.debug(" > Installing Cooja add-ons...")
        # modify Cooja.java and adapt build.xml and ~/.cooja.user.properties
        modify_cooja(COOJA_FOLDER)
        update_cooja_build(COOJA_FOLDER)
        update_cooja_user_properties()
        recompile = True
    # install VisualizerScreenshot plugin in Cooja
    visualizer = join(COOJA_FOLDER, 'apps', 'visualizer_screenshot')
    if not exists(visualizer):
        logging.debug(" > Installing VisualizerScreenshot Cooja plugin...")
        copy_folder('src/visualizer_screenshot', visualizer)
        recompile = True
    # recompile Cooja for making the changes take effect
    if recompile:
        with lcd(COOJA_FOLDER):
            logging.debug(" > Recompiling Cooja...")
            with settings(warn_only=True):
                local("ant clean")
                local("ant jar")
    else:
        logging.debug(" > Cooja is up-to-date")
    # install imagemagick
    with hide(*HIDDEN_ALL):
        imagemagick_apt_output = local('apt-cache policy imagemagick', capture=True)
        if 'Unable to locate package' in imagemagick_apt_output:
            logging.debug(" > Installing imagemagick package...")
            sudo("apt-get install imagemagick -y &")
        else:
            logging.debug(" > Imagemagick is installed")
    # install msp430 (GCC) upgrade
    with hide(*HIDDEN_ALL):
        msp430_version_output = local('msp430-gcc --version', capture=True)
    if 'msp430-gcc (GCC) 4.7.0 20120322' not in msp430_version_output:
        txt = "In order to extend msp430x memory support, it is necessary to upgrade msp430-gcc.\n" \
              "Would you like to upgrade it now ? (yes|no) [default: no] "
        answer = std_input(txt)
        if answer == "yes":
            logging.debug(" > Upgrading msp430-gcc from version 4.6.3 to 4.7.0...")
            logging.warning("If you encounter problems with this upgrade, please refer to:\n"
                            "https://github.com/contiki-os/contiki/wiki/MSP430X")
            with lcd('src/'):
                logging.warning(" > Upgrade now starts, this may take up to 30 minutes...")
                sudo('./upgrade-msp430.sh')
                sudo('rm -r tmp/')
                local('export PATH=/usr/local/msp430/bin:$PATH')
                register_new_path_in_profile()
        else:
            logging.warning("Upgrade of library msp430-gcc aborted")
            logging.warning("You may experience problems of mote memory size at compilation")
    else:
        logging.debug(" > Library msp430-gcc is up-to-date (version 4.7.0)")


# **************************************** MAGIC COMMAND ****************************************
@command()
def do_rip_my_slip():
    """
    Run a demonstration.
    """
    # TODO: prepare 'rpl-attacks' campaign, make all its experiments then run them
    print("yeah, man !")
