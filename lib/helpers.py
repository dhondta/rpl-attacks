# -*- coding: utf8 -*-
import ast
import logging
import sh
from os.path import join

from .decorators import expand_folder


# ********************* SIMPLE INPUT HELPERS (FOR SUPPORT IN BOTH PYTHON 2.X AND 3.Y *******************
def std_input(txt="Are you sure ? (yes|no) [default: no] "):
    """
    This helper function is aimed to simplify user input regarding raw_input() (Python 2.X) and input()
     (Python 3.Y).

    :param txt: text to be displayed at user input
    :return: user input
    """
    try:
        return raw_input(txt)
    except NameError:
        return input(txt)


# **************************************** FILE-RELATED HELPERS ****************************************
@expand_folder(2)
def copy_files(src_path, dst_path, *files):
    """
    This helper function is aimed to copy files from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    for file in files:
        if isinstance(file, tuple):
            src, dst = file
        elif isinstance(file, (str, bytes)):
            src, dst = 2 * [file]
        else:
            logging.warning("File {} was not copied from {} to {}".format(file, src_path, dst_path))
            continue
        src, dst = join(src_path, src), join(dst_path, dst)
        if src != dst:
            sh.cp(src, dst)


@expand_folder(2)
def copy_folder(src_path, dst_path):
    """
    This helper function is aimed to copy an entire folder from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    """
    if src_path != dst_path:
        sh.cp('-R', src_path, dst_path)


@expand_folder(2)
def move_files(src_path, dst_path, *files):
    """
    This helper function is aimed to move files from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    for file in files:
        if isinstance(file, tuple):
            src, dst = file
        elif isinstance(file, (str, bytes)):
            src, dst = 2 * [file]
        else:
            logging.warning("File {} was not moved from {} to {}".format(file, src_path, dst_path))
            continue
        src, dst = join(src_path, src), join(dst_path, dst)
        if src != dst:
            sh.mv(src, dst)


@expand_folder(2)
def move_folder(src_path, dst_path, new_folder_name=None):
    """
    This helper function is aimed to copy a folder from a source path to a destination path,
     eventually renaming the folder to be moved. If it fails, it does it silently.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination root path
    :param new_folder_name: new name for the source path's folder
    """
    if new_folder_name is not None:
        dst_path = join(dst_path, new_folder_name).rstrip("/")
    try:
        if src_path != dst_path:
            sh.mv(src_path, dst_path)
    except sh.ErrorReturnCode_1:
        pass


@expand_folder(1)
def remove_files(path, *files):
    """
    This helper function is aimed to remove specified files. If a file does not exist,
     it fails silently.

    :param path: absolute or relative source path
    :param files: filenames of files to be removed
    """
    for file in files:
        try:
            sh.rm(join(path, file))
        except sh.ErrorReturnCode_1:
            pass


@expand_folder(1)
def remove_folder(path):
    """
    This helper function is aimed to remove an entire folder. If the folder does not exist,
     it fails silently.

    :param path: absolute or relative source path
    """
    try:
        sh.rm('-r', path)
    except sh.ErrorReturnCode_1:
        pass


# *********************************** SIMULATION CONFIG HELPERS *************************************
@expand_folder(1)
def read_config(path, sep=' = '):
    config = {}
    try:
        with open(join(path, '.simulation.conf')) as f:
            for line in f.readlines():
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
        logging.error("Configuration file '.simulation.conf' does not exist !")
    return config


@expand_folder(1)
def write_config(path, config, sep=' = '):
    width = max([len(k) for k in config.keys()])
    with open(join(path, '.simulation.conf'), 'w') as f:
        for k, v in config.items():
            f.write('{}{}{}\n'.format(k.ljust(width), sep, v))
