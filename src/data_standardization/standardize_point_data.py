import argparse
import os
import pandas as pd
from collections import OrderedDict
import yaml
from . import standardization_util

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(CURR_FP)
DATA_FP = None


def read_file_info(config):

    points = []
    for source_config in list(config['data_source']):
        csv_file = source_config['filename']
        filepath = os.path.join(DATA_FP, 'raw', 'supplemental', csv_file)
        if not os.path.exists(filepath):
            raise SystemExit(csv_file + " not found, exiting")

        df = pd.read_csv(filepath, na_filter=False)
        rows = df.to_dict("records")

        for row in rows:
            lat = None
            lon = None
            if 'address' in source_config:
                lat, lon = standardization_util.parse_address(
                    rows[100][source_config['address']])
            if lat and lon:

                time = None
                if 'time' in source_config and source_config['time']:
                    time = source_config['time']

                date_time = standardization_util.parse_date(
                    row[source_config['date']], row[time])
                updated_row = OrderedDict([
                    ("source", source_config["name"]),
                    ("date", date_time),
                    ("location", OrderedDict([
                        ("latitude", lat),
                        ("longitude", lon)
                    ]))
                ])

                if "category" in source_config and source_config['category']:
                    updated_row['category'] = row[source_config['category']]
                if "notes" in source_config and source_config['notes']:
                    updated_row['notes'] = row[source_config['notes']]

                points.append(updated_row)

    if points:

        schema_path = os.path.join(os.path.dirname(BASE_FP),
                                   "standards", "points-schema.json")
        output = os.path.join(DATA_FP, "standardized", "points.json")
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
    DATA_FP = args.datadir
    # load config for this city
    config_file = os.path.join(BASE_FP, args.config)
    with open(config_file) as f:
        config = yaml.safe_load(f)

    if 'data_source' in config:
        read_file_info(config)

    