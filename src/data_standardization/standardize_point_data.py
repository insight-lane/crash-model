import argparse
import os
import pandas as pd
from collections import OrderedDict
from . import standardization_util
import data.config

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(CURR_FP)


def read_file_info(config, datadir):

    points = []
    for source_config in list(config.data_source):

        print("Processing {} data".format(source_config['name']))
        csv_file = source_config['filename']
        filepath = os.path.join(datadir, 'raw', 'supplemental', csv_file)
        if not os.path.exists(filepath):
            raise SystemExit(csv_file + " not found, exiting")

        df = pd.read_csv(filepath, na_filter=False)
        rows = df.to_dict("records")
        missing = 0
        missing_date = 0
        for row in rows:
            lat = None
            lon = None
            if 'latitude' in source_config and 'longitude' in source_config:
                lat = row[source_config['latitude']]
                lon = row[source_config['longitude']]
            elif 'address' in source_config:
                _, lat, lon = standardization_util.parse_address(
                    row[source_config['address']])
            if lat and lon:
                time = None
                
                if 'time' in source_config and source_config['time']:
                    time = row[source_config['time']]
                date_time = row[source_config['date']]
                if not date_time:
                    missing_date += 1
                    continue
                date_time = standardization_util.parse_date(
                    row[source_config['date']], config.timezone, time=time)
                updated_row = OrderedDict([
                    ("feature", source_config["name"]),
                    ("date", date_time),
                    ("location", OrderedDict([
                        ("latitude", float(lat)),
                        ("longitude", float(lon))
                    ]))
                ])
                if "category" in source_config and source_config['category']:
                    updated_row['category'] = row[source_config['category']]
                if "notes" in source_config and source_config['notes']:
                    updated_row['notes'] = row[source_config['notes']]
                if "feat_agg" in source_config and source_config['feat_agg']:
                    updated_row['feat_agg'] = source_config['feat_agg']
                if "value" in source_config and source_config['value']:
                    updated_row['value'] = row[source_config['value']]

                points.append(updated_row)
            else:
                missing += 1

        if missing:
            print("{} entries didn't have a lat/lon".format(missing))
        if missing_date:
            print("{} entries didn't have a date".format(missing_date))
    if points:

        schema_path = os.path.join(os.path.dirname(BASE_FP),
                                   "standards", "points-schema.json")
        output = os.path.join(datadir, "standardized", "points.json")
        standardization_util.validate_and_write_schema(
            schema_path, points, output)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="config file for city")
    parser.add_argument("-d", "--datadir", type=str,
                        help="path to destination's data folder," +
                        "e.g. ../data/boston")

    args = parser.parse_args()

    # load config for this city
    config_file = os.path.join(BASE_FP, args.config)
    config = data.config.Configuration(config_file)
    if config.data_source:
        read_file_info(config, args.datadir)
    else:
        print("No point data found, skipping")    
