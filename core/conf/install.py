# -*- coding: utf8 -*-
from os.path import exists, expanduser, join

from core.conf.logconfig import logger


__all__ = [
    'check_cooja',
    'modify_cooja',
    'modify_rpl_debug',
    'register_new_path_in_profile',
    'update_cooja_build',
    'update_cooja_user_properties',
]


def check_cooja(cooja_dir):
    """
    This function checks if Cooja.java already contains the required modification.

    :param cooja_dir: Cooja's directory
    :return: True if the modification is present else False
    """
    pattern = 'if (args.length > 0 && args[0].startsWith("-hidden="))'
    with open(join(cooja_dir, 'java', 'org', 'contikios', 'cooja', 'Cooja.java')) as f:
        source = f.read()
    for line in source.split('\n'):
        if pattern in line:
            return True
    return False


def modify_cooja(cooja_dir):
    """
    This function inserts a block in the IF statement for parsing Cooja's input arguments.
    It searches for the IF statement pattern containing the '-nogui' case and inserts
     an IF block for a new '-hidden' case (aimed to run a simulation with the GUI hidden).

    :param cooja_dir: Cooja's directory
    :return: None
    """
    pattern = 'if (args.length > 0 && args[0].startsWith("-nogui="))'
    cooja_file = join(cooja_dir, 'java', 'org', 'contikios', 'cooja', 'Cooja.java')
    changed = False
    with open(cooja_file) as f:
        source = f.read()
    buffer = []
    for line in source.split('\n'):
        if pattern in line:
            with open('src/Cooja.java.snippet') as f:
                line = line.replace(pattern, '{} else {}'.format(f.read().strip(), pattern))
            changed = True
        buffer.append(line)
    with open(cooja_file, 'w') as f:
        f.write('\n'.join(buffer))
    logger.debug(" > Cooja.java modified" if changed else " > Cooja.java already up-to-date")


def modify_rpl_debug(contiki_dir):
    """
    This function checks and modifies, if necessary, the DEBUG constant in
     [CONTIKI]/core/net/ipv6/uip-ds6-route.c in order to enable mote relationships logging.
     This is required for the script.js used in Cooja simulations to catch relationships
     evolution and to plot the sensor network in an animated GIF.

    :param contiki_dir: Contiki's directory
    :return: None
    """
    pattern = '#define DEBUG DEBUG_NONE'
    for module, descr in zip([('ipv6', 'uip-ds6-route.c'), ('rpl', 'rpl.c')], ["IPv6", "RPL"]):
        filepath = join(contiki_dir, 'core', 'net', *module)
        changed = False
        with open(filepath) as f:
            source = f.read()
        buffer = []
        for line in source.split('\n'):
            if pattern in line:
                buffer.append(line.replace(pattern, '#define DEBUG DEBUG_ANNOTATE'))
                changed = True
            else:
                buffer.append(line)
        with open(filepath, 'w') as f:
            f.write('\n'.join(buffer))
        logger.debug((" > {} debug modified" if changed else " > {} debug already up-to-date").format(descr))


def register_new_path_in_profile():
    """
    This function appends PATH adaptation to user's .profile for support of the last version of msp430-gcc.

    :return: None
    """
    msp430_path_adapted = False
    with open(expanduser('~/.profile')) as f:
        for line in f.readlines():
            if 'export PATH=/usr/local/msp430/bin:$PATH' in line:
                msp430_path_adapted = True
    if not msp430_path_adapted:
        with open(expanduser('~/.profile'), 'a') as f:
            f.write("\n\n# msp430-gcc (GCC) 4.6.3\n# export PATH=/usr/bin/msp430-gcc/bin:$PATH\n"
                    "# msp430-gcc (GCC) 4.7.0\nexport PATH=/usr/local/msp430/bin:$PATH")
    logger.debug(" > PATH adapted for msp430-gcc (GCC) 4.7.0 support")


def update_cooja_build(cooja_dir):
    """
    This function adds a line for the 'visualizer_screenshot' plugin in the 'clean' and 'jar' sections
     of Cooja's build.xml.

    :param cooja_dir: Cooja's directory
    :return: None
    """
    cooja_build = join(cooja_dir, 'build.xml')
    with open(cooja_build) as f:
        source = f.read()
    buffer, tmp, is_in_jar_block, is_in_clean_block = [], [], False, False
    for line in source.split('\n'):
        if '<target name="clean" depends="init">' in line:
            is_in_clean_block = True
        elif '<target name="jar" depends="jar_cooja">' in line:
            is_in_jar_block = True
        if (is_in_clean_block or is_in_jar_block) and '"apps/visualizer_screenshot"' in line:
            return
        # if in 'clean' block, collect '<delete dir=...' lines in a buffer, add the required line then re-append buffer
        if is_in_clean_block and '</target>' in line:
            while buffer[-1].strip().startswith('<delete dir='):
                tmp.append(buffer.pop())
            buffer.append('    <ant antfile="build.xml" dir="apps/visualizer_screenshot"'
                          ' target="clean" inheritAll="false"/>')
            is_in_clean_block = False
            while len(tmp) > 0:
                buffer.append(tmp.pop())
        # if in 'jar' block, just put the required line at the end of the block
        elif is_in_jar_block and '</target>' in line:
            buffer.append('    <ant antfile="build.xml" dir="apps/visualizer_screenshot"'
                          ' target="jar" inheritAll="false"/>')
            is_in_jar_block = False
        buffer.append(line)
    with open(cooja_build, 'w') as f:
        f.write('\n'.join(buffer))
    logger.debug(" > Cooja's build.xml modified")


def update_cooja_user_properties():
    """
    This function updates ~/.cooja.user.properties to include 'visualizer_screenshot' plugin

    :return: None
    """
    cooja_user_properties = join(expanduser('~'), '.cooja.user.properties')
    # if it does not exist, create it from 'src' folder's template
    if not exists(cooja_user_properties):
        with open('src/cooja-user-properties') as tf:
            with open(cooja_user_properties, 'w') as nf:
                nf.write(tf.read())
        logger.debug(" > Cooja user properties created")
        return
    # if it exists, append plugin's reference inside
    with open(cooja_user_properties) as f:
        source = f.read()
    buffer, plugin_appended = [], False
    for line in source.split('\n'):
        if line.startswith('DEFAULT_PROJECTDIRS='):
            if '[APPS_DIR]/visualizer_screenshot' in line:
                return
            else:
                plugin_appended = True
                line += ';[APPS_DIR]/visualizer_screenshot'
        buffer.append(line)
    # if the line with the correct constant name was not found, create it from 'src' folder's template
    if not plugin_appended:
        with open('src/cooja-user-properties') as f:
            for line in f.readlines():
                if 'DEFAULT_PROJECTDIRS=' in line:
                    buffer.append(line)
                    break
    # then write the modified .cooja.user.properties
    with open(cooja_user_properties, 'w') as f:
        f.write('\n'.join(buffer))
    logger.debug(" > Cooja user properties modified")
