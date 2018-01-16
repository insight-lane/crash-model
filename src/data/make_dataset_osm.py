# -*- coding: utf-8 -*-
import os
import subprocess

DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/osm-data/'


if __name__ == '__main__':

    city = 'Boston, Massachusetts, USA'

    # Get the maps out of open street map, both projections
    subprocess.check_call([
        'python',
        '-m',
        'data.osm_create_maps',
        city,
        DATA_FP,
        '--forceupdate'
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        DATA_FP + '/processed/maps/osm_ways.shp',
        '-d',
        DATA_FP
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        DATA_FP,
        '-r',
        DATA_FP + '/processed/maps/osm_ways_3857.shp'
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.join_segments_crash_concern',
        '-d',
        DATA_FP
    ])
    subprocess.check_call([
        'python',
        '-m',
        'data.ATR_scraping.geocode_snap_ATRs',
        '-d',
        DATA_FP + '/processed/'
    ])
