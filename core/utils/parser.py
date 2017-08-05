# -*- coding: utf8 -*-
import networkx
import numpy
from csv import DictReader, DictWriter
from matplotlib import pyplot
from matplotlib.patches import FancyArrowPatch
from os.path import basename, join, normpath
from re import finditer, match, MULTILINE
from subprocess import Popen, PIPE

from core.utils.rpla import get_available_platforms, get_motes_from_simulation


__all__ = [
    'parsing_chain',
]


# *************************************** MAIN PARSING FUNCTION ****************************************
def parsing_chain(path):
    convert_pcap_to_csv(path)
    convert_powertracker_log_to_csv(path)
    draw_dodag(path)
    draw_power_barchart(path)


# *********************************** SIMULATION PARSING FUNCTIONS *************************************
def convert_pcap_to_csv(path):
    """
    This function creates a CSV file (to ./results) from a PCAP file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment (including [with-|without-malicious])
    """
    data, results = join(path, 'data'), join(path, 'results')
    try:
        p = Popen(['tshark',
                   '-T', 'fields',
                   '-E', 'header=y',
                   '-E', 'separator=,',
                   '-e', 'frame.time',
                   '-e', 'frame.len',
                   '-e', 'wpan.src64',
                   '-e', 'wpan.dst64',
                   '-e', 'icmpv6.type',
                   '-e', 'ipv6.src',
                   '-e', 'ipv6.dst',
                   '-e', 'icmpv6.code',
                   '-e', 'data.data',
                   '-r', join(data, 'output.pcap')], stdout=PIPE)
        out, _ = p.communicate()
    except OSError:
        out = "[ERROR] Tshark is not installed !"
    with open(join(results, 'pcap.csv'), 'wb') as f:
        f.write(out)


PT_ITEMS = ['monitored', 'on', 'tx', 'rx', 'int']
PT_REGEX = r'^({})_(?P<mote_id>\d+) {} (?P<{}>\d+)'


def convert_powertracker_log_to_csv(path):
    """
    This function creates a CSV file (to ./results) from a PowerTracker log file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment (including [with-|without-malicious])
    """
    platforms = [p.capitalize() for p in get_available_platforms()]
    data, results = join(path, 'data'), join(path, 'results')
    with open(join(data, 'powertracker.log')) as f:
        log = f.read()
    iterables, fields = [], ['mote_id']
    for it in PT_ITEMS:
        time_field = '{}_time'.format(it)
        iterables.append(finditer(PT_REGEX.format('|'.join(platforms), it.upper(), time_field), log, MULTILINE))
        fields.append(time_field)
    with open(join(results, 'powertracker.csv'), 'w') as f:
        writer = DictWriter(f, delimiter=',', fieldnames=fields)
        writer.writeheader()
        for matches in zip(*iterables):
            row = {}
            for m in matches:
                row.update((k, int(v)) for k, v in m.groupdict().items())
            for it in PT_ITEMS:
                time_field = '{}_time'.format(it)
                row[time_field] = float(row[time_field] / 10 ** 6)
            writer.writerow(row)


RELATIONSHIP_REGEX = r'^\d+\s+ID\:(?P<mote_id>\d+)\s+#L\s+(?P<parent_id>\d+)\s+(?P<flag>\d+)$'


def draw_dodag(path):
    """
    This function draws the DODAG (to ./results) from the list of motes (from ./simulation.csc) and the list of
     edges (from ./data/relationships.log).

    :param path: path to the experiment (including [with-|without-malicious])
    """
    pyplot.clf()
    with_malicious = (basename(normpath(path)) == 'with-malicious')
    data, results = join(path, 'data'), join(path, 'results')
    with open(join(data, 'relationships.log')) as f:
        relationships = f.read()
    # first, check if the mote relationships were recorded
    if len(relationships.strip()) == 0:
        return
    # retrieve motes and their colors
    dodag = networkx.DiGraph()
    motes = get_motes_from_simulation(join(path, 'simulation.csc'))
    dodag.add_nodes_from(motes.keys())
    colors = []
    for n, p in motes.items():
        x, y = p
        dodag.node[n]['pos'] = motes[n] = (x, -y)
        colors.append('green' if n == 0 else ('yellow' if not with_malicious or
                                              (with_malicious and 0 < n < len(motes) - 1) else 'red'))
    # retrieve edges from relationships.log
    edges = {}
    for relationship in relationships.split('\n'):
        try:
            d = match(RELATIONSHIP_REGEX, relationship.strip()).groupdict()
            if int(d['flag']) == 0:
                continue
            mote, parent = int(d['mote_id']), int(d['parent_id'])
            edges[mote] = parent
        except AttributeError:
            continue
    # now, fill in the graph with edges
    dodag.add_edges_from(edges.items())
    # finally, draw the graph
    networkx.draw(dodag, motes, node_color=colors, with_labels=True)
    pyplot.savefig(join(results, 'dodag.png'), arrow_style=FancyArrowPatch)


def draw_power_barchart(path):
    """
    This function plots the average power tracking data from the CSV at:
     [EXPERIMENT]/[with-|without-malicious]/results/powertracker.csv

    :param path: path to the experiment (including [with-|without-malicious])
    :return:
    """
    pyplot.clf()
    items = ['on', 'tx', 'rx', 'int']
    series = {i: [] for i in items}
    averages, c = {}, 0
    with open(join(path, 'results', 'powertracker.csv')) as f:
        for row in DictReader(f):
            mid = int(row['mote_id'])
            averages.setdefault(mid, {i: 0.0 for i in items})
            for s, k in zip(items, [i + '_time' for i in items]):
                averages[mid][s] += float(row[k])
            c += 1
    n = len(averages)
    ind = numpy.arange(n)
    c //= n
    averages = {mid: {k: v / c for k, v in avg.items()} for mid, avg in averages.items()}
    for mid, avg in sorted(averages.items(), key=lambda x: x[0]):
        for k, v in series.items():
            v.append(avg[k])
    width = 0.5
    plots = []
    for s, color in zip(items, ['r', 'b', 'g', 'y']):
        plots.append(pyplot.bar(ind, series[s], width, color=color))
    pyplot.title("Power tracking per mote")
    pyplot.xticks(ind + width / 2., tuple(sorted(averages.keys())))
    pyplot.yticks(numpy.arange(0, 31, 10))
    pyplot.ylabel("Consumed power (%)")
    pyplot.legend((p[0] for p in plots), (i.upper() for i in items))
    pyplot.savefig(join(path, 'results', 'powertracking.png'))
