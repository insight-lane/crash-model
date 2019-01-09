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
import pytz
import dateutil.parser as date_parser
from .standardization_util import parse_date, validate_and_write_schema

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))

def read_standardized_fields(raw_crashes, fields, opt_fields,
                             timezone, startdate=None, enddate=None):

    crashes = {}
    # Drop times from startdate/enddate in the unlikely event
    # they're passed in
    if startdate:
        startdate = parse_date(startdate, timezone)
        startdate = date_parser.parse(startdate).date()
    if enddate:
        enddate = parse_date(enddate, timezone)
        enddate = date_parser.parse(enddate).date()

    min_date = None
    max_date = None
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
                crash_date = str(crash[fields["date_year"]]) + "-" + str(
                    crash[fields["date_month"]]) + "-" + crash[fields["date_day"]]
            # some cities do not supply a day of month for crashes, randomize if so
            else:
                available_dates = calendar.Calendar().itermonthdates(
                    crash[fields["date_year"]], crash[fields["date_month"]])
                crash_date = str(random.choice(
                    [date for date in available_dates if date.month == crash[fields["date_month"]]]))

        # skip any crashes that don't have a date
        else:
            continue

        crash_time = None
        if fields["time"]:
            crash_time = crash[fields["time"]]

        if fields["time_format"]:
            crash_date_time = parse_date(
                crash_date,
                timezone,
                crash_time,
                fields["time_format"]
            )

        else:
            crash_date_time = parse_date(
                crash_date,
                timezone,
                crash_time
            )

        # Skip crashes where date can't be parsed
        if not crash_date_time:
            continue

        crash_day = date_parser.parse(crash_date_time).date()
        # Drop crashes that occur outside of the range, if specified
        if ((startdate is not None and crash_day < startdate) or
                (enddate is not None and crash_day > enddate)):

            continue
        if min_date is None or crash_day < min_date:
            min_date = crash_day
        if max_date is None or crash_day > max_date:
            max_date = crash_day
            
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

    if min_date and max_date:
        print("Including crashes between {} and {}".format(
            min_date.isoformat(), max_date.isoformat()))
    elif min_date:
        print("Including crashes after {}".format(
            min_date.isoformat()))
    elif max_date:
        print("Including crashes before {}".format(
            max_date.isoformat()))

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
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="config file")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="data directory")

    args = parser.parse_args()

    # load config
    config_file = args.config
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # by default standardize all available crashes
    startdate = None
    enddate = None

    if config['startdate']:
        startdate = str(config['startdate'])

    if config['enddate']:
        enddate = str(config['enddate'])

    crash_dir = os.path.join(args.datadir, "raw/crashes")
    if not os.path.exists(crash_dir):
        raise SystemExit(crash_dir + " not found, exiting")

    print("searching "+crash_dir+" for raw files:")
    dict_crashes = {}

    for csv_file in list(config['crashes_files'].keys()):
        csv_config = config['crashes_files'][csv_file]

        if not os.path.exists(os.path.join(crash_dir, csv_file)):
            raise SystemExit(os.path.join(
                crash_dir, csv_file) + " not found, exiting")

        add_id(
            os.path.join(crash_dir, csv_file), csv_config['required']['id'])

        print("processing {}".format(csv_file))

        df_crashes = pd.read_csv(os.path.join(
            crash_dir, csv_file), na_filter=False)
        raw_crashes = df_crashes.to_dict("records")

        std_crashes = read_standardized_fields(
            raw_crashes,
            csv_config['required'],
            csv_config['optional'],
            pytz.timezone(config['timezone']),
            startdate,
            enddate
        )

        print("{} crashes loaded with standardized fields, checking for specific fields".format(
            len(std_crashes)))
        dict_crashes.update(std_crashes)

    print("{} crashes loaded, validating against schema".format(len(dict_crashes)))

    schema_path = os.path.join(BASE_FP, "standards", "crashes-schema.json")
    list_crashes = list(dict_crashes.values())
    crashes_output = os.path.join(args.datadir, "standardized/crashes.json")
    validate_and_write_schema(schema_path, list_crashes, crashes_output)
