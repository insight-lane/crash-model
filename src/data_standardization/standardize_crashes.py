# Standardize a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import os
import pandas as pd
import yaml
from collections import OrderedDict
import csv
import calendar
import random
from .standardization_util import parse_date, validate_and_write_schema

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))


def read_standardized_fields(raw_crashes, fields, opt_fields):

    crashes = {}

    for i, crash in enumerate(raw_crashes):
        if i % 10000 == 0:
            print(i)
        
        # skip any crashes that don't have coordinates
        if crash[fields["latitude"]] == "" or crash[fields["longitude"]] == "":
            continue
        
        # construct crash date based on config settings, skipping any crashes without date
        if fields["date_complete"]:
            if not crash[fields["date_complete"]]:
                continue
                
            else:
                crash_date = crash[fields["date_complete"]]
            
        elif fields["date_year"] and fields["date_month"]:
            if fields["date_day"]:
                crash_date = str(crash[fields["date_year"]]) + "-" + str(crash[fields["date_month"]]) + "-" + crash[fields["date_day"]]
            # some cities do not supply a day of month for crashes, randomize if so
            else:
                available_dates = calendar.Calendar().itermonthdates(
                    crash[fields["date_year"]], crash[fields["date_month"]])
                crash_date = str(random.choice([date for date in available_dates if date.month == crash[fields["date_month"]]]))
                
        # skip any crashes that don't have a date
        else:
            continue

        crash_time = None
        if fields["time"]:
            crash_time = crash[fields["time"]]
        
        if fields["time_format"]:
            crash_date_time = parse_date(
                crash_date,
                crash_time,
                fields["time_format"]
            )
            
        else:
            crash_date_time = parse_date(
                crash_date,
                crash_time
            )
            
        # Skip crashes where date can't be parsed
        if not crash_date_time:
            continue

        formatted_crash = OrderedDict([
            ("id", crash[fields["id"]]),
            ("dateOccurred", crash_date_time),
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
    if "summary" in list(fields.keys()) and fields["summary"]:
        formatted_crash["summary"] = crash[fields["summary"]]
    if "address" in list(fields.keys()) and fields["address"]:
        formatted_crash["address"] = crash[fields["address"]]

    # setup a vehicles list for each crash
    formatted_crash["vehicles"] = []

    # check for car involvement
    if "vehicles" in list(fields.keys()) and fields["vehicles"] == "mode_type":
        # this needs work, but for now any of these mode types
        # translates to a car being involved, quantity unknown
        if crash[fields["vehicles"]] == "mv" or crash[fields["vehicles"]] == "ped" or crash[fields["vehicles"]] == "":
            formatted_crash["vehicles"].append({"category": "car"})

    elif "vehicles" in list(fields.keys()) and fields["vehicles"] == "TOTAL_VEHICLES":
        if crash[fields["vehicles"]] != 0 and crash[fields["vehicles"]] != "":
            formatted_crash["vehicles"].append({
                "category": "car",
                "quantity": int(crash[fields["vehicles"]])
            })

    # check for bike involvement
    if "bikes" in list(fields.keys()) and fields["bikes"] == "mode_type":
        # assume bike and car involved, quantities unknown
        if crash[fields["bikes"]] == "bike":
            formatted_crash["vehicles"].append({"category": "car"})
            formatted_crash["vehicles"].append({"category": "bike"})

    elif "bikes" in list(fields.keys()) and fields["bikes"] == "TOTAL_BICYCLES":
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
            writer = csv.DictWriter(f, list(rows[0].keys()))
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
        print(raw_path+" not found, exiting")
        exit(1)

    # load config for this city
    config_file = os.path.join(BASE_FP, 'src/config',
                               "config_"+args.destination+".yml")
    with open(config_file) as f:
        config = yaml.safe_load(f)

    dict_city_crashes = {}
    print("searching "+raw_path+" for raw files:\n")

    for csv_file in list(config['crashes_files'].keys()):

        if not os.path.exists(os.path.join(raw_path, csv_file)):
            raise SystemExit(csv_file + " not found, exiting")
        # find the config for this crash file
        crash_config = config['crashes_files'][csv_file]
        if crash_config is None:
            print("- could not find config for crash file "+csv_file+", skipping")
            continue

        add_id(
            os.path.join(raw_path, csv_file), crash_config['required']['id'])

        print("processing "+csv_file)

        df_crashes = pd.read_csv(os.path.join(raw_path, csv_file), na_filter=False)
        raw_crashes = df_crashes.to_dict("records")

        std_crashes = read_standardized_fields(raw_crashes,
                            crash_config['required'], crash_config['optional'])
        print("- {} crashes loaded with standardized fields, checking for specific fields\n".format(len(std_crashes)))
        dict_city_crashes.update(std_crashes)

    print("all crash files processed")
    print("- {} {} crashes loaded, validating against schema".format(len(dict_city_crashes), args.destination))

    schema_path = os.path.join(BASE_FP, "standards", "crashes-schema.json")
    list_city_crashes = list(dict_city_crashes.values())
    crashes_output = os.path.join(args.folder, "standardized/crashes.json")
    validate_and_write_schema(schema_path, list_city_crashes, crashes_output)
