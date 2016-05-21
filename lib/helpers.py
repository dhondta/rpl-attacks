# -*- coding: utf8 -*-
import copy
import logging
import os
import sh

from . import NBR_MOTES, TEMPLATE_ENV
from .utils import generate_motes, get_constants


def copy_files(src_path, dst_path, *files):
    """
    This helper function is aimed to copy files from a source path to a destination path

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    :param files: tuples with the following format (source_filename, destination_filename)
    """
    for src, dst in files:
        sh.cp(os.path.join(src_path, src), os.path.join(dst_path, dst))


def copy_folder(src_path, dst_path):
    """
    This helper function is aimed to copy an entire folder from a source path to a destination path

    :param src_path: absolute or relative source path
    :param dst_path: absolute or relative destination path
    """
    sh.cp(src_path, dst_path)


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


def render_templates(path, templates, n, blocks, duration, title, goal, notes):
    """
    This function is aimed to adapt the input templates dictionary with provided parameters.

    :param path: experiment folder path
    :param templates: dictionary of the templates to be deployed
    :param n: number of motes
    :param blocks: build blocks to be included in the current experiment
    :param duration: duration of the simulation
    :param title: title of the simulation
    :param goal: goal description for the simulation
    :param notes: additional notes for the simulation
    """
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = generate_motes(int(n or NBR_MOTES))
    # fill in the different templates
    templates["motes/malicious.c"]["constants"] = "\n".join(["#define {} {}".format(*c) for c in get_constants(blocks).items()]) or ""
    templates["script.js"]["timeout"] = 1000 * int(duration or templates["script.js"]["timeout"])
    templates["script.js"]["sampling_period"] = templates["script.js"]["timeout"] // 100
    simulation_template = templates.pop("simulation.csc")
    simulation_template["title"] = title or simulation_template["title"]
    simulation_template["goal"] = goal or simulation_template["goal"]
    simulation_template["notes"] = notes or simulation_template["notes"]
    templates["simulation_with_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_with_malicious.csc"]["motes"] = motes
    templates["simulation_without_malicious.csc"] = copy.deepcopy(simulation_template)
    templates["simulation_without_malicious.csc"]["motes"] = motes[:-1]
    del templates["simulation_without_malicious.csc"]["mote_types"][-1]  # remove malicious mote
    for template_name, kwargs in templates.items():
        logging.debug(" > Setting template file: {}".format(template_name))
        template = TEMPLATE_ENV.get_template(template_name).render(**kwargs)
        with open(os.path.join(path, template_name), "w") as f:
            f.write(template)
