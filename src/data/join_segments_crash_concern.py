
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
# filepaths of raw crash data (hardcoded for now)
CRASH_DATA_FPS = [
    'cad_crash_events_with_transport_2016_wgs84.csv',
    '2015motorvehicles_with_modetype.csv',
    '2017motorvehicles_with_modetype.csv'
]


def process_concerns(
        concernfile, date_col, x, y, start_year=None, end_year=None):

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

    concern_raw = pd.read_csv(os.path.join(
        RAW_DATA_FP, concernfile))

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
    with open(
            os.path.join(PROCESSED_DATA_FP, 'concern_joined.json'),
            'w'
    ) as f:
        json.dump([c['properties'] for c in concern], f)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-c", "--crashfiles", nargs='+',
                        help="Can give alternate list of crash files. " +
                        "Only use filename, don't include path")
    parser.add_argument("-s", "--safetyconcern", type=str,
                        help="Can give alternate concern file." +
                        "Only use filename, don't include path")
    parser.add_argument("-x_crash", "--x_crash", type=str,
                        help="column name in csv file containing longitude")
    parser.add_argument("-y_crash", "--y_crash", type=str,
                        help="column name in csv file containing latitude")
    parser.add_argument("-t_crash", "--date_col_crash", type=str,
                        help="col name in crash csv file containing date")
    parser.add_argument("-t_concern", "--date_col_concern", type=str,
                        help="col name in concern csv file containing date")
    parser.add_argument("-x_concern", "--x_concern", type=str,
                        help="column name in csv file containing longitude")
    parser.add_argument("-y_concern", "--y_concern", type=str,
                        help="column name in csv file containing latitude")
    parser.add_argument("-start", "--startyear", type=str,
                        help="Can limit data to crashes this year or later")
    parser.add_argument("-end", "--endyear", type=str,
                        help="Can limit data to crashes this year or earlier")

    args = parser.parse_args()
    # Can override the hardcoded data directory
    if args.datadir:
        RAW_DATA_FP = os.path.join(args.datadir, 'raw')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(args.datadir, 'processed/maps')
    if args.crashfiles:
        CRASH_DATA_FPS = args.crashfiles

    x_crash = 'X'
    y_crash = 'Y'
    y_concern = 'Y'
    x_concern = 'X'
    if args.x_concern:
        x_concern = args.x_concern
    if args.x_crash:
        x_crash = args.x_crash
    if args.y_crash:
        y_crash = args.y_crash
    if args.y_concern:
        y_concern = args.y_concern

    safetyconcern = 'Vision_Zero_Entry.csv'
    if args.safetyconcern:
        safetyconcern = args.safetyconcern

    # Read in CAD crash data
    crash = []
    for fp in CRASH_DATA_FPS:

        tmp = util.csv_to_projected_records(
            os.path.join(RAW_DATA_FP, fp),
            x=x_crash,
            y=y_crash
        )
        crash = crash + tmp

    crash_with_date = []
    count = 0
    # Keep track of the earliest and latest crash date used
    start = None
    end = None
    for i in range(len(crash)):
        # If the date column given in the crash data isn't
        # 'CALENDAR_DATE', copy the date column to 'CALENDAR_DATE'
        # for standardization
        match_date = True
        if args.date_col_crash:
            if crash[i]['properties'][args.date_col_crash]:
                d = parse(
                    crash[i]['properties'][args.date_col_crash]).isoformat()
                crash[i]['properties']['CALENDAR_DATE'] = d

        # If there's no date given
        if not crash[i]['properties']['CALENDAR_DATE']:
            match_date = False
            count += 1
        else:
            year = parse(
                crash[i]['properties']['CALENDAR_DATE']).year

            # If the start year given is earlier than the crash year, skip
            if args.startyear and int(args.startyear) > year:
                match_date = False
            # Or the end year is later than the crash year, skip
            elif args.endyear and int(args.endyear) < year:
                match_date = False

        if match_date:

            crash_with_date.append(crash[i])

            if not start or start > crash[i]['properties']['CALENDAR_DATE']:
                start = crash[i]['properties']['CALENDAR_DATE']
            if not end or end < crash[i]['properties']['CALENDAR_DATE']:
                end = crash[i]['properties']['CALENDAR_DATE']

    if count:
        print str(count) + " out of " + str(len(crash)) \
            + " don't have a date, skipping"
    crash = crash_with_date

    print "Read in data from {} crashes from {} to {}".format(
        len(crash), parse(start).date(), parse(end).date())

    combined_seg, segments_index = util.read_segments(dirname=MAP_FP)

    # Find nearest crashes - 30 tolerance
    print "snapping crashes to segments"

    util.find_nearest(crash, combined_seg, segments_index, 30)

    # Write crash
    crash_schema = util.make_schema('Point', crash[0]['properties'])
    print "output crash shp to", MAP_FP
    util.write_shp(crash_schema, os.path.join(MAP_FP, 'crash_joined.shp'),
                   crash, 'point', 'properties')
    print "output crash data to", PROCESSED_DATA_FP
    with open(os.path.join(PROCESSED_DATA_FP, 'crash_joined.json'), 'w') as f:
        json.dump([c['properties'] for c in crash], f)

    date_col_concern = args.date_col_concern or 'REQUESTDATE'
    process_concerns(
        safetyconcern, date_col_concern, x_concern, y_concern,
        start_year=args.startyear, end_year=args.endyear
    )
