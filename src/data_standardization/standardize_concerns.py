# Standardize a concerns CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import dateutil.parser as date_parser
import os
import pandas as pd
from collections import OrderedDict
from datetime import datetime
from .standardization_util import validate_and_write_schema


CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--destination", type=str,
                    help="destination name")
parser.add_argument("-f", "--folder", type=str,
                    help="absolute path to destination folder")

args = parser.parse_args()

raw_path = os.path.join(args.folder, "raw/concerns")
if not os.path.exists(raw_path):
    print(raw_path+" not found, exiting")
    exit(1)

concerns = []
manual_concern_id = 1

print("searching "+raw_path+" for raw concerns file(s)")

for csv_file in os.listdir(raw_path):
    print(csv_file)


    df_concerns = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_concerns = df_concerns.to_dict("records")

    for key in dict_concerns:
        if args.destination == "boston":
            # Boston presently has concerns from two sources - VisionZero and SeeClickFix
            if csv_file == "Vision_Zero_Entry.csv":
                # skip concerns that don't have a date or request type
                if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                    continue

                else:
                    concerns.append(OrderedDict([
                        ("id", key["OBJECTID"]),
                        ("source", "visionzero"),
                        ("dateCreated", key["REQUESTDATE"]),
                        ("status", key["STATUS"]),
                        ("category", key["REQUESTTYPE"]),
                        ("location", OrderedDict([
                            ("latitude", key["Y"]),
                            ("longitude", key["X"])
                        ])),
                        ("summary", key["COMMENTS"])
                    ]))

            elif csv_file == "bos_scf.csv":
                # skip concerns that don't have a date or request type
                if key["created"] == "" or key["summary"] == "":
                    continue

                else:
                    concerns.append(OrderedDict([
                        ("id", manual_concern_id),
                        ("source", "seeclickfix"),
                        ("dateCreated", key["created"]),
                        ("status", "unknown"),
                        ("category", key["summary"]),
                        ("location", OrderedDict([
                            ("latitude", key["Y"]),
                            ("longitude", key["X"])
                        ])),
                        ("summary", key["description"])
                    ]))

                manual_concern_id += 1

        if args.destination == "dc":
            # skip concerns that don't have a date or request type
            if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                continue

            concerns.append(OrderedDict([
                ("id", key["OBJECTID"]),
                ("source", "visionzero"),
                ("dateCreated", key["REQUESTDATE"]),
                ("status", key["STATUS"]),
                ("category", key["REQUESTTYPE"]),
                ("location", OrderedDict([
                    ("latitude", key["Y"]),
                    ("longitude", key["X"])
                ])),
                ("summary", key["COMMENTS"])
            ]))

        elif args.destination == "cambridge":
            # skip concerns that don't have a date or issue type
            if key["ticket_created_date_time"] == "" or key["issue_type"] == "":
                continue

            concerns.append(OrderedDict([
                ("id", key["ticket_id"]),
                ("source", "seeclickfix"),
                ("dateCreated", datetime.strftime(date_parser.parse(key["ticket_created_date_time"]), "%Y-%m-%dT%H:%M:%S")+"-05:00"),
                ("status", key["ticket_status"]),
                ("category", key["issue_type"]),
                ("location", OrderedDict([
                    ("latitude", key["lat"]),
                    ("longitude", key["lng"])
                ])),
                ("summary", key["issue_description"])
            ]))

print("done, {} concerns loaded, validating against schema".format(len(concerns)))

schema_path = os.path.join(BASE_FP, "standards/concerns-schema.json")
concerns_output = os.path.join(args.folder, "standardized/concerns.json")
validate_and_write_schema(schema_path, concerns, concerns_output)
