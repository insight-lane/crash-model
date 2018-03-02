
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


def process_concerns():
    # Read in vision zero data
    # Have to use pandas read_csv, unicode trubs

    path = os.path.join(
        RAW_DATA_FP, 'Vision_Zero_Entry.csv')

    # Only read in if the file exists
    # Since at the moment, only Boston has concern data, this is
    # still hard coded in, but should change this
    if not os.path.exists(path):
        print "No concern data found"
        return

    concern_raw = pd.read_csv(os.path.join(
        RAW_DATA_FP, 'Vision_Zero_Entry.csv'))
    concern_raw = concern_raw.to_dict('records')
    concern = util.raw_to_record_list(concern_raw,
                                      pyproj.Proj(init='epsg:4326'))
    print "Read in data from {} concerns".format(len(concern))

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
    parser.add_argument("-x", "--longitude", type=str,
                        help="column name in csv file containing longitude")
    parser.add_argument("-y", "--latitude", type=str,
                        help="column name in csv file containing latitude")
    parser.add_argument("-t", "--datecol", type=str,
                        help="col name in crash csv file containing date")

    args = parser.parse_args()

    # Can override the hardcoded data directory
    if args.datadir:
        RAW_DATA_FP = os.path.join(args.datadir, 'raw')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(args.datadir, 'processed/maps')
    if args.crashfiles:
        CRASH_DATA_FPS = args.crashfiles

    longitude = 'X'
    latitude = 'Y'
    if args.longitude:
        longitude = args.longitude
    if args.latitude:
        latitude = args.latitude

    # Read in CAD crash data
    crash = []
    for fp in CRASH_DATA_FPS:
        tmp = util.csv_to_projected_records(
            os.path.join(RAW_DATA_FP, fp),
            x=longitude,
            y=latitude
        )
        crash = crash + tmp

    if args.datecol:
        for i in range(len(crash)):
            d = parse(crash[i]['properties'][args.datecol]).isoformat()
            crash[i]['properties']['CALENDAR_DATE'] = d

    print "Read in data from {} crashes".format(len(crash))

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

    process_concerns()
