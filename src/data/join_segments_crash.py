
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


def make_crash_rollup(crashes_json):
    """
    Generates a GeoDataframe with the total number of crashes, number of bike,
    pedestrian and vehicle crashes, along with a comma-separated string
    of crash dates per unique lat/lng pair

    Inputs:
        - a json of standardized crash data

    Output:
        - a GeoDataframe with the following columns:
            - total number of crashes
            - total number of bike crashes
            - total number of pedestrian crashes
            - total number of vehicle crashes
            - list of unique dates that crashes occurred
            - GeoJSON point features created from the latitude and longitude
    """

    crash_locations = {}
    for crash in crashes_json:
        loc = (crash['location']['longitude'], crash['location']['latitude'])
        if loc not in crash_locations:
            crash_locations[loc] = {
                'coordinates': Point(loc),
                'total_crashes': 0,
                'crash_dates': [],
            }
            if 'mode' in crash and crash['mode']:
                crash_locations[loc]['pedestrian'] = 0
                crash_locations[loc]['bike'] = 0
                crash_locations[loc]['vehicle'] = 0
        crash_locations[loc]['total_crashes'] += 1
        if 'mode' in crash and crash['mode']:
            crash_locations[loc][crash['mode']] += 1
        crash_locations[loc]['crash_dates'].append(crash['dateOccurred'])
    crashes_agg_gdf = gpd.GeoDataFrame(
        pd.DataFrame.from_dict(crash_locations, orient='index'),
        geometry='coordinates'
    )
    crashes_agg_gdf.index = range(len(crashes_agg_gdf))
    crashes_agg_gdf['crash_dates'] = crashes_agg_gdf['crash_dates'].apply(
        lambda x: ",".join(sorted(set(x))))

    return crashes_agg_gdf


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-start", "--startyear", type=str,
                        help="Can limit data to crashes this year or later")
    parser.add_argument("-end", "--endyear", type=str,
                        help="Can limit data to crashes this year or earlier")

    args = parser.parse_args()

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
    crashes_agg_gdf = make_crash_rollup(data)

    crashes_agg_path = os.path.join(
        args.datadir, "processed", "crashes_rollup.geojson")
    if os.path.exists(crashes_agg_path):
        os.remove(crashes_agg_path)

    crashes_agg_gdf.to_file(
        os.path.join(args.datadir, "processed", "crashes_rollup.geojson"),
        driver="GeoJSON"
    )
