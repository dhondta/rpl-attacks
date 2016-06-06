# -*- coding: utf8 -*-
import ast
import re
import sh
from os import makedirs
from os.path import exists, expanduser, join, split
from six import string_types
from termcolor import colored

from .logconfig import logger


def __expand_folders(*folders):
    """
    This private function expands folder paths if these are in the form of a tuple.

    :param folders: tuples to be joined and expanded as paths
    :return: the expanded paths
    """
    paths = []
    for folder in folders:
        if isinstance(folder, (tuple, list)):
            path = join(*folder)
        else:
            path = folder
        paths.append(expanduser(path))
    return paths[0] if len(paths) == 1 else paths


# ********************* SIMPLE INPUT HELPERS (FOR SUPPORT IN BOTH PYTHON 2.X AND 3.Y *******************
def std_input(txt="Are you sure ? (yes|no) [default: no] ", color=None):
    """
    This helper function is aimed to simplify user input regarding raw_input() (Python 2.X) and input()
     (Python 3.Y).

    :param txt: text to be displayed at prompt
    :param color: to be used when displaying the prompt
    :return: user input
    """
    txt = txt if color is None else colored(txt, color)
    try:
        try:
            return raw_input(txt)
        except NameError:
            return input(txt)
    except KeyboardInterrupt:
        print('')
        return ''


# **************************************** FILE-RELATED HELPERS ****************************************
def copy_files(src_path, dst_path, *files):
    """
    This helper function is aimed to copy files from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    src_path, dst_path = __expand_folders(src_path, dst_path)
    for file in files:
        if isinstance(file, tuple):
            src, dst = file
        elif isinstance(file, string_types):
            src, dst = 2 * [file]
        else:
            logger.warning("File {} was not copied from {} to {}".format(file, src_path, dst_path))
            continue
        src, dst = join(src_path, src), join(dst_path, dst)
        if src != dst:
            sh.cp(src, dst)


def copy_folder(src_path, dst_path, includes=None):
    """
    This helper function is aimed to copy an entire folder from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param includes: list of sub-folders and files to be included from the src_path and to be copied into dst_path
    """
    src_path, dst_path = __expand_folders(src_path, dst_path)
    if src_path != dst_path:
        if includes is not None:
            dst_path = join(dst_path, split(src_path)[-1])
            if not exists(dst_path):
                makedirs(dst_path)
            for include in includes:
                head, tail = split(include)
                sub_dst_path = join(dst_path, head)
                if not exists(sub_dst_path):
                    makedirs(sub_dst_path)
                sh.cp('-R', join(src_path, include), sub_dst_path)
        else:
            sh.cp('-R', src_path, dst_path)


def move_files(src_path, dst_path, *files):
    """
    This helper function is aimed to move files from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    src_path, dst_path = __expand_folders(src_path, dst_path)
    for file in files:
        if isinstance(file, tuple):
            src, dst = file
        elif isinstance(file, string_types):
            src, dst = 2 * [file]
        else:
            logger.warning("File {} was not moved from {} to {}".format(file, src_path, dst_path))
            continue
        src, dst = join(src_path, src), join(dst_path, dst)
        if src != dst:
            sh.mv(src, dst)


def move_folder(src_path, dst_path, new_folder_name=None):
    """
    This helper function is aimed to copy a folder from a source path to a destination path,
     eventually renaming the folder to be moved. If it fails, it does it silently.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination root path
    :param new_folder_name: new name for the source path's folder
    """
    src_path, dst_path = __expand_folders(src_path, dst_path)
    if new_folder_name is not None:
        dst_path = join(dst_path, new_folder_name).rstrip("/")
    try:
        if src_path != dst_path:
            sh.mv(src_path, dst_path)
    except sh.ErrorReturnCode_1:
        pass


def remove_files(path, *files):
    """
    This helper function is aimed to remove specified files. If a file does not exist,
     it fails silently.

    :param path: absolute or relative source path
    :param files: filenames of files to be removed
    """
    path = __expand_folders(path)
    for file in files:
        try:
            sh.rm(join(path, file))
        except sh.ErrorReturnCode_1:
            pass


def remove_folder(path):
    """
    This helper function is aimed to remove an entire folder. If the folder does not exist,
     it fails silently.

    :param path: absolute or relative source path
    """
    path = __expand_folders(path)
    try:
        sh.rm('-r', path)
    except sh.ErrorReturnCode_1:
        pass


def replace_in_file(path, replacement):
    """
    This helper function performs a line replacement in the file located at 'path'.

    :param path: path to the file to be altered
    :param replacement: list of two strings formatted as [old_line_pattern, new_line_replacement]
    """
    tmp = path + '.tmp'
    try:
        regex = re.compile(replacement[0])
    except re.error:
        regex = None
    with open(tmp, 'w+') as nf:
        with open(path) as of:
            for line in of.readlines():
                if regex is not None:
                    match = regex.search(line)
                    if match is not None:
                        try:
                            line = line.replace(match.groups(0)[0], replacement[1])
                        except IndexError:
                            line = line.replace(match.group(), replacement[1])
                elif replacement[0] in line:
                    line = line.replace(replacement[0], replacement[1])
                nf.write(line)
    sh.rm(path)
    sh.mv(tmp, path)


# *********************************** SIMULATION CONFIG HELPERS *************************************
def read_config(path, sep=' = '):
    """
    This helper function reads a simple configuration file with the following format:

     max_range = 50.0
     repeat    = 1
     blocks    = []
     goal      = ""
     ...

    :param path: path to the configuration file
    :param sep: separator between the key and the value
    :return: dictionary with the whole configuration
    """
    config = {}
    try:
        with open(join(path, 'simulation.conf')) as f:
            for line in f.readlines():
                if line.strip().startswith('#'):
                    continue
                try:
                    k, v = [x.strip() for x in line.split(sep)]
                except ValueError:
                    continue
                try:
                    v = ast.literal_eval(v)
                except ValueError:
                    pass
                config[k] = v
    except OSError:
        logger.error("Configuration file 'simulation.conf' does not exist !")
    return config


def write_config(path, config, sep=' = '):
    """
    This helper function saves a simple configuration file.

    :param path: path to the configuration file
    :param config: dictionary with the whole configuration
    :param sep: separator between the key and the value
    """
    width = max([len(k) for k in config.keys()])
    with open(join(path, 'simulation.conf'), 'w') as f:
        for k, v in sorted(config.items(), key=lambda x: x[0]):
            f.write('{}{}{}\n'.format(k.ljust(width), sep, ['{}', '"{}"'][isinstance(v, string_types)].format(v)))
