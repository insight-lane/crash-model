
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
from . import util
import os
import argparse

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

    jsonfile = os.path.join(
        PROCESSED_DATA_FP, 'crash_joined.json')

    print("output crash data to " + jsonfile)
    with open(jsonfile, 'w') as f:
        json.dump([r.properties for r in records], f)


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

