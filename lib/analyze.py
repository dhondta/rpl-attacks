# -*- coding: utf-8 -*-
from os.path import join as pj
import os
import pandas as pd


def dashboard(folder, BIN=5):
    df = pd.read_csv(pj(folder, "results", "pcap_relooked.csv"))

    df["bin_start"] = BIN * (df.time // BIN)

    bin_df = pd.DataFrame()
    bin_df["total"] = df.groupby("bin_start").length.sum()
    bin_df["udp"] = df[df.icmpv6_type == "udp"].groupby("bin_start").length.sum()
    bin_df["rpl"] = df[df.icmpv6_type == "rpl"].groupby("bin_start").length.sum()
    bin_df["forwarding"] = df[df.forwarding].groupby("bin_start").length.sum()
    bin_df.to_csv(pj(folder, "results", "bin_global.csv"))

    powertracker = pd.read_csv(pj(folder, "results", "powertracker.csv"))

    for target in pd.Series(df.mac_src.values.ravel()).unique():
        if target > 1:
            node_df = df[df.mac_src == target]
            bin_df = pd.DataFrame()
            bin_df["total"] = node_df.groupby("bin_start").length.sum()
            bin_df["udp"] = node_df[node_df.icmpv6_type == "udp"].groupby("bin_start").length.sum()
            bin_df["rpl"] = node_df[node_df.icmpv6_type == "rpl"].groupby("bin_start").length.sum()
            bin_df["forwarding"] = node_df[node_df.forwarding].groupby("bin_start").length.sum()

            # Conversion from bytes to time
            RATE = 250000
            bin_df = 8.0 * bin_df / RATE

            output_folder = pj(folder, "results", "protocol_repartition")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            bin_df.to_csv(pj(output_folder, "protocol_repartition_%d.csv" % int(target)))

            output_folder = pj(folder, "results", "powertracker")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            powertracker_target = powertracker[powertracker.mote_id == target]
            powertracker_target["bin_start"] = BIN * (powertracker.monitored_time // BIN)
            del powertracker_target["mote_id"]
            powertracker_target.to_csv(pj(output_folder, "series_powertracker_%.d.csv" % target))

            bin_powertracker = powertracker_target.groupby("bin_start").max()[["tx_time", "rx_time"]]
            for kind in ["tx_time", "rx_time"]:
                bin_powertracker["diff_%s" % kind] = bin_powertracker[kind].diff()

            #res = res.join(bin_powertracker)
            output_folder = pj(folder, "results", "dashboard")
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            #res.to_csv(pj(output_folder, "res_%d.csv" % int(target)))
            bin_powertracker.to_csv(pj(output_folder, "res_%d.csv" % int(target)))

