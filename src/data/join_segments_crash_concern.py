
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
import pyproj
import pandas as pd
import util
import os
import argparse
from dateutil.parser import parse
import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
RAW_DATA_FP = os.path.join(BASE_DIR, 'data/raw')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def process_concerns(
        concern_args, start_year=None, end_year=None):

    name, concernfile, y, x, date_col = concern_args.split(',')
    # Default column names
    y = y or 'Y'
    x = x or 'X'
    date_col = date_col or 'REQUESTDATE'

    # Read in vision zero data
    # Have to use pandas read_csv, unicode trubs

    path = os.path.join(
        RAW_DATA_FP, concernfile)

    # Only read in if the file exists
    # Since at the moment, only Boston has concern data, this is
    # still hard coded in, but should change this
    if not os.path.exists(path):
        print "No concern data found"
        return

    concern_raw = pd.read_csv(path)

    concern_all = concern_raw.fillna(value="")

    # First filter out empty dates
    concern_raw = concern_all[concern_all[date_col] != '']

    # If a start year was passed in, filter everything before that year
    if start_year:
        concern_raw = concern_raw[
            pd.to_datetime(concern_all[date_col])
            >= datetime.datetime(year=int(start_year), month=1, day=1)
        ]
    # If an end year is passed in, filter everything after the end of that year
    if end_year:
        concern_raw = concern_raw[
            pd.to_datetime(concern_all[date_col])
            < datetime.datetime(year=int(end_year)+1, month=1, day=1)
        ]

    min_date = parse(min(concern_raw[date_col])).date()
    max_date = parse(max(concern_raw[date_col])).date()
    concern_raw = concern_raw.to_dict('records')
    concern = util.raw_to_record_list(concern_raw,
                                      pyproj.Proj(init='epsg:4326'), x=x, y=y)

    print "Read in data from {} concerns from {} to {}".format(
        len(concern), min_date, max_date
    )

    # Find nearest concerns - 20 tolerance
    print "snapping concerns to segments"
    util.find_nearest(concern, combined_seg, segments_index, 20)

    # Write concerns
    concern_schema = util.make_schema('Point', concern[0]['properties'])
    print "output concerns shp to", MAP_FP
    util.write_shp(
        concern_schema,
        os.path.join(MAP_FP, 'concern_joined.shp'),
        concern, 'point', 'properties')
    print "output concerns data to", PROCESSED_DATA_FP

    outfile = os.path.join(PROCESSED_DATA_FP, name + '_joined.json')
    with open(outfile, 'w') as f:
        json.dump([c['properties'] for c in concern], f)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-start", "--startyear", type=str,
                        help="Can limit data to crashes this year or later")
    parser.add_argument("-end", "--endyear", type=str,
                        help="Can limit data to crashes this year or earlier")

    parser.add_argument('-concerns', '--concern_info', nargs="+",
                        help="A list of comma separated concern info, " +
                        "containing filename, latitude, longitude and " +
                        "time columns",
                        default=['concern,Vision_Zero_Entry.csv,,,'])

    args = parser.parse_args()
    # Can override the hardcoded data directory
    if args.datadir:
        RAW_DATA_FP = os.path.join(args.datadir, 'raw')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(args.datadir, 'processed/maps')

    crash = util.read_records(
        os.path.join(RAW_DATA_FP, 'crashes.json'),
        'crash', args.startyear, args.endyear)
    combined_seg, segments_index = util.read_segments(dirname=MAP_FP)

    # Find nearest crashes - 30 tolerance
    print "snapping crashes to segments"
    util.find_nearest(
        crash, combined_seg, segments_index, 30, type_record=True)

    # Write crash
    crash_schema = crash[0].schema
    print "output crash shp to", MAP_FP
    util.records_to_shapefile(
        crash_schema, os.path.join(MAP_FP, 'crash_joined.shp'),
        crash
    )
    print "output crash data to", PROCESSED_DATA_FP
    with open(os.path.join(PROCESSED_DATA_FP, 'crash_joined.json'), 'w') as f:
        json.dump([c.get_properties() for c in crash], f)

    concerns = args.concern_info

    for concern in concerns:
        process_concerns(
            concern, start_year=args.startyear, end_year=args.endyear
        )
