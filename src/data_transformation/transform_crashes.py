# Transform a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import datetime
import dateutil.parser as parser
import json
import os
import pandas as pd
from collections import OrderedDict

cmd_parser = argparse.ArgumentParser()
cmd_parser.add_argument("-d", "--destination", type=str,
                    help="destination name")
cmd_parser.add_argument("-f", "--folder", type=str,
                    help="absolute path to destination folder")

args = cmd_parser.parse_args()

raw_path = os.path.join(args.folder, "raw")
if not os.path.exists(raw_path):
    print raw_path+" not found, exiting"
    exit(1)

valid_crashes = []
manual_crash_id = 1

print "searching "+raw_path+" for raw crash file(s)"

for csv_file in os.listdir(raw_path):
    print csv_file
    df_crashes = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_crashes = df_crashes.to_dict("records")

    for key in dict_crashes:
        if args.destination == "boston":
            # skip crashes that don't have X, Y and date details
            if key["X"] == "" or key["Y"] == "" or key["CALENDAR_DATE"] == "":
                continue

            # 2015 and 2017 files
            # date requires no modification
            # time exists as seconds since midnight
            if "TIME," in key:
                if key["TIME,"] != "":
                    formatted_date = key["CALENDAR_DATE"]
                    m, s = divmod(int(key["TIME,"]), 60)
                    h, m = divmod(m, 60)
                    formatted_time = str("%02d:%02d:%02d" % (h, m, s))
                else:
                    continue

            # 2016 file
            # date requires splitting
            # time requires no modification
            if "TIME" in key:
                if key["TIME"] != "":
                    formatted_date = key["CALENDAR_DATE"].split(" ")[0]
                    formatted_time = key["TIME"]
                else:
                    continue

            valid_crash = OrderedDict([
                ("id", key["CAD_EVENT_REL_COMMON_ID"]),
                # assume all crashes are in local time (GMT-5)
                ("dateOccurred", formatted_date+"T"+formatted_time+"-05:00"),
                ("location", OrderedDict([
                    ("latitude", float(key["Y"])),
                    ("longitude", float(key["X"]))
                ]))
            ])

            # very basic transformation of mode_type into vehicles
            valid_crash["vehicles"] = []

            # all crashes are assumed to have involved a car
            valid_crash["vehicles"].append({"category": "car"})

            if key["mode_type"] == "bike":
                valid_crash["vehicles"].append({"category": "bike"})

            # TODO persons

            if key["FIRST_EVENT_SUBTYPE"] != "":
                valid_crash["summary"] = key["FIRST_EVENT_SUBTYPE"]

            valid_crashes.append(valid_crash)

        elif args.destination == "cambridge":
            # skip crashes that don't have a date, X and Y
            if key["Date Time"] == "" or key["X"] == "" or key["Y"] == "":
                continue

            valid_crash = OrderedDict([
                ("id", manual_crash_id),
                # assume all crashes are in local time (GMT-5)
                ("dateOccurred", str(parser.parse(key["Date Time"]))+"-05:00"),
                ("location", OrderedDict([
                    ("latitude", float(key["Y"])),
                    ("longitude", float(key["X"]))
                ]))
            ])

            # TODO persons

            if key["V1 First Event"] != "":
                valid_crash["summary"] = key["V1 First Event"]

            valid_crashes.append(valid_crash)

            manual_crash_id += 1

        elif args.destination == "dc":
            # skip crashes that don't have a date, X and Y
            if key["REPORTDATE"] == "" or key["X"] == "" or key["Y"] == "":
                continue

            valid_crash = OrderedDict([
                ("id", key["OBJECTID"]),
                ("dateOccurred", key["REPORTDATE"]),
                ("location", OrderedDict([
                    ("latitude", float(key["Y"])),
                    ("longitude", float(key["X"]))
                ]))
            ])

            if key["TOTAL_VEHICLES"] != 0 or key["TOTAL_BICYCLES"] != 0:
                valid_crash["vehicles"] = []

                if key["TOTAL_VEHICLES"] != 0:
                    valid_crash["vehicles"].append({"category": "car", "quantity": key["TOTAL_VEHICLES"]})

                if key["TOTAL_BICYCLES"] != 0:
                    valid_crash["vehicles"].append({"category": "bike", "quantity": key["TOTAL_BICYCLES"]})

            # TODO persons

            if key["ADDRESS"] != "":
                valid_crash["address"] = key["ADDRESS"]

            valid_crashes.append(valid_crash)

        else:
            print "transformation of "+args.destination+" crashes not yet implemented"
            exit(1)

print "done, {} valid crashes loaded".format(len(valid_crashes))

crashes_output = os.path.join(args.folder, "transformed/crashes.json")

with open(crashes_output, "w") as f:
    json.dump(valid_crashes, f)

print "output written to {}".format(crashes_output)
