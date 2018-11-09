# -*- coding: utf8 -*-
import hashlib
import re
import sh
import sys
import traceback
from jsmin import jsmin
from json import loads
from os import execv, execvp, geteuid, makedirs, remove
from os.path import exists, expanduser, join, split
from six import string_types
from termcolor import colored
from time import gmtime, strftime
from collections import Counter

__all__ = [
    'copy_files',
    'copy_folder',
    'hash_file',
    'is_valid_commented_json',
    'make_crash_report',
    'move_files',
    'move_folder',
    'remove_files',
    'remove_folder',
    'replace_in_file',
    'restart',
    'std_input',
]


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


# *************************************** GENERAL-PURPOSE HELPERS **************************************
def restart(to_be_removed=None):
    """
    This simple helper function allows to restart the current script, either privileged or not.

    :param to_be_removed: list of temporary files to be removed before restarting (e.g. lock or PID file)
    """
    if isinstance(to_be_removed, str):
        to_be_removed = [to_be_removed]
    if to_be_removed is not None and isinstance(to_be_removed, list):
        for f in to_be_removed:
            try:
                remove(f)
            except:
                continue
    python = [] if sys.argv[0].startswith("./") else ["python"]
    if geteuid() == 0:
        execvp("sudo", ["sudo"] + python + sys.argv)
    else:
        execv(sys.executable, python + sys.argv)


# ******************** SIMPLE INPUT HELPERS (FOR SUPPORT IN BOTH PYTHON 2.X AND 3.Y) *******************
def std_input(txt="Are you sure ? (yes|no) [default: no] ", color=None, choices=('yes', 'no', '')):
    """
    This helper function is aimed to simplify user input regarding raw_input() (Python 2.X) and input()
     (Python 3.Y).

    :param txt: text to be displayed at prompt
    :param color: to be used when displaying the prompt
    :return: user input
    """
    txt = txt if color is None else colored(txt, color)
    choices = None if not type(choices) in [list, tuple, set] or len(choices) == 0 else choices
    try:
        while True:
            try:
                user_input = raw_input(txt)
            except NameError:
                user_input = input(txt)
            if choices is None or user_input in choices:
                return user_input
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


def hash_file(filename, algo="sha1", bsize=65536):
    """
    This helper function is aimed to hash a file.

    :param path: name of the file to be hashed
    :param algo: hashing algorithm (among those implemented in hashlib)
    :param bsize: block size
    """
    h = getattr(hashlib, algo)()
    with open(filename, 'rb') as f:
        b = f.read(bsize)
        while len(b) > 0:
            h.update(b)
            b = f.read(bsize)
    return h.hexdigest()


def move_files(src_path, dst_path, *files):
    """
    This helper function is aimed to move files from a source path to a destination path.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    src_path, dst_path = __expand_folders(src_path, dst_path)
    for f in files:
        if isinstance(f, tuple):
            src, dst = f
        elif isinstance(f, string_types):
            src, dst = 2 * [f]
        else:
            continue
        src, dst = join(src_path, src), join(dst_path, dst)
        try:
            if src != dst:
                sh.mv(src, dst)
        except sh.ErrorReturnCode_1:
            pass


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


def replace_in_file(path, replacements, logger=None):
    """
    This helper function performs a line replacement in the file located at 'path'.

    :param is_debug_flag: true if method is called from apply_debug_flag. Needed only for managing logger output
    :param path: path to the file to be altered
    :param replacements: list of string pairs formatted as [old_line_pattern, new_line_replacement]
    :param logger: logger object, optional. If not none, used to output if replacement is successful
    """
    tmp = path + '.tmp'
    if isinstance(replacements[0], string_types):
        replacements = [replacements]
    regexs = []
    for replacement in replacements:
        try:
            regex = re.compile(replacement[0])
        except re.error:
            regex = None
        regexs.append(regex)
    replacements_found = []
    with open(tmp, 'w+') as nf:
        with open(path) as of:
            for line in of.readlines():
                for replacement, regex in zip(replacements, regexs):
                    # try a simple string match
                    if replacement[0] in line:
                        line = line.replace(replacement[0], "" if replacement[1] in (None, '') else replacement[1])
                        replacements_found.append(replacement[0])
                    # then try a regex match
                    else:
                        if regex is not None:
                            match = regex.search(line)
                            if match is not None:
                                try:
                                    line = line.replace(match.groups(0)[0], "" if replacement[1] in (None, '') else replacement[1])
                                    replacements_found.append(match.groups(0)[0])
                                except IndexError:
                                    line = line.replace(match.group(), replacement[1])
                                    replacements_found.append([match.group()])
                                break
                # write changed line back
                nf.write(line)
    sh.rm(path)
    sh.mv(tmp, path)
    if logger:
        c = Counter(replacements_found)
        for k in c.keys():
            logger.debug("Found and replaced {} occurrence{}: \t{} ".format(c[k], ['', 's'][c[k] > 1], k))


# **************************************** JSON-RELATED HELPER *****************************************
def is_valid_commented_json(path, return_json=False, logger=None):
    """
    This function checks if the given file path is a valid commented JSON file.

    :param path: JSON file to be checked
    :param return_json: specify whether the return value (in case of success) should be the json object or True
    :param logger: pass a logger object to log a message in case of error
    :return: True if valid file, otherwise False
    """
    try:
        # TODO: check JSON file structure
        with open(path) as f:
            content = loads(jsmin(f.read()))
        return content if return_json else True
    except ValueError:
        if logger is not None:
            logger.error("JSON file '{}' cannot be read ! (check that the syntax is correct)".format(path))
        return False


# **************************************** DEBUG-PURPOSE HELPER ****************************************
def make_crash_report(info=None, title=None, dest=".", filename="crash-report"):
    """
    This function creates a txt file and formats a simple crash report in order to facilitate debugging.

    :param info: a dictionary with additional information about the error
    :param title: title of the crash report
    :param dest: destionation folder
    :param filename: name of the crash report (MD5(current time) will be appended)
    """
    assert info is None or isinstance(info, dict)
    trace = traceback.format_exc()
    h = hashlib.new('MD5')
    h.update(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    dest = expanduser(dest)
    if not exists(dest):
        makedirs(dest)
    path = join(dest, "{}-{}.txt".format(filename, h.hexdigest()))
    with open(path, 'w') as f:
        newlines = False
        if title is not None:
            f.write("{0}\n{1}\n".format(title, len(title) * "="))
            newlines = True
        if info is not None and len(info) > 0:
            hlen = max(len(x) for x in info.keys())
            for k, v in info.items():
                f.write("\n- {0}: {1}".format(k.ljust(hlen + 1), v))
            newlines = True
        f.write(["", "\n\n"][newlines])
        f.write(trace)
