# Standardize a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import dateutil.parser as date_parser
import json
import os
import pandas as pd
import re
import yaml
from collections import OrderedDict
from datetime import timedelta
from jsonschema import validate
import csv
import datetime

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))


def read_standardized_fields(raw_crashes, fields, opt_fields):

    crashes = {}

    for i, crash in enumerate(raw_crashes):
        if i % 10000 == 0:
            print i
        # skip any crashes that don't have coordinates or date
        if crash[fields["latitude"]] == "" or crash[fields["longitude"]] == "" \
           or crash[fields['date']] == "":
            continue

        # Date can either be a date or a date time
        date = date_parser.parse(crash[fields['date']])
        # If there's no time in the date given, look at the time field
        # if available
        if date.hour == 0 and date.minute == 0 and date.second == 0 \
           and 'time' in fields and fields['time']:

            # special case of seconds past midnight
            time = crash[fields['time']]
            if re.match(r"^\d+$", str(time)) and int(time) >= 0 \
               and int(time) < 86400:
                date = date + timedelta(seconds=int(crash[fields['time']]))

            else:
                date = date_parser.parse(
                    date.strftime('%Y-%m-%d ') + str(time)
                )

        # TODO add timezone to config ("Z" is UTC)
        date_time = date.strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted_crash = OrderedDict([
            ("id", crash[fields["id"]]),
            ("dateOccurred", date_time),
            ("location", OrderedDict([
                ("latitude", float(crash[fields["latitude"]])),
                ("longitude", float(crash[fields["longitude"]]))
            ]))
        ])
        formatted_crash = add_city_specific_fields(crash, formatted_crash,
                                                   opt_fields)
        crashes[formatted_crash["id"]] = formatted_crash
    return crashes


def add_city_specific_fields(crash, formatted_crash, fields):

    # Add summary and address
    if "summary" in fields.keys() and fields["summary"]:
        formatted_crash["summary"] = crash[fields["summary"]]
    if "address" in fields.keys() and fields["address"]:
        formatted_crash["address"] = crash[fields["address"]]

    # setup a vehicles list for each crash
    formatted_crash["vehicles"] = []

    # check for car involvement
    if "vehicles" in fields.keys() and fields["vehicles"] == "mode_type":
        # this needs work, but for now any of these mode types
        # translates to a car being involved, quantity unknown
        if crash[fields["vehicles"]] == "mv" or crash[fields["vehicles"]] == "ped" or crash[fields["vehicles"]] == "":
            formatted_crash["vehicles"].append({"category": "car"})

    elif "vehicles" in fields.keys() and fields["vehicles"] == "TOTAL_VEHICLES":
        if crash[fields["vehicles"]] != 0 and crash[fields["vehicles"]] != "":
            formatted_crash["vehicles"].append({
                "category": "car",
                "quantity": int(crash[fields["vehicles"]])
            })

    # check for bike involvement
    if "bikes" in fields.keys() and fields["bikes"] == "mode_type":
        # assume bike and car involved, quantities unknown
        if crash[fields["bikes"]] == "bike":
            formatted_crash["vehicles"].append({"category": "car"})
            formatted_crash["vehicles"].append({"category": "bike"})

    elif "bikes" in fields.keys() and fields["bikes"] == "TOTAL_BICYCLES":
        if crash[fields["bikes"]] != 0 and crash[fields["bikes"]] != "":
            formatted_crash['vehicles'].append({
                "category": "bike",
                "quantity": int(crash[fields["bikes"]])
            })
    return formatted_crash


def add_id(csv_file, id_field):
    """
    If the csv_file does not contain an id, create one
    """

    rows = []
    with open(csv_file) as f:
        csv_reader = csv.DictReader(f)
        count = 1
        for row in csv_reader:
            if id_field in row:
                break
            row.update({id_field: count})
            rows.append(row)
            count += 1
    if rows:
        with open(csv_file, 'w') as f:
            writer = csv.DictWriter(f, rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(row)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", type=str,
                        help="destination name, e.g. boston")
    parser.add_argument("-f", "--folder", type=str,
                        help="path to destination's data folder")

    args = parser.parse_args()

    raw_path = os.path.join(args.folder, "raw/crashes")
    if not os.path.exists(raw_path):
        print raw_path+" not found, exiting"
        exit(1)

    # load config for this city
    config_file = os.path.join(BASE_FP, 'src/config',
                               "config_"+args.destination+".yml")
    with open(config_file) as f:
        config = yaml.safe_load(f)

    dict_city_crashes = {}
    print "searching "+raw_path+" for raw files:\n"

    for csv_file in config['crashes_files'].keys():

        if not os.path.exists(os.path.join(raw_path, csv_file)):
            raise SystemExit(csv_file + " not found, exiting")
        # find the config for this crash file
        crash_config = config['crashes_files'][csv_file]
        if crash_config is None:
            print "- could not find config for crash file "+csv_file+", skipping"
            continue

        add_id(
            os.path.join(raw_path, csv_file), crash_config['required']['id'])

        print "processing "+csv_file

        df_crashes = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
        raw_crashes = df_crashes.to_dict("records")

        std_crashes = read_standardized_fields(raw_crashes,
                            crash_config['required'], crash_config['optional'])
        print "- {} crashes loaded with standardized fields, checking for specific fields\n".format(len(std_crashes))
        dict_city_crashes.update(std_crashes)

    print "all crash files processed"
    print "- {} {} crashes loaded, validating against schema".format(len(dict_city_crashes), args.destination)

    schema_path = os.path.join(BASE_FP, "standards", "crashes-schema.json")
    list_city_crashes = dict_city_crashes.values()
    with open(schema_path) as crashes_schema:
        validate(list_city_crashes, json.load(crashes_schema))

    crashes_output = os.path.join(args.folder, "standardized/crashes.json")

    with open(crashes_output, "w") as f:
        json.dump(list_city_crashes, f)

    print "- output written to {}".format(crashes_output)
