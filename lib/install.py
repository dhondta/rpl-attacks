# -*- coding: utf8 -*-
import os


def modify_cooja(cooja_dir):
    """
    This function inserts a block in the IF statement for parsing Cooja's input arguments.
    It searches for the IF statement pattern containing the '-nogui' case and insterts
     an IF block for a new '-test' case (aimed to run a simulation with the GUI hidden).

    :param cooja_dir: Cooja's directory
    :return: None
    """
    pattern = 'if (args.length > 0 && args[0].startsWith("-nogui="))'
    cooja_file = os.path.join(cooja_dir, 'java', 'org', 'contikios', 'cooja', 'Cooja.java')
    with open('src/Cooja.java.snippet') as f:
        code = f.read().strip()
    with open(cooja_file) as f:
        source = f.read()
    buffer = []
    for line in source.split('\n'):
        if 'if (args.length > 0 && args[0].startsWith("-test="))' in line:
            return
        if pattern in line:
            line = line.replace(pattern, '{} else {}'.format(code, pattern))
        buffer.append(line)
    with open(cooja_file, 'w') as f:
        f.write('\n'.join(buffer))


def update_cooja_build(cooja_dir):
    """
    This function adds a line for the 'visualizer_screenshot' plugin in the 'clean' and 'jar' sections
     of Cooja's build.xml.

    :param cooja_dir: Cooja's directory
    :return: None
    """
    cooja_build = os.path.join(cooja_dir, 'build.xml')
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
        if is_in_clean_block and '</target>' in line:
            while buffer[-1].strip().startswith('<delete dir='):
                tmp.append(buffer.pop())
            buffer.append('    <ant antfile="build.xml" dir="apps/visualizer_screenshot" target="clean" inheritAll="false"/>')
            while len(tmp) > 0:
                buffer.append(tmp.pop())
        elif is_in_jar_block and '</target>' in line:
            buffer.append('    <ant antfile="build.xml" dir="apps/visualizer_screenshot" target="jar" inheritAll="false"/>')
        buffer.append(line)
    with open(cooja_build, 'w') as f:
        f.write('\n'.join(buffer))


def update_cooja_user_properties():
    """
    This function updates ~/.cooja.user.properties to include 'visualizer_screenshot' plugin

    :return: None
    """
    cooja_user_properties = os.path.join(os.path.expanduser('~'), '.cooja.user.properties')
    with open(cooja_user_properties) as f:
        source = f.read()
    buffer = []
    for line in source.split('\n'):
        if line.startswith('DEFAULT_PROJECTDIRS='):
            if '[APPS_DIR]/visualizer_screenshot' in line:
                return
            else:
                line += ';[APPS_DIR]/visualizer_screenshot'
        buffer.append(line)
    with open(cooja_user_properties, 'w') as f:
        f.write('\n'.join(buffer))
