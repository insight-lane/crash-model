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


def make_feature_list(config, datadir, waze=False):
    """
    Make the list of features, and write it to the city's data folder
    That way, we can avoid hardcoding the feature list in multiple places.
    If you add extra features, the only place you should need to add them
    is here
    Args:
        Config - the city's config file
        waze - whether or not we're including waze data
    """

    # Features drawn from open street maps
    # Additional features can be added if you're using an extra map
    # beyond open street map
    feat_types = {
        'f_cat': ['width', 'cycleway_type', 'signal', 'oneway'],
        'f_cont': ['lanes', 'hwy_type', 'osm_speed', 'width_per_lane']
    }

    # Features can also be added if additional data sources are given
    if 'data_source' in config and config['data_source']:
        feat_types['f_cat'] += [x['name'] for x in config['data_source']
                                if 'feat' == 'f_cat']
        feat_types['f_cont'] += [x['name'] for x in config['data_source']
                                if 'feat' == 'f_cont']

    # If we have waze data for the city
    if waze:
        feat_types['f_cont'] += ['jam_percent']
        feat_types['f_cat'] += ['jam']

    # Additional features from additional city-specific maps
    if 'additional_features' in config and config['additional_features']:
        additional = config['additional_features']
        if 'f_cat' in additional and additional['f_cat']:
            feat_types['f_cat'] += additional['f_cat'].split()
        if 'f_cont' in additional and additional['f_cont']:
            feat_types['f_cont'] += additional['f_cont'].split()

    features = feat_types['f_cat'] + feat_types['f_cont']
    # Write features to file
    with open(os.path.join(datadir, 'processed', 'features.yml'), 'w') as f:
        yaml.dump(feat_types, f, default_flow_style=False)
    return features

    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # Can give a config file
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Config file")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="Data directory")

    parser.add_argument("-s", "--startdate", type=str,
                        help="Can limit data to crashes this date or later" +
                        "in form YYYY-MM-DD")
    parser.add_argument("-e", "--enddate", type=str,
                        help="Can limit data to crashes this date or earlier" +
                        "in form YYYY-MM-DD")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()

    config_file = args.config
    startdate = None
    enddate = None

    with open(config_file) as f:
        config = yaml.safe_load(f)

    # City
    if 'city' not in list(config.keys()) or config['city'] is None:
        sys.exit('City is required in config file')
    city = config['city']

    DATA_FP = args.datadir

    # This block handles any extra map info as we have in Boston
    extra_map = None

    recreate = False
    outputdir = city.split(',')[0]
    additional_features = None
    if 'extra_map' in list(config.keys()) and config['extra_map']:
        # Require additional features and additional shapefile in 3857 proj
        if 'additional_features' not in list(config.keys()) \
           or config['additional_features'] is None:
            sys.exit("If extra_map is given, additional_features " +
                     "are required.")

        extra_map = config['extra_map']

    # Whether to regenerate maps from open street map
    if args.forceupdate:
        recreate = True

    waze = False
    if os.path.exists(os.path.join(DATA_FP, 'standardized', 'waze.json')):
        waze = True

    features = make_feature_list(config, args.datadir, waze)

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

    # Add waze data if applicable
    if waze:
        print("Adding Waze features")
        subprocess.check_call([
            'python',
            '-m',
            'data.add_waze_data',
            '-d',
            DATA_FP
        ])
    else:
        print("No Waze data found, skipping...")
    
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
        + (['-start', startdate] if startdate else [])
        + (['-end', enddate] if enddate else [])
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
