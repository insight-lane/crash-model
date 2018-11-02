# Standardize a concerns CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import os
import pandas as pd
from collections import OrderedDict
import yaml
import pytz
from .standardization_util import validate_and_write_schema, parse_date


CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))


def read_concerns(datadir, folder, timezone):
    """
    Reads concerns from a directory
    todo: need to move away from hardcoded cities here
    Args:
        raw_path - path to the concerns
        timezone
    Returns:
        nothing - writes standardized concerns to file
    """
    concerns = []
    manual_concern_id = 1

    raw_path = os.path.join(datadir, "raw/concerns")
    if not os.path.exists(raw_path):
        print(raw_path + " not found, exiting")
        exit(1)

    print("searching "+raw_path+" for raw concerns file(s)")

    for csv_file in os.listdir(raw_path):
        print(csv_file)

        df_concerns = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
        dict_concerns = df_concerns.to_dict("records")

        for key in dict_concerns:
            if folder == "boston":
                # Boston presently has concerns from two sources - VisionZero and SeeClickFix
                if csv_file == "Vision_Zero_Entry.csv":
                    # skip concerns that don't have a date or request type
                    if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                        continue

                    else:
                        concerns.append(OrderedDict([
                            ("id", key["OBJECTID"]),
                            ("source", "visionzero"),
                            ("dateCreated", parse_date(
                                key["REQUESTDATE"], timezone)),
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
                            ("dateCreated", parse_date(
                                key["created"], timezone)),
                            ("status", "unknown"),
                            ("category", key["summary"]),
                            ("location", OrderedDict([
                                ("latitude", key["Y"]),
                                ("longitude", key["X"])
                            ])),
                            ("summary", key["description"])
                        ]))

                    manual_concern_id += 1

            if folder == "dc":
                # skip concerns that don't have a date or request type
                if key["REQUESTDATE"] == "" or key["REQUESTTYPE"] == "":
                    continue

                concerns.append(OrderedDict([
                    ("id", key["OBJECTID"]),
                    ("source", "visionzero"),
                    ("dateCreated", parse_date(key["REQUESTDATE"], timezone)),
                    ("status", key["STATUS"]),
                    ("category", key["REQUESTTYPE"]),
                    ("location", OrderedDict([
                        ("latitude", key["Y"]),
                        ("longitude", key["X"])
                    ])),
                    ("summary", key["COMMENTS"])
                ]))

            elif folder == "cambridge":
                # skip concerns that don't have a date or issue type
                if key["ticket_created_date_time"] == "" or key["issue_type"] == "":
                    continue

                concerns.append(OrderedDict([
                    ("id", key["ticket_id"]),
                    ("source", "seeclickfix"),
                    ("dateCreated", parse_date(
                        key["ticket_created_date_time"], timezone)),
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
    concerns_output = os.path.join(datadir, "standardized/concerns.json")
    validate_and_write_schema(schema_path, concerns, concerns_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="config file")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="data directory")

    args = parser.parse_args()

    # load config
    config_file = args.config
    with open(config_file) as f:
        config = yaml.safe_load(f)

    read_concerns(
        args.datadir, config['name'], pytz.timezone(config['timezone']))
