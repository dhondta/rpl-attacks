# -*- coding: utf8 -*-
import networkx
from csv import DictWriter
from json import load
from matplotlib import pyplot
from os.path import join
from re import finditer, match, MULTILINE
from subprocess import Popen, PIPE

from .utils import get_available_platforms


# *************************************** MAIN PARSING FUNCTION ****************************************
def parsing_chain(path, **kwargs):
    convert_pcap_to_csv(path)
    convert_powertracker_log_to_csv(path)
    draw_dodag(path, kwargs.get('with_malicious', False))


# *********************************** SIMULATION PARSING FUNCTIONS *************************************
def convert_pcap_to_csv(path):
    """
    This function creates a CSV file (to ./results) from a PCAP file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment
    """
    data, results = join(path, 'data'), join(path, 'results')
    with open(join(results, 'pcap.csv'), 'wb') as f:
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
        f.write(out)


PT_ITEMS = ['monitored', 'on', 'tx', 'rx', 'int']
PT_REGEX = r'^({})_(?P<mote_id>\d+) {} (?P<{}>\d+)'


def convert_powertracker_log_to_csv(path):
    """
    This function creates a CSV file (to ./results) from a PowerTracker log file (from ./data).
    This is inspired from https://github.com/sieben/makesense/blob/master/makesense/parser.py.

    :param path: path to the experiment
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
            for match in matches:
                #all(m.groupdict()['mote_id'] == matches[0].groupdict()['mote_id'] for m in matches)
                row.update((k, int(v)) for k, v in match.groupdict().items())
            for it in PT_ITEMS:
                time_field = '{}_time'.format(it)
                row[time_field] = float(row[time_field] / 10 ** 6)
            writer.writerow(row)


RELATIONSHIP_REGEX = r'^\d+\s+ID\:(?P<src_id>\d+)\s+#L\s+(?P<dst_id>\d+)\s+(?P<flag>\d+)$'


def draw_dodag(path, with_malicious=False):
    """
    This function draws the DODAG (to ./results) from the list of motes (from ./data/motes.json) and the list of
     edges (from ./data/relationships.log).

    :param path: path to the experiment
    """
    data, results = join(path, 'data'), join(path, 'results')
    dodag = networkx.DiGraph()
    with open(join(data, 'motes.json')) as f:
        motes = load(f)
    motes = {int(k): v for k, v in motes.items()}
    dodag.add_nodes_from([int(x) for x in motes.keys()])
    colors = []
    for n, p in motes.items():
        dodag.node[n]['pos'] = p
        colors.append('green' if n == 0 else ('yellow' if not with_malicious or
                                                          (with_malicious and 0 < n < len(motes) - 1) else 'red'))
    with open(join(data, 'relationships.log')) as f:
        for line in f.readlines():
            try:
                d = match(RELATIONSHIP_REGEX, line).groupdict()
                if int(d['flag']) == 0:
                    continue
                src, dst = int(d['src_id']), int(d['dst_id'])
            except AttributeError:
                continue
            for child in dodag.successors(src):
                dodag.remove_edge(src, child)
            dodag.add_edge(src, dst)
    networkx.draw(dodag, motes, node_color=colors)
    pyplot.savefig(join(results, 'dodag.png'))
