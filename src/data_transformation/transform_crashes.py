# Transform a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import dateutil.parser as date_parser
import json
import os
import pandas as pd
import re
import yaml
from collections import OrderedDict
from datetime import datetime
from jsonschema import validate


def read_standardized_fields(filename, config):

    df_crashes = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_crashes = df_crashes.to_dict("records")

    crashes = {}

    for key in dict_crashes:

        # skip any crashes that don't have coordinates
        if key[config["latitude"]] == "" or key[config["longitude"]] == "":
            continue

        # crash data & time exist in a single field
        if config["date_and_time"] != None:

            # skip any crashes that don't have a date_time
            if key[config["date_and_time"]] == "":
                continue

            # values matching this regex require no transformation
            if re.match(r"\d{4}-\d{2}-\d{2}T.+", str(key[config["date_and_time"]])):
                date_time = key[config["date_and_time"]]

            else:
                date_time = datetime.strftime(date_parser.parse(key[config["Date Time"]]), "%Y-%m-%dT%H:%M:%S")+"Z"

        # date and time exist in separate fields
        else:
            # some dates arrive as 'YYYY-MM-DD 00:00:00.000', remove useless timestamp
            if key[config["date_only"]].endswith(' 00:00:00.000'):
                date = key[config["date_only"]][:-13]

            else:
                date = key[config["date_only"]]

            # some times arrive as 'HH:MM:SS'
            if re.match(r"\d{2}:\d{2}:\d{2}", str(key[config["time_only"]])):
                time = key[config["time_only"]]

            # others are seconds since midnight
            else:
                m, s = divmod(int(key[config["time_only"]]), 60)
                h, m = divmod(m, 60)
                time = str("%02d:%02d:%02d" % (h, m, s))

            # TODO add timezone to config ("Z" is UTC)
            date_time = date+"T"+time+"Z"

        crash = OrderedDict([
            ("id", key[config["id"]]),
            ("dateOccurred", date_time),
            ("location", OrderedDict([
                ("latitude", float(key[config["latitude"]])),
                ("longitude", float(key[config["longitude"]]))
            ]))
        ])

        crash["summary"] = key[config["summary"]]

        crashes[crash["id"]] = crash

    return crashes

def read_city_specific_fields(filename, crashes, config):

    df_crashes = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
    dict_crashes = df_crashes.to_dict("records")

    for key in dict_crashes:

        # crash may not have made it through standardized function if it was missing required data
        if crashes.has_key(key[config["id"]]) == False:
            # print "crash "+str(key[config["id"]])+" not present in standardized crashes, skipping"
            continue

        # setup a vehicles list for each crash
        crashes[key[config["id"]]]["vehicles"] = []

        # check for car involvement
        if config["vehicles"] == "mode_type":
            # this needs work, but for now any of these mode types translates to a car being involved, quantity unknown
            if key[config["vehicles"]] == "mv" or key[config["vehicles"]] == "ped" or key[config["vehicles"]] == "":
                crashes[key[config["id"]]]["vehicles"].append({ "category": "car" })

        elif config["vehicles"] == "TOTAL_VEHICLES":
            if key[config["vehicles"]] != 0 and key[config["vehicles"]] != "":
                crashes[key[config["id"]]]["vehicles"].append({ "category": "car", "quantity": int(key[config["vehicles"]]) })

        # check for bike involvement
        if config["bikes"] == "mode_type":
            # assume bike and car involved, quantities unknown
            if key[config["bikes"]] == "bike":
                crashes[key[config["id"]]]["vehicles"].append({ "category": "car" })
                crashes[key[config["id"]]]["vehicles"].append({ "category": "bike" })

        elif config["bikes"] == "TOTAL_BICYCLES":
            if key[config["bikes"]] != 0 and key[config["bikes"]] != "":
                crashes[key[config["id"]]]["vehicles"].append({ "category": "bike", "quantity": int(key[config["bikes"]]) })


    return crashes

    # Unfortunately, since we need to handle these separately,
    # We'll have to iterate through each row of each file again,
    # and compare it against the existing structure

    # Here's where you do the hardcoded if city == 'boston' etc handling

    # I recommend making read_standardized_fields return a dict indexed on
    # id but also including id (passed in as crashes).
    # Then convert to a list using a list comprehension
    pass


def make_dir_structure(city, filename):
    # if the directory name doesn't exist, create it
    # dir name of the city?
    # if raw, processed, docs subdirs don't exist, create them
    # copy filename into raw directory
    pass

# In main:
# handle args
# make_dir_structure
# read_standardized_fields
# read city specific fields
# dump transformed fields


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", type=str,
                        help="destination name")
    parser.add_argument("-f", "--folder", type=str,
                        help="path to destination's data folder")

    args = parser.parse_args()

    raw_path = os.path.join(args.folder, "raw/crashes")
    if not os.path.exists(raw_path):
        print raw_path+" not found, exiting"
        exit(1)

    # load config for this city
    config_file = "/app/src/data/config_"+args.destination+".yml"
    with open(config_file) as f:
        config = yaml.safe_load(f)

    dict_city_crashes = {}

    print "searching "+raw_path+" for raw files:\n"

    for csv_file in os.listdir(raw_path):

        # find the config for this crash file
        crash_config = None
        for crash_file in config['crashes_files']:
            if (crash_file['filename'] == csv_file):
                crash_config = crash_file
                break

        if crash_config is None:
            print "- could not find config for crash file "+csv_file+", skipping"
            continue

        print "processing "+csv_file
        std_crashes = read_standardized_fields(csv_file, crash_config)
        print "- {} crashes loaded with standardized fields, checking for specific fields\n".format(len(std_crashes))

        spc_crashes = read_city_specific_fields(csv_file, std_crashes, crash_config)

        dict_city_crashes.update(spc_crashes)

    print "all crash files processed"
    print "- {} {} crashes loaded, validating against schema".format(len(dict_city_crashes), args.destination)

    schema_path = "/app/standards/crashes-schema.json"
    list_city_crashes = dict_city_crashes.values()
    with open(schema_path) as crashes_schema:
        validate(list_city_crashes, json.load(crashes_schema))

    crashes_output = os.path.join(args.folder, "standardized/crashes.json")

    with open(crashes_output, "w") as f:
        json.dump(list_city_crashes, f)

    print "- output written to {}".format(crashes_output)
