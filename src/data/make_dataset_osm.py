# -*- coding: utf-8 -*-
import os
import subprocess
import argparse
import yaml
import sys

DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/data/'

# For this pipeline to run
# crash data needs to be under raw in the data directory given

# Plan is to make only the crash data required

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # Can give a config file
    parser.add_argument("-c", "--config", type=str,
                        help="Can give a different .yml config file")
    args = parser.parse_args()
    config_file = 'data/config.yml'
    if args.config:
        config_file = args.config
    with open(config_file) as f:
        config = yaml.safe_load(f)

    if 'city' not in config.keys() or config['city'] is None:
        sys.exit('City is required in config file')
    city = config['city']

    if 'datadir' in config.keys() and config['datadir']:
        DATA_FP = config['datadir']

    extra_map = None
    additional_features = None
    extra_map3857 = None
    recreate = False
    outputdir = city.split(',')[0]
    if 'extra_map' in config.keys() and config['extra_map']:
        # Require additional features and additional shapefile in 3857 proj
        if 'additional_features' not in config.keys() \
           or config['additional_features'] is None \
           or 'extra_map3857' not in config.keys() \
           or config['extra_map3857'] is None:
            sys.exit("If extra_map is given, additional_features and" +
                     "extra_map3857 are required.")
            
        extra_map = config['extra_map']
        additional_features = config['additional_features'].split()
        extra_map3857 = config['extra_map3857']

    longitude_crash = None
    latitude_crash = None
    date_col_crash = None
    longitude_concern = None
    latitude_concern = None
    date_col_concern = None

    crash_files = None
    concern = None
    if 'longitude_crash' in config.keys() and config['longitude_crash']:
        longitude_crash = config['longitude_crash']
    if 'latitude_crash' in config.keys() and config['latitude_crash']:
        latitude_crash = config['latitude_crash']
    if 'date_col_crash' in config.keys() and config['date_col_crash']:
        date_col_crash = config['date_col_crash']

    if 'longitude_concern' in config.keys() and config['longitude_concern']:
        longitude_concern = config['longitude_concern']
    if 'latitude_concern' in config.keys() and config['latitude_concern']:
        latitude_concern = config['latitude_concern']
    if 'date_col_concern' in config.keys() and config['date_col_concern']:
        date_col_concern = config['date_col_concern']

    if 'crashfiles' in config.keys() and config['crashfiles']:
        crash_files = config['crashfiles']

    if 'recreate' in config.keys() and config['recreate']:
        recreate = True

    if 'concern' in config.keys() and config['concern']:
        concern = config['concern']

    # Features drawn from open street maps
    # additional_features from config file can add on to
    features = [
        'width', 'lanes', 'hwy_type', 'osm_speed', 'signal', 'oneway']

    print "Generating maps for " + city + ' in ' + DATA_FP
    if recreate:
        print "Overwriting existing data..."
    # Get the maps out of open street map, both projections
    subprocess.check_call([
        'python',
        '-m',
        'data.osm_create_maps',
        city,
        DATA_FP,
    ] + (['--forceupdate'] if recreate else []))

    # Create segments on the open street map data
    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        DATA_FP,
        '-r',
        os.path.join(DATA_FP, 'processed/maps/osm_ways_3857.shp'),
        '-i',
        os.path.join(DATA_FP, 'processed/maps/osm_nodes.shp')
    ])

    if extra_map:
        # Extract intersections from the new city file
        # Write to a subdirectory so files created from osm aren't overwritten
        # Eventually, directory of additional files should also be an argument
        subprocess.check_call([
            'python',
            '-m',
            'data.extract_intersections',
            os.path.join(extra_map),
            '-d',
            DATA_FP,
            '-n',
            outputdir
        ] + (['--forceupdate'] if recreate else []))
        # Create segments from the Boston data
        subprocess.check_call([
            'python',
            '-m',
            'data.create_segments',
            '-d',
            DATA_FP,
            '-n',
            outputdir,
            '-r',
            extra_map3857
        ])

        # Map the boston segments to the open street map segments
        # and add features
        subprocess.check_call([
            'python',
            '-m',
            'data.add_map',
            DATA_FP,
            outputdir,
        ])

    subprocess.check_call([
        'python',
        '-m',
        'data.join_segments_crash_concern',
        '-d',
        DATA_FP
    ]
        + (['-c'] + (crash_files if crash_files else []))
        + (['-s', concern] if concern else [])
        + (['-x_crash', longitude_crash] if longitude_crash else [])
        + (['-y_crash', latitude_crash] if latitude_crash else [])
        + (['-x_concern', longitude_concern] if longitude_concern else [])
        + (['-y_concern', latitude_concern] if latitude_concern else [])
        + (['-t_crash', date_col_crash] if date_col_crash else [])
        + (['-t_concern', date_col_concern] if date_col_concern else [])
    )

    subprocess.check_call([
        'python',
        '-m',
        'data.ATR_scraping.geocode_snap_ATRs',
        '-d',
        DATA_FP
    ] + (['--forceupdate'] if recreate else []))
    subprocess.check_call([
        'python',
        '-m',
        'data.TMC_scraping.parse_tmc',
        '-d',
        DATA_FP
    ] + (['--forceupdate'] if recreate else []))

    if additional_features:
        features = features + additional_features

    # Throw in make canonical dataset here too just to keep track
    # of standardized features
    subprocess.check_call([
        'python',
        '-m',
        'features.make_canon_dataset',
        '-d',
        DATA_FP,
        '-features'
    ] + features)

