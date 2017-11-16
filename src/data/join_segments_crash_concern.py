
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import json
import pyproj
import pandas as pd
import util
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = BASE_DIR + '/data/processed/maps'
RAW_DATA_FP = BASE_DIR + '/data/raw'
PROCESSED_DATA_FP = BASE_DIR + '/data/processed'
# filepaths of raw crash data (hardcoded for now)
CRASH_DATA_FPS = [
    '/cad_crash_events_with_transport_2016_wgs84.csv',
    '/2015motorvehicles_formatted.csv',
    '/2017motorvehicles_formatted.csv'
]


def make_schema(geometry, properties):
    """
    Utility for making schema with 'str' value for each key in properties
    """
    properties_dict = {k: 'str' for k, v in properties.items()}
    schema = {
        'geometry': geometry,
        'properties': properties_dict
    }
    return(schema)
    

if __name__ == '__main__':

    # Read in CAD crash data
    crash = []
    for fp in CRASH_DATA_FPS:
        tmp = util.csv_to_projected_records(RAW_DATA_FP + fp)
        crash = crash + tmp
    print "Read in data from {} crashes".format(len(crash))

    # Read in vision zero data
    concern = []
    # Have to use pandas read_csv, unicode trubs
    concern_raw = pd.read_csv(RAW_DATA_FP + '/Vision_Zero_Entry.csv')
    concern_raw = concern_raw.to_dict('records')
    for r in concern_raw:
        concern.append(
            util.read_record(r, r['X'], r['Y'],
                        orig=pyproj.Proj(init='epsg:4326'))
        )
    print "Read in data from {} concerns".format(len(concern))

    combined_seg, segments_index = util.read_segments()

    # Find nearest crashes - 30 tolerance
    print "snapping crashes to segments"
    util.find_nearest(crash, combined_seg, segments_index, 30)

    # Find nearest concerns - 20 tolerance
    print "snapping concerns to segments"
    util.find_nearest(concern, combined_seg, segments_index, 20)

    # Write concerns
    concern_schema = make_schema('Point', concern[0]['properties'])
    print "output concerns shp to ", MAP_FP
    util.write_shp(concern_schema, MAP_FP + '/concern_joined.shp',
                       concern, 'point', 'properties')
    print "output concerns data to ", PROCESSED_DATA_FP
    with open(PROCESSED_DATA_FP + '/concern_joined.json', 'w') as f:
        json.dump([c['properties'] for c in concern], f)

    # Write crash
    crash_schema = make_schema('Point', crash[0]['properties'])
    print "output crash shp to ", MAP_FP
    util.write_shp(crash_schema, MAP_FP + '/crash_joined.shp',
                       crash, 'point', 'properties')
    print "output crash data to ", PROCESSED_DATA_FP
    with open(PROCESSED_DATA_FP + '/crash_joined.json', 'w') as f:
        json.dump([c['properties'] for c in crash], f)

