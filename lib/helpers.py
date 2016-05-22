# -*- coding: utf8 -*-
import logging
import os
import sh


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
        sh.cp(os.path.join(src_path, src), os.path.join(dst_path, dst))


def copy_folder(src_path, dst_path):
    """
    This helper function is aimed to copy an entire folder from a source path to a destination path

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    """
    sh.cp('-R', src_path, dst_path)


def move_folder(src_path, dst_path, new_folder_name=None):
    """
    This helper function is aimed to copy a folder from a source path to a destination path,
     eventually renaming the folder to be moved. If it fails, it does it silently.

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination root path
    :param new_folder_name: new name for the source path's folder
    """
    if new_folder_name is not None:
        dst_path = os.path.join(dst_path, new_folder_name).rstrip("/")
    try:
        sh.mv(src_path, dst_path)
    except:
        pass


def remove_files(path, *files):
    """
    This helper function is aimed to remove specified files. If a file does not exist,
     it fails silently.

    :param path: absolute or relative source path
    :param files: filenames of files to be removed
    """
    for file in files:
        try:
            sh.rm(os.path.join(path, file))
        except:
            pass


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
