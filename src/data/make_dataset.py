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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # Can give a config file
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Config file")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="Data directory")

    parser.add_argument("-s", "--startyear", type=str,
                        help="Can limit data to crashes this year or later")
    parser.add_argument("-e", "--endyear", type=str,
                        help="Can limit data to crashes this year or earlier")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()

    config_file = args.config
    start_year = None
    end_year = None
    if args.startyear:
        start_year = str(args.startyear)
    if args.endyear:
        end_year = str(args.endyear)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    # City
    if 'city' not in list(config.keys()) or config['city'] is None:
        sys.exit('City is required in config file')
    city = config['city']

    DATA_FP = args.datadir

    # This block handles any extra map info as we have in Boston
    extra_map = None
    additional_features = None
    recreate = False
    outputdir = city.split(',')[0]
    if 'extra_map' in list(config.keys()) and config['extra_map']:
        # Require additional features and additional shapefile in 3857 proj
        if 'additional_features' not in list(config.keys()) \
           or config['additional_features'] is None:
            sys.exit("If extra_map is given, additional_features " +
                     "are required.")

        extra_map = config['extra_map']
        additional_features = config['additional_features'].split()

    # Whether to regenerate maps from open street map
    if args.forceupdate:
        recreate = True

    # Features drawn from open street maps
    # Additional features can be added if you're using an extra map
    # beyond open street map
    features = [
        'width', 'lanes', 'hwy_type', 'osm_speed', 'signal', 'oneway',
        'intersection_segments', 'width_per_lane'
    ]
    # Features can also be added if additional data sources are given
    if 'data_source' in config and config['data_source']:
        features += [x['name'] for x in config['data_source']]

    print("Generating maps for " + city + ' in ' + DATA_FP)
    if recreate:
        print("Overwriting existing data...")
    # Get the maps out of open street map, both projections
    subprocess.check_call([
        'python',
        '-m',
        'data.osm_create_maps',
        '-c',
        config_file,
        '-d',
        DATA_FP,
    ] + (['--forceupdate'] if recreate else []))

    # Create segments on the open street map data
    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        DATA_FP
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
            os.path.join(
                DATA_FP, 'processed', 'maps', outputdir, 'elements.geojson')
        ] + (['--forceupdate'] if recreate else []))

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
        + (['-start', start_year] if start_year else [])
        + (['-end', end_year] if end_year else [])
    )

    subprocess.check_call([
        'python',
        '-m',
        'data.propagate_volume',
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
