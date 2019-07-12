
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
from . import util
import os
import argparse
from pandas.io.json import json_normalize
from shapely.geometry import Point
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


def calculate_crashes_by_location(df):
    """
    Calculates total number of crashes that occurred at each unique lat/lng pair and
    generates a comma-separated string of the dates that crashes occurred at that location

    Inputs:
        - a dataframe where each row represents one unique crash incident

    Output:
        - a dataframe with the total number of crashes at each unique crash location
          and list of unique crash dates
    """
    crashes_agg = df.groupby(['latitude', 'longitude']).agg(['count', 'unique'])
    crashes_agg.columns = crashes_agg.columns.get_level_values(1)
    crashes_agg.rename(columns={'count': 'total_crashes', 'unique': 'crash_dates'}, inplace=True)
    crashes_agg.reset_index(inplace=True)
    
    crashes_agg['crash_dates'] = crashes_agg['crash_dates'].str.join(',')
    return crashes_agg


def make_crash_rollup(crashes_json):
    """
    Generates a GeoDataframe with the total number of crashes and a comma-separated string
    of crash dates per unique lat/lng pair

    Inputs:
        - a json of standardized crash data

    Output:
        - a GeoDataframe with the following columns:
            - total number of crashes
            - list of unique dates that crashes occurred
            - GeoJSON point features created from the latitude and longitude
    """
    df_std_crashes = json_normalize(crashes_json)
    df_std_crashes = df_std_crashes[
        ["dateOccurred", "location.latitude", "location.longitude"]]
    df_std_crashes.rename(columns={
        "location.latitude": "latitude",
        "location.longitude": "longitude"
    }, inplace=True)

    crashes_agg = calculate_crashes_by_location(df_std_crashes)
    crashes_agg["coordinates"] = list(zip(
        crashes_agg.longitude, crashes_agg.latitude))
    crashes_agg["coordinates"] = crashes_agg["coordinates"].apply(Point)
    crashes_agg = crashes_agg[["coordinates", "total_crashes", "crash_dates"]]

    crashes_agg_gdf = gpd.GeoDataFrame(crashes_agg, geometry="coordinates")

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
