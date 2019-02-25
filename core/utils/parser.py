# -*- coding: utf8 -*-
import networkx
import numpy
from csv import DictReader, DictWriter
from matplotlib import pyplot
from matplotlib.patches import FancyArrowPatch
from os.path import basename, isdir, join, normpath
from re import finditer, match, MULTILINE
from subprocess import Popen, PIPE

from core.utils.rpla import get_available_platforms, get_motes_from_simulation


__all__ = [
    'parsing_chain',
]


# *************************************** MAIN PARSING FUNCTION ****************************************
def parsing_chain(path, logger=None):
    """
    This function chains the conversion and drawings for exploiting the data collected while running a Cooja
     simulation into relevant results.

    :param path: path to the experiment (including [with-|without-malicious])
    :param logger: logging.Logger instance
    """
    assert isdir(path)
    __convert_pcap_to_csv(path, logger)
    __convert_powertracker_log_to_csv(path, logger)
    __draw_dodag(path, logger)
    __draw_power_barchart(path, logger)


# *********************************** SIMULATION PARSING FUNCTIONS *************************************
def __convert_pcap_to_csv(path, logger=None):
    """
    This function creates a CSV file (to ./results) from a PCAP file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment (including [with-|without-malicious])
    :param logger: logging.Logger instance
    """
    if logger:
        logger.debug(" > Converting PCAP to CSV...")
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
        out = b"Tshark is not installed !"
        if logger:
            logger.warn(out)
    with open(join(results, 'pcap.csv'), 'wb') as f:
        f.write(out)


PT_ITEMS = ['monitored', 'on', 'tx', 'rx', 'int']
PT_REGEX = r'^({})_(?P<mote_id>\d+) {} (?P<{}>\d+)'


def __convert_powertracker_log_to_csv(path, logger=None):
    """
    This function creates a CSV file (to ./results) from a PowerTracker log file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment (including [with-|without-malicious])
    :param logger: logging.Logger instance
    """
    if logger:
        logger.debug(" > Converting power tracking log to CSV...")
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


def __draw_dodag(path, logger=None):
    """
    This function draws the DODAG (to ./results) from the list of motes (from ./simulation.csc) and the list of
     edges (from ./data/relationships.log).

    :param path: path to the experiment (including [with-|without-malicious])
    :param logger: logging.Logger instance
    """
    if logger:
        logger.debug(" > Drawing DODAG to PNG...")
    pyplot.clf()
    with_malicious = (basename(normpath(path)) == 'with-malicious')
    data, results = join(path, 'data'), join(path, 'results')
    with open(join(data, 'relationships.log')) as f:
        relationships = f.read()
    # first, check if the mote relationships were recorded
    if len(relationships.strip()) == 0:
        if logger:
            logger.warn("Relationships log file is empty !")
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


def __draw_power_barchart(path, logger=None):
    """
    This function plots the average power tracking data from the CSV at:
     [EXPERIMENT]/[with-|without-malicious]/results/powertracker.csv

    :param path: path to the experiment (including [with-|without-malicious])
    :param logger: logging.Logger instance
    """
    if logger:
        logger.debug(" > Drawing power bar chart to PNG...")
    pyplot.clf()
    items = ['on', 'tx', 'rx', 'int']
    # aggregate power tracker measures per mote
    data, c = {}, 0
    with open(join(path, 'results', 'powertracker.csv')) as f:
        for row in DictReader(f):
            mid = int(row['mote_id'])
            data.setdefault(mid, {i: 0.0 for i in items})
            for i in items:
                data[mid][i] += float(row[i + '_time'])
            c += 1
    n = len(data)
    c //= n  # number of measures per mote
    # normalize measures
    data = {mid: {i: measure / c for i, measure in totals.items()} for mid, totals in data.items()}
    # prepare series' data for the chart
    ind = numpy.arange(n)
    series = {i: [] for i in items}
    for mid, avg in sorted(data.items(), key=lambda x: x[0]):
        for k, v in series.items():
            v.append(avg[k])
    width = 0.5
    plots = []
    for s, color in zip(items, ['r', 'b', 'g', 'y']):
        plots.append(pyplot.bar(ind, series[s], width, color=color))
    pyplot.title("Power tracking per mote")
    pyplot.xticks(ind + width / 2., tuple(sorted(data.keys())))
    pyplot.yticks(numpy.arange(0, 31, 10))
    pyplot.ylabel("Consumed power (%)")
    pyplot.legend(tuple(p[0] for p in plots), tuple(i.upper() for i in items))
    pyplot.savefig(join(path, 'results', 'powertracking.png'))
