# Transform a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import json
import os
import argparse
import pandas as pd
import datetime
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--destination", type=str,
                    help="destination name")
parser.add_argument("-f", "--file", type=str,
                    help="absolute path to crashes file")

args = parser.parse_args()

if not os.path.exists(args.file):
    print args.file+" not found, exiting"
    exit(1)

print "converting "+args.file+" to json"
df_crashes = pd.read_csv(args.file, na_filter=False)
dict_crashes = df_crashes.to_dict("records")

valid_crashes = []

for key in dict_crashes:

    if args.destination == "boston":
        # skip crashes that don't have a date & time
        if key["CALENDAR_DATE"] != "" and key["TIME,"] != "":
            valid_crash = OrderedDict([
                ("id", key["CAD_EVENT_REL_COMMON_ID"]),
                # assuming all crashes are timestamped in local time (GMT - 5)
                ("dateOccurred", key["CALENDAR_DATE"]+"T"+key["TIME"]+"-05:00"),
                ("location", OrderedDict([
                    ("latitude", key["X"]),
                    ("longitude", key["Y"])
                ])),
                # TODO vehicles
                # TODO persons
                ("summary", key["FIRST_EVENT_SUBTYPE"])
            ])
            valid_crashes.append(valid_crash)

    elif args.destination == "cambridge":
		# skip crashes that don't have a date & time
		valid_crash = OrderedDict([
			("id", key["CAD_EVENT_REL_COMMON_ID"]),
			# time values are supplied as epoch, assume they are in local time (GMT - 5)
			("dateOccurred", key["CALENDAR_DATE"]."T"+datetime.timedelta(seconds=key["TIME"])+"-05:00"),
			("location", OrderedDict([
				("latitude", key["X"]),
				("longitude", key["Y"])
			])),
			# TODO vehicles
			# TODO persons
			("summary", key["FIRST_EVENT_SUBTYPE"])
		])

		valid_crashes.append(valid_crash)

	else:
        print "transformation of "+args.destination+" crashes not yet implemented"
        exit(1)


print "done, {} valid crashes loaded".format(len(valid_crashes))

crashes_output = os.path.join(os.path.dirname(os.path.abspath(args.file)), args.destination+"_crashes.json")

with open(crashes_output, "w") as f:
    json.dump(valid_crashes, f)

print "output written to {}".format(crashes_output)
