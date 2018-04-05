
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
import util
import os
import argparse

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
RAW_DATA_FP = os.path.join(BASE_DIR, 'data/raw')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def snap_records(
        combined_seg, segments_index, infile, record_type, outfile,
        startyear=None, endyear=None):

    records = util.read_records(infile, record_type, startyear, endyear)

    # Find nearest crashes - 30 tolerance
    print "snapping " + record_type + " records to segments"
    util.find_nearest(
        records, combined_seg, segments_index, 30, type_record=True)

    # Write out snapped records
    schema = records[0].schema
    print "output crash shp to", MAP_FP
    util.records_to_shapefile(
        schema, os.path.join(MAP_FP, 'crash_joined.shp'),
        records
    )
    print "output " + record_type + " data to" + outfile
    with open(outfile, 'w') as f:
        json.dump([r.get_properties() for r in records], f)


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
        RAW_DATA_FP = os.path.join(args.datadir, 'raw')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(args.datadir, 'processed/maps')

    combined_seg, segments_index = util.read_segments(dirname=MAP_FP)

    snap_records(
        combined_seg, segments_index,
        os.path.join(RAW_DATA_FP, 'crashes.json'), 'crash',
        os.path.join(PROCESSED_DATA_FP, 'crash_joined.json'),
        startyear=args.startyear, endyear=args.endyear)

    snap_records(
        combined_seg, segments_index,
        os.path.join(RAW_DATA_FP, 'concerns.json'), 'concern',
        os.path.join(PROCESSED_DATA_FP, 'concern_joined.json'))
