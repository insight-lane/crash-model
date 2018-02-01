# -*- coding: utf-8 -*-
import os
import subprocess

# Until we're ready to switch over to using this data,
# use osm-data as data directory instead of data
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
        DATA_FP
    ])
    # Extract intersections from the open street map data
    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        DATA_FP + '/processed/maps/osm_ways.shp',
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
        DATA_FP + '/processed/maps/osm_ways_3857.shp'
    ])

    # Extract intersections from the Boston data
    # Write them to a subdirectory so files created from osm aren't overwritten
    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        DATA_FP + '/raw/Boston_Segments.shp',
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
    
    # Map the boston segments to the open street map segments and add features
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
        DATA_FP + '/processed/'
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
        '-f',
        'AADT,SPEEDLIMIT,Struct_Cnd,Surface_Tp,F_F_Class,width,lanes,hwy_type,osm_speed',
    ])
