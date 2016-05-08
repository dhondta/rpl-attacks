# -*- coding: utf8 -*-
import math
import random
from os.path import join


NBR_MOTES = 10
MAX_XY_POSITION = [100, 100]
MIN_DIST_BETWEEN_MOTES = 20.0
MAX_DIST_BETWEEN_MOTES = 50.0


def _generate_mote_position(motes, max_xy=MAX_XY_POSITION, dmin=MIN_DIST_BETWEEN_MOTES, dmax=MAX_DIST_BETWEEN_MOTES * 0.9):
    while True:
        d, x, y = float("Inf"), random.randint(-max_xy[0], max_xy[0]), random.randint(-max_xy[1], max_xy[1])
        for n in motes:
            d = min(d, math.sqrt((x - n['x'])**2 + (y - n['y'])**2))
        if dmin < d < dmax:
            return x, y


def _render_save_template(path, env, template_name, **kwargs):
    template = env.get_template(template_name).render(**kwargs)
    with open(join(path, template_name), "w") as f:
        f.write(template)
    return template


def announce(f):
    def wrapper(*args, **kwargs):
        print("*** {}: {} ***".format(args[0], f.__name__))
        return f(*args, **kwargs)
    return wrapper


def generate_motes(n=NBR_MOTES):
    motes = [{"id": 0, "type": "root", "x": 0, "y": 0, "z": 0}]
    malicious_generated = False
    for i in range(n):
        # this is aimed to randomly add the malicious mote in the middle of the WSN
        if not malicious_generated and i == random.randint(0, n // 2):
            x, y = _generate_mote_position(motes)
            motes.append({"id": n + 1, "type": "malicious", "x": float(x), "y": float(y), "z": 0})
            malicious_generated = True
        # now generate a position for the current mote
        x, y = _generate_mote_position(motes)
        motes.append({"id": i + 1, "type": "sensor", "x": float(x), "y": float(y), "z": 0})
    if not malicious_generated:
        x, y = _generate_mote_position(motes)
        motes.append({"id": n + 1, "type": "malicious", "x": float(x), "y": float(y), "z": 0})
    return motes

