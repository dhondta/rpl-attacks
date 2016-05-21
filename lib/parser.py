# -*- coding: utf8 -*-
from csv import DictWriter
from os.path import join as pj
import os
import re
import subprocess


def powertracker2csv(folder, shift=0):
    output_folder = pj(folder, "results")
    with open(pj(folder, "powertracker.log")) as f:
        powertracker_logs = f.read()
        monitored_iterable = re.finditer(
            r"^(Sky|Wismote|Z1)_(?P<mote_id>\d+) MONITORED (?P<monitored_time>\d+)",
            powertracker_logs, re.MULTILINE)
        on_iterable = re.finditer(
            r"^(Sky|Wismote|Z1)_(?P<mote_id>\d+) ON (?P<on_time>\d+)",
            powertracker_logs, re.MULTILINE)
        tx_iterable = re.finditer(
            r"^(Sky|Wismote|Z1)_(?P<mote_id>\d+) TX (?P<tx_time>\d+)",
            powertracker_logs, re.MULTILINE)
        rx_iterable = re.finditer(
            r"^(Sky|Wismote|Z1)_(?P<mote_id>\d+) RX (?P<rx_time>\d+)",
            powertracker_logs, re.MULTILINE)
        int_iterable = re.finditer(
            r"^(Sky|Wismote|Z1)_(?P<mote_id>\d+) INT (?P<int_time>\d+)",
            powertracker_logs, re.MULTILINE)
        all_iterable = zip(monitored_iterable, on_iterable, tx_iterable, rx_iterable, int_iterable)
        fields = ["mote_id", "monitored_time", "tx_time", "rx_time", "on_time", "int_time"]


        with open(pj(output_folder, "powertracker.csv"), "w") as csv_output:
            writer = DictWriter(csv_output, delimiter=',', fieldnames=fields)
            writer.writeheader()

            for matches in all_iterable:
                row = {}
                for match in matches:
                    all(m.groupdict()["mote_id"] == matches[0].groupdict()["mote_id"]
                        for m in matches)
                    row.update((k, int(v))
                               for k, v in match.groupdict().items())
                # Passing the result from us to s
                row["monitored_time"] = float(
                    row["monitored_time"]) / (10 ** 6)
                row["tx_time"] = float(row["tx_time"]) / (10 ** 6)
                row["rx_time"] = float(row["rx_time"]) / (10 ** 6)
                row["on_time"] = float(row["on_time"]) / (10 ** 6)
                row["int_time"] = float(row["int_time"]) / (10 ** 6)
                if row["monitored_time"] > shift:
                    writer.writerow(row)


def pcap2csv(folder):
    """
    Execute a simple filter on PCAP and count
    """
    print("start pcap2csv")
    with open(pj(folder, "results", "pcap.csv"), "wb") as output_file:
        command = ["tshark",
                   "-T", "fields",
                   "-E", "header=y",
                   "-E", "separator=,",
                   "-e", "frame.time_relative",
                   "-e", "frame.len",
                   "-e", "wpan.src64",
                   "-e", "wpan.dst64",
                   "-e", "icmpv6.type",
                   "-e", "ipv6.src",
                   "-e", "ipv6.dst",
                   "-e", "icmpv6.code",
                   "-e", "data.data",
                   "-r", pj(folder, "output.pcap")]
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        output_file.write(stdout)

