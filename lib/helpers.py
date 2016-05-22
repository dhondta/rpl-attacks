# -*- coding: utf8 -*-
import logging
import sh

from functools import wraps
from os.path import dirname, join


# **************************************** PATH-RELATED DECORATORS ****************************************
def expand_file(inside=None, ensure_ext=None):
    """
    This decorator expands the path to the specified filename. If this filename is not already a path,
     expand it to specified folder 'inside'. If an extension is to be ensured, check and add it if relevant.

    :param fn: input filename
    :param inside: folder to expand in order to build filename's path (if not already specified in filename)
    :param ensure_ext: extension to be ensured for the file
    :return: the actual path to the specified filename
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fn = args[0]
            if dirname(fn) == '':
                fn = join(inside, fn)
            if ensure_ext and not fn.endswith("." + ensure_ext):
                fn += "." + ensure_ext
            args = (fn,) + args[1:]
            return f(*args, **kwargs)
        return wrapper
    return decorator


def expand_folder(nargs):
    """
    This decorator expands folder paths (up to the nth arguments) if these are in the form
     of a tuple.

    :param nargs: number of heading arguments on which the wrapper is to be applied
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            margs = []
            for i in range(nargs):
                if isinstance(args[i], (tuple, list)):
                    margs.append(join(*args[i]))
                else:
                    margs.append(args[i])
            args = tuple(margs) + args[nargs:]
            return f(*args, **kwargs)
        return wrapper
    return decorator


# **************************************** FILE-RELATED HELPERS ****************************************
@expand_folder(2)
def copy_files(src_path, dst_path, *files):
    """
    This helper function is aimed to copy files from a source path to a destination path

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    for file in files:
        if isinstance(file, tuple):
            src, dst = file
        elif isinstance(file, [str, bytes]):
            src, dst = 2 * [file]
        else:
            logging.warning("File {} was not copied from {} to {}".format(file, src_path, dst_path))
            continue
        sh.cp(join(src_path, src), join(dst_path, dst))


@expand_folder(2)
def copy_folder(src_path, dst_path):
    """
    This helper function is aimed to copy an entire folder from a source path to a destination path

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    """
    sh.cp('-R', src_path, dst_path)


@expand_folder(2)
def move_folder(src_path, dst_path, new_folder_name=None):
    """
    This helper function is aimed to copy a folder from a source path to a destination path,
     eventually renaming the folder to be moved. If it fails, it does it silently.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination root path
    :param new_folder_name: new name for the source path's folder
    """
    src_path = join(*src_path) if isinstance(src_path, (tuple, list)) else src_path
    dst_path = join(*dst_path) if isinstance(dst_path, (tuple, list)) else dst_path
    if new_folder_name is not None:
        dst_path = join(dst_path, new_folder_name).rstrip("/")
    try:
        sh.mv(src_path, dst_path)
    except:
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
        except:
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
    except:
        pass
