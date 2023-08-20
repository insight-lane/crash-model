import argparse
import os
import pandas as pd
from collections import OrderedDict
from . import standardization_util
import data.config

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(CURR_FP)

def process_row(row: dict, row_config: dict) -> OrderedDict:
    """
    Function to process a row of pbf data
    Args:
        row: dictionary of data from pdf
        row_config: dictionary derived from config yaml
    Returns: dict with appropriate values
    """
    new_row = OrderedDict()
    if "category" in row_config and row_config['category']:
        new_row['category'] = row[row_config['category']]
    if "value" in row_config and row_config['value']:
        # value must be numeric
        val = row[row_config['value']]
        if type(val) not in (int, float):
            val = pd.to_numeric(val).item()
        new_row['value'] = val
    if "notes" in row_config and row_config['notes']:
        new_row['notes'] = row[row_config['notes']]
    if "feat_agg" in row_config and row_config['feat_agg']:
        new_row['feat_agg'] = row_config['feat_agg']
    return(new_row)

def read_file_info(config: data.config.Configuration,
                   datadir: str) -> None:
    """
    Reads information from additional point based feature files, processes, validates and writes them
    Args:
        config: project configuration object
        datadir: filepath for point based features
    Returns: None, writes output directly

    """

    points = []
    for source_config in list(config.data_source):

        print("Processing {} data".format(source_config['filename']))
        csv_file = source_config['filename']
        filepath = os.path.join(datadir, 'raw', 'supplemental', csv_file)
        if not os.path.exists(filepath):
            # automatically check the raw/crashes directory
            print(f"{filepath} not found, trying 'raw/crashes' directory")
            filepath = os.path.join(datadir, 'raw', 'crashes', csv_file)
            if not os.path.exists(filepath):
                raise SystemExit(filepath + " not found, exiting")

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
                    str(row[source_config['date']]), config.timezone, time=time)

                updated_row = OrderedDict([
                    ("date", date_time),
                    ("location", OrderedDict([
                        ("latitude", float(lat)),
                        ("longitude", float(lon))
                    ]))
                ])

                # process for multiple features
                if 'feats' in source_config:
                    for feat in source_config['feats']:
                        updated_row['feature'] = feat['name']
                        feat_row = process_row(row, feat)
                        feat_row.update(updated_row)
                        points.append(feat_row)
                else:
                    updated_row['feature'] = source_config['name']
                    updated_row.update(process_row(row, source_config))
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
