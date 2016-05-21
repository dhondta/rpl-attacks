# -*- coding: utf8 -*-
import json
import logging
import math
import os
import random

from . import NBR_MOTES, MAX_XY_POSITION, MIN_DIST_BETWEEN_MOTES, MAX_DIST_BETWEEN_MOTES


# **************************************** PROTECTED FUNCTIONS ****************************************
def _generate_mote(motes, mote_id, mote_type, max_xy=MAX_XY_POSITION, dmin=MIN_DIST_BETWEEN_MOTES, dmax=MAX_DIST_BETWEEN_MOTES * 0.9):
    while True:
        d, x, y = float("Inf"), random.randint(-max_xy[0], max_xy[0]), random.randint(-max_xy[1], max_xy[1])
        for n in motes:
            d = min(d, math.sqrt((x - n['x'])**2 + (y - n['y'])**2))
        if dmin < d < dmax:
            return {"id": mote_id, "type": mote_type, "x": float(x), "y": float(y), "z": 0}


# ******************************************* GET FUNCTIONS *******************************************
def generate_motes(n=NBR_MOTES):
    motes = [{"id": 0, "type": "root", "x": 0, "y": 0, "z": 0}]
    malicious = None
    for i in range(n):
        # this is aimed to randomly add the malicious mote not far from the root
        if malicious is None and random.randint(1, n // (i + 1)) == 1:
            malicious = _generate_mote(motes, n + 1, "malicious")
            motes.append(malicious)
        # now generate a position for the current mote
        motes.append(_generate_mote(motes, i + 1, "sensor"))
    malicious = _generate_mote(motes, n + 1, "malicious") if not malicious else motes.pop(motes.index(malicious))
    motes.append(malicious)
    return motes


def get_constants(blocks):
    with open('./templates/building-blocks.json') as f:
        available_blocks = json.load(f)
    constants = {}
    for block in blocks:
        try:
            for constant, value in available_blocks[block].items():
                if constant in constants.keys():
                    logging.warning(" > Building-block '{}': '{}' is already set to {}".format(block, constant, value))
                else:
                    constants[constant] = value
        except KeyError:
            logging.error(" > Building-block '{}' does not exist !".format(block))
    return constants


def get_experiments(exp_file):
    exp_file = os.path.expanduser(exp_file)
    if not exp_file.endswith(".json"):
        exp_file += ".json"
    if not os.path.exists(exp_file):
        logging.critical("Simulation campaign JSON file does not exist !")
        exit(2)
    with open(exp_file) as f:
        experiments = json.load(f)
    return experiments


def get_path(*args):
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.makedirs(path)
    return path
