# -*- coding: utf-8 -*-
import os
import subprocess
import argparse

# Until we're ready to switch over to using this data,
# use osm-data as data directory instead of data
DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/osm-data/'

# For this pipeline to run with the boston data, files needed are:
# osm-data/processed/maps/ma_cob*
# osm-data/raw/Boston_Segments.shp
# ATRs and TMCs in osm-data/raw/
# crash data in osm-data/raw/

# Plan is to make only the crash data required

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # Can optionally give a new map file from which new features
    # can be generated
    parser.add_argument("-c", "--cityfile", type=str,
                        help="Can give an additional shapefile")
    args = parser.parse_args()

    # Eventually make this an arg as well:
    city = 'Boston, Massachusetts, USA'

    # Get the maps out of open street map, both projections
    subprocess.check_call([
        'python',
        '-m',
        'data.osm_create_maps',
        city,
        DATA_FP
    ])
    # Extract intersections from the open street map data
    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        os.path.join(DATA_FP, 'processed/maps/osm_ways.shp'),
        '-d',
        DATA_FP
    ])
    # Create segments on the open street map data
    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        DATA_FP,
        '-r',
        os.path.join(DATA_FP, 'processed/maps/osm_ways_3857.shp')
    ])

    if args.cityfile:
        # Extract intersections from the new city file
        # Write to a subdirectory so files created from osm aren't overwritten
        # Eventually, directory of additional files should also be an argument
        subprocess.check_call([
            'python',
            '-m',
            'data.extract_intersections',
            os.path.join(DATA_FP,  '/raw/Boston_Segments.shp'),
            '-d',
            DATA_FP,
            '-n',
            'boston'
        ])
        # Create segments from the Boston data
        subprocess.check_call([
            'python',
            '-m',
            'data.create_segments',
            '-d',
            DATA_FP,
            '-n',
            'boston',
            '-r',
            DATA_FP + '/processed/maps/ma_cob_spatially_joined_streets.shp'
        ])

        # Map the boston segments to the open street map segments
        # and add features
        subprocess.check_call([
            'python',
            '-m',
            'data.add_map',
            DATA_FP,
            DATA_FP + '/processed/maps/boston/'
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
        os.path.join(DATA_FP, 'processed')
    ])
    subprocess.check_call([
        'python',
        '-m',
        'data.TMC_scraping.parse_tmc',
        '-d',
        DATA_FP
    ])
    # Throw in make canonical dataset here too just to keep track
    # of standardized features
    subprocess.check_call([
        'python',
        '-m',
        'features.make_canon_dataset',
        '-d',
        DATA_FP,
        '-f',
#        'AADT,SPEEDLIMIT,Struct_Cnd,Surface_Tp,F_F_Class,width,lanes,hwy_type,osm_speed',
        'width,lanes,hwy_type,osm_speed',
    ])
