# Standardize a crashes CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import argparse
import os
import pandas as pd
from collections import OrderedDict
import csv
import calendar
import random
import dateutil.parser as date_parser
from .standardization_util import parse_date, validate_and_write_schema
from data.geocoding_util import read_geocode_cache
import data.config

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))

def validate_coords(crash: dict, lat_field: str, lon_field: str):
    """
    Validates latitude/longitude values, returns numeric values
    Args:
        crash: crash data
        lat_field: lat field name
        lon_field: lon field name
    Returns: tuple of float values or None, if invalid
    """
    if lat_field and lon_field:
        try:
            # if strings, try and convert
            lat = float(crash[lat_field])
            lon = float(crash[lon_field])
        except ValueError:
            return
        if abs(lat) > 90:
            return
        if abs(lon) > 180:
            return
        return lat, lon




def read_standardized_fields(raw_crashes: dict, fields: dict, opt_fields: dict,
                             timezone: str, datadir: str, city: str,
                             startdate=None, enddate=None) -> dict:

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
    
    cached_addresses = {}

    if (not fields['latitude'] or not fields['longitude']):
        if 'address' in opt_fields and opt_fields['address']:
            # load cache for geocode lookup
            geocoded_file = os.path.join(
                    datadir, 'processed', 'geocoded_addresses.csv')
            if os.path.exists(geocoded_file):
                cached_addresses = read_geocode_cache(
                    filename=os.path.join(
                        datadir, 'processed', 'geocoded_addresses.csv'))
            else:

                raise SystemExit(
                    "Need to geocode addresses before standardizing crashes")
        else:
            raise SystemExit(
                "Can't standardize crash data, no lat/lon or address found"
            )

    no_geocoded_count = 0
    for i, crash in enumerate(raw_crashes):
        if i % 10000 == 0:
            print(i)

        lat_lon = validate_coords(crash, fields['latitude'], fields['longitude'])
        if lat_lon:
            lat, lon = lat_lon

        else:
            # skip any crashes that don't have coordinates
            if 'address' not in opt_fields or opt_fields['address'] not in crash:
                continue

            address = crash[opt_fields['address']] + ' ' + city

            # If we have an address, look it up in the geocoded cache
            if address in cached_addresses:
                address, lat, lon, _ = cached_addresses[address]
                if not address:
                    no_geocoded_count += 1
                    continue
            else:
                no_geocoded_count += 1
                continue

        # construct crash date based on config settings, skipping any crashes without date
        if fields["date_complete"]:
            if not crash[fields["date_complete"]]:
                continue

            else:
                crash_date = crash[fields["date_complete"]]

        elif fields["date_year"]:
            # TODO: generally, we don't need date anymore, we should remove it
            # for now, month is always january if unspecified
            date_month = 1
            date_year = int(crash[fields["date_year"]])
            if fields["date_month"]:
                date_month = int(crash[fields["date_month"]])
            if fields["date_day"]:
                crash_date = f'{date_year}-{date_month}-{crash[fields["date_day"]]}'
            # some cities do not supply a day of month for crashes, randomize if so
            else:
                available_dates = calendar.Calendar().itermonthdates(
                    date_year, date_month)
                crash_date = str(random.choice(
                    [date for date in available_dates if date.month == date_month]))
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
                ("latitude", float(lat)),
                ("longitude", float(lon))
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

    # Making sure we have enough entries with lat/lon to continue
    if len(crashes) > 0 and no_geocoded_count/len(raw_crashes) > .9:
        raise SystemExit("Not enough geocoded addresses found, exiting")
    
    return crashes


def add_city_specific_fields(crash, formatted_crash, fields):

    # Add summary and address
    if "summary" in list(fields.keys()) and fields["summary"]:
        formatted_crash["summary"] = crash[fields["summary"]]
    if "address" in list(fields.keys()) and fields["address"]:
        formatted_crash["address"] = crash[fields["address"]]

    # Add all features that have been specified under split_columns
    if 'split_columns' in fields:
        formatted_crash = add_split_columns(crash, formatted_crash, fields)
    return formatted_crash


def add_split_columns(crash, formatted_crash, fields):
    """
    Add any fields specified in the split_columns field of the config
    Args:
        crash - a dict of unformatted crash information
        formatted_crash - a dict with formatted crash fields
        fields - a dict of config information about the crash fields
    Returns:
        formatted_fields
    """
    split_columns = fields['split_columns']

    # Negative splits are all fields that only have a positive value if none of
    # the columns specified in not_column have values, so look at these separately
    negative_splits = [x for x in split_columns if 'not_column' in split_columns[x].keys()]
    splits_dict = {}
    for key, value in split_columns.items():

        if key in negative_splits or 'column_value' not in value or not value['column_name']:
            continue

        if value['column_value'] == 'any' and crash[value['column_name']]:
            splits_dict[key] = 1
        else:
            if crash[value['column_name']] == value['column_value']:
                splits_dict[key] = 1

    for column in negative_splits:
        # These are the columns that can't have a value for the current column to be true
        # E.g. column is vehicle, and bike and pedestrian need to not be present in splits_dict
        compare_columns = split_columns[column]['not_column'].split()
        value = True

        for compare_column in compare_columns:
            if compare_column in splits_dict:
                value = False
        if value:
            splits_dict[column] = 1

    for key, value in splits_dict.items():
        formatted_crash[key] = value

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
    config = data.config.Configuration(config_file)

    crash_dir = os.path.join(args.datadir, "raw/crashes")
    if not os.path.exists(crash_dir):
        raise SystemExit(crash_dir + " not found, exiting")

    print("searching "+crash_dir+" for raw files:")
    dict_crashes = {}

    for csv_file, csv_config in config.crashes_files.items():
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
            config.timezone,
            args.datadir,
            config.city,
            config.startdate,
            config.enddate
        )

        print("{} crashes loaded with standardized fields, checking for specific fields".format(
            len(std_crashes)))
        dict_crashes.update(std_crashes)

    print("{} crashes loaded, validating against schema".format(len(dict_crashes)))

    schema_path = os.path.join(BASE_FP, "standards", "crashes-schema.json")
    list_crashes = list(dict_crashes.values())
    crashes_output = os.path.join(args.datadir, "standardized/crashes.json")
    validate_and_write_schema(schema_path, list_crashes, crashes_output)
