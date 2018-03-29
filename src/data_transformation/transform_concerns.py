# Transform a concerns CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import json
import os
import argparse
import pandas as pd
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--destination", type=str,
                    help="destination name")
parser.add_argument("-f", "--folder", type=str,
                    help="absolute path to destination folder")

args = parser.parse_args()

raw_path = os.path.join(args.folder, "raw")
if not os.path.exists(raw_path):
    print raw_path+" not found, exiting"
    exit(1)

valid_concerns = []

print "searching "+raw_path+" for raw concerns file(s)"

for csv_file in os.listdir(raw_path):
    print csv_file
    df_concerns = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_concerns = df_concerns.to_dict("records")

    for key in dict_concerns:
        if args.destination == "dc" or args.destination == "boston":
            # skip concerns that don't have a date or request type
            if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                continue

            valid_concern = OrderedDict([
                ("id", key["OBJECTID"]),
                ("dateCreated", key["REQUESTDATE"]),
                ("status", key["STATUS"]),
                ("category", key["REQUESTTYPE"]),
                ("location", OrderedDict([
                    ("latitude", key["X"]),
                    ("longitude", key["Y"])
                ]))
            ])

            # only add summary property if data exists
            if key["COMMENTS"] != "":
                valid_concern.update({"summary": key["COMMENTS"]})

            valid_concerns.append(valid_concern)

        elif args.destination == "cambridge":
            print "transformation of cambridge concerns not yet implemented"
            exit(1)

print "done, {} valid concerns loaded".format(len(valid_concerns))

concerns_output = os.path.join(args.folder, "transformed/concerns.json")

with open(concerns_output, "w") as f:
    json.dump(valid_concerns, f)

print "output written to {}".format(concerns_output)
