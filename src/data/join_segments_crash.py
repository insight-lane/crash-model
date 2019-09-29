
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
from . import util
import os
import argparse
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd
import data.config


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
RAW_DATA_FP = os.path.join(BASE_DIR, 'data/standardized')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def snap_records(
        combined_seg, segments_index, infile,
        startyear=None, endyear=None):

    print("reading crash data...")
    records = util.read_records(infile, 'crash', startyear, endyear)

    # Find nearest crashes - 30 tolerance
    print("snapping crash records to segments")
    util.find_nearest(
        records, combined_seg, segments_index, 30, type_record=True)
    record_num = len(records)
    records = [x for x in records if x.near_id]
    dropped_records = record_num - len(records)
    if dropped_records:
        print("Dropped {} crashes that don't map to a segment".format(dropped_records))
        print("{} crashes remain".format(len(records)))
    jsonfile = os.path.join(
        PROCESSED_DATA_FP, 'crash_joined.json')

    print("output crash data to " + jsonfile)
    with open(jsonfile, 'w') as f:
        json.dump([r.properties for r in records], f)


def make_crash_rollup(crashes_json, split_columns=[]):
    """
    Generates a GeoDataframe with the total number of crashes, number of bike,
    pedestrian and vehicle crashes, along with a comma-separated string
    of crash dates per unique lat/lng pair

    Inputs:
        - a json of standardized crash data

    Output:
        - a list of GeoDataframes
          (one for the total counts, and one for each split_column)
          Each GeoDataFrame has the following columns:
            - total number of crashes
            - list of unique dates that crashes occurred
            - GeoJSON point features created from the latitude and longitude
    """

    crash_locations = {
        'all': {}
    }
    for column in split_columns:
        crash_locations[column] = {}

    # Make multiple crash rollup files
    for crash in crashes_json:
        loc = (crash['location']['longitude'], crash['location']['latitude'])

        if loc not in crash_locations['all']:
            crash_locations['all'][loc] = {
                'coordinates': Point(loc),
                'total_crashes': 0,
                'crash_dates': [],
            }
        crash_locations['all'][loc]['total_crashes'] += 1
        date = crash['dateOccurred']

        crash_locations['all'][loc]['crash_dates'].append(date)
        for column in split_columns:
            if column in crash:
                if loc not in crash_locations[column]:
                    crash_locations[column][loc] = {
                        'coordinates': Point(loc),
                        'total_crashes': 0,
                        'crash_dates': [],
                    }
                crash_locations[column][loc]['total_crashes'] += 1
                crash_locations[column][loc]['crash_dates'].append(crash['dateOccurred'])

    crashes_agg = {}
    for crash_type in crash_locations.keys():
        crashes_agg_gdf = gpd.GeoDataFrame(
            pd.DataFrame.from_dict(crash_locations[crash_type], orient='index'),
            geometry='coordinates'
        )
        crashes_agg_gdf.index = range(len(crashes_agg_gdf))
        crashes_agg_gdf['crash_dates'] = crashes_agg_gdf['crash_dates'].apply(
            lambda x: ",".join(sorted(set(x))))
        crashes_agg[crash_type] = crashes_agg_gdf

    return crashes_agg

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="Config file", required=True)
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-start", "--startyear", type=str,
                        help="Can limit data to crashes this year or later")
    parser.add_argument("-end", "--endyear", type=str,
                        help="Can limit data to crashes this year or earlier")

    args = parser.parse_args()
    config = data.config.Configuration(args.config)
    
    # Can override the hardcoded data directory
    if args.datadir:
        RAW_DATA_FP = os.path.join(args.datadir, 'standardized')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(args.datadir, 'processed/maps')

    combined_seg, segments_index = util.read_segments(dirname=MAP_FP)
    snap_records(
        combined_seg, segments_index,
        os.path.join(RAW_DATA_FP, 'crashes.json'),
        startyear=args.startyear, endyear=args.endyear)

    with open(os.path.join(PROCESSED_DATA_FP, 'crash_joined.json')) as crash_file:
        data = json.load(crash_file)
    crashes_agg_list = make_crash_rollup(data, config.split_columns)

    crashes_agg_path = os.path.join(
        args.datadir, "processed", "crashes_rollup.geojson")
    if os.path.exists(crashes_agg_path):
        os.remove(crashes_agg_path)

    for split, crashes_agg_gdf in crashes_agg_list.items():
        if split == 'all':
            filename = os.path.join(
                args.datadir,
                "processed",
                "crashes_rollup.geojson"
            )
        else:
            filename = os.path.join(
                args.datadir,
                "processed",
                "crashes_rollup_" + split + ".geojson"
            )
        crashes_agg_gdf.to_file(
            filename,
            driver="GeoJSON"
        )
