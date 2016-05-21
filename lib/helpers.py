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
     eventually renaming the folder to be moved. This fails silently if the source path exists.

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


    :param path:
    :param files:
    """
    for file in files:
        try:
            sh.rm(os.path.join(path, file))
        except:
            pass


def remove_folder(path):
    try:
        sh.rm('-r', path)
    except:
        pass


def render_templates(path, templates, n, blocks, duration, title, goal, notes, debug):
    # generate the list of motes (first one is the root, last one is the malicious mote)
    motes = generate_motes(int(n or NBR_MOTES))
    # fill in the different templates
    templates["motes/root.c"]["debug"] = ["DEBUG_NONE", "DEBUG_FULL"][debug or 0]
    templates["motes/sensor.c"]["debug"] = ["DEBUG_NONE", "DEBUG_FULL"][debug or 0]
    templates["motes/malicious.c"]["debug"] = ["DEBUG_NONE", "DEBUG_FULL"][debug or 0]
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
