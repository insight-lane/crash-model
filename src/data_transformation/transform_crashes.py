# Transform a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import dateutil.parser as date_parser
import json
import os
import pandas as pd
from collections import OrderedDict
from datetime import datetime
from jsonschema import validate


def read_standardized_fields(filenames, x_col, y_col, date_col, id=None,
                             address=None, summary=None):

    # Iterate through each filename:

    #     read each row in the csv
    #     look up the required fields and put them into the format we want
    #     use dateutil.parser parse for the date column
    # return a dict of results (see comments in read_city_specific_fields)

    # address and summary are easy fields to handle, so they can be handled
    # in this function, but handling vehicles/peds is going to complicated
    # so should be handled in read_city_specific_fields

    pass


def read_city_specific_fields(filenames, crashes, city):
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
                        help="absolute path to destination folder")

    args = parser.parse_args()

    raw_path = os.path.join(args.folder, "raw")
    if not os.path.exists(raw_path):
        print raw_path+" not found, exiting"
        exit(1)

    crashes = []
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

                crash = OrderedDict([
                    ("id", key["CAD_EVENT_REL_COMMON_ID"]),
                    # assume all crashes are in local time (GMT-5)
                    ("dateOccurred", formatted_date+"T"+formatted_time+"-05:00"),
                    ("location", OrderedDict([
                        ("latitude", float(key["Y"])),
                        ("longitude", float(key["X"]))
                    ]))
                ])

                # very basic transformation of mode_type into vehicles
                crash["vehicles"] = []

                # all crashes are assumed to have involved a car
                crash["vehicles"].append({"category": "car"})

                if key["mode_type"] == "bike":
                    crash["vehicles"].append({"category": "bike"})

                # TODO persons

                if key["FIRST_EVENT_SUBTYPE"] != "":
                    crash["summary"] = key["FIRST_EVENT_SUBTYPE"]

                crashes.append(crash)

            elif args.destination == "cambridge":
                # skip crashes that don't have a date, X and Y
                if key["Date Time"] == "" or key["X"] == "" or key["Y"] == "":
                    continue

                crash = OrderedDict([
                    ("id", manual_crash_id),
                    # assume all crashes are in local time (GMT-5)
                    ("dateOccurred", datetime.strftime(date_parser.parse(key["Date Time"]), "%Y-%m-%dT%H:%M:%S")+"-05:00"),
                    ("location", OrderedDict([
                        ("latitude", float(key["Y"])),
                        ("longitude", float(key["X"]))
                    ]))
                ])

                # TODO persons

                if key["V1 First Event"] != "":
                    crash["summary"] = key["V1 First Event"]

                crashes.append(crash)
                manual_crash_id += 1

            elif args.destination == "dc":
                # skip crashes that don't have a date, X and Y
                if key["REPORTDATE"] == "" or key["X"] == "" or key["Y"] == "":
                    continue

                crash = OrderedDict([
                    ("id", key["OBJECTID"]),
                    ("dateOccurred", key["REPORTDATE"]),
                    ("location", OrderedDict([
                        ("latitude", float(key["Y"])),
                        ("longitude", float(key["X"]))
                    ]))
                ])

                if key["TOTAL_VEHICLES"] != 0 or key["TOTAL_BICYCLES"] != 0:
                    crash["vehicles"] = []

                    if key["TOTAL_VEHICLES"] != 0 and key["TOTAL_VEHICLES"] != "":
                        crash["vehicles"].append({"category": "car", "quantity": int(key["TOTAL_VEHICLES"])})

                    if key["TOTAL_BICYCLES"] != 0 and key["TOTAL_BICYCLES"] != "":
                        crash["vehicles"].append({"category": "bike", "quantity": int(key["TOTAL_BICYCLES"])})

                # TODO persons

                if key["ADDRESS"] != "":
                    crash["address"] = key["ADDRESS"]

                crashes.append(crash)

            else:
                print "transformation of "+args.destination+" crashes not yet implemented"
                exit(1)

    print "done, {} crashes loaded, validating against schema".format(len(crashes))

    schema_path = "/app/data_standards/crashes-schema.json"
    with open(schema_path) as crashes_schema:
        validate(crashes, json.load(crashes_schema))

    crashes_output = os.path.join(args.folder, "transformed/crashes.json")

    with open(crashes_output, "w") as f:
        json.dump(crashes, f)

    print "output written to {}".format(crashes_output)
