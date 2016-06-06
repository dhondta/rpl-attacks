# -*- coding: utf8 -*-
from numpy import arccos, average, cos, pi, sign, sin, sqrt
from random import randint, shuffle

WSN_DENSITY_FACTOR = 3


# ************************************** NETWORK GENERATION FUNCTION ****************************************
def generate_motes(**kwargs):
    """
    This function generates a WSN with 1 root, n legitimate motes and 1 malicious mote

    :return: the list of motes (formatted as dictionaries like hereafter)
    """
    defaults = kwargs.pop('defaults')
    nodes = [{"id": 0, "type": "root", "x": 0, "y": 0, "z": 0}]
    n = kwargs.pop('n', kwargs["number-motes"])
    min_range = kwargs.pop('min_range', defaults["minimum-distance-from-root"])
    max_range = kwargs.pop('max_range', defaults["area-square-side"] // 2)
    tx_range = kwargs.pop('tx_range', defaults["transmission-range"])
    # determine 'i', the number of steps for the algorithm
    # at step i, the newtork must be filled with at most sum(f * 2 ** i)
    #   e.g. if f = 3, with 10 nodes, root's proximity will hold 6 nodes then the 4 ones remaining in the next ring
    i, s, ni = 1, 0, 0
    node_ids = list(range(1, n + 1))
    shuffle(node_ids)
    while s <= n:
        s += WSN_DENSITY_FACTOR * 2 ** i
        i += 1
    # now, generate the nodes
    # first, the range increment is defined ; it will provide the interval of ranges for the quadrants
    range_inc = min(tx_range, max_range / (i - 1))
    for ns in range(1, i):
        # determine the number of nodes to be generated inside the current ring
        n_step = min(WSN_DENSITY_FACTOR * 2 ** ns, n - ni)
        # determine the angle increment for the quadrants
        angle_inc = 360 // n_step
        # then, divide the ring in quadrants and generate 1 node per quadrant with a 10% margin either
        #  for the angle or for the range
        range_min, range_max = int((ns - 0.7) * range_inc), int((ns - 0.1) * range_inc)
        for j in range(0, n_step):
            ni += 1
            angle_min, angle_max = int((j + 0.25) * angle_inc), int((j + 0.75) * angle_inc)
            d, k, x, y = 0, 0, 0, 0
            while not min_range < d < tx_range * 0.9 and k < 1000:
                node_angle = randint(angle_min, angle_max) * pi / 180
                node_range = randint(max(range_min, min_range), min(range_max, max_range))
                # compute the coordinates and append the new node to the list
                x, y = node_range * cos(node_angle), node_range * sin(node_angle)
                for node in nodes:
                    d = min(d, sqrt((x - node['x'])**2 + (y - node['y'])**2))
                k += 1
            nodes.append({'id': node_ids[ni-1], 'type': 'sensor', 'x': x, 'y': y, 'z': 0})
        if ni == n:
            break
        range_inc *= 0.6
    # finally, add the malicious mote in the middle of the network
    # get the average of the squared x and y deltas
    avg_x = average([sign(n['x']) * n['x'] ** 2 for n in nodes])
    x = sign(avg_x) * sqrt(abs(avg_x))
    avg_y = average([sign(n['y']) * n['y'] ** 2 for n in nodes])
    y = sign(avg_y) * sqrt(abs(avg_y))
    # if malicious mote is too close by the root, just push it away
    radius = sqrt(x ** 2 + y ** 2)
    if radius < min_range:
        angle = arccos(x / radius)
        x, y = min_range * cos(angle), min_range * sin(angle)
    nodes.append({'id': len(nodes), 'type': 'malicious', 'x': x, 'y': y, 'z': 0})
    return sorted(nodes, key=lambda o: o['id'])
