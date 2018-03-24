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
parser.add_argument("-f", "--file", type=str,
                    help="absolute path to concerns file")

args = parser.parse_args()

if not os.path.exists(args.file):
    print args.file+" not found, exiting"
    exit(1)

print "converting "+args.file+" to json"
df_concerns = pd.read_csv(args.file, na_filter=False)
dict_concerns = df_concerns.to_dict("records")

valid_concerns = []

for key in dict_concerns:

    if args.destination == "dc" or args.destination == "boston":
        # skip concerns that don't have a date
        if key["REQUESTDATE"] != "":
            valid_concern = OrderedDict([
                ("id", key["OBJECTID"]),
                ("dateCreated", key["REQUESTDATE"]),
                ("status", key["STATUS"]),
                ("tags", [key["REQUESTTYPE"]]),
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

concerns_output = os.path.join(os.path.dirname(os.path.abspath(args.file)), args.destination+"_concerns.json")

with open(concerns_output, "w") as f:
    json.dump(valid_concerns, f)

print "output written to {}".format(concerns_output)
