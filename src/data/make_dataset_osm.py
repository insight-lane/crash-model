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
    parser.add_argument("-e", "--extramap", type=str,
                        help="Can give an additional shapefile")
    # if city file is given, need to also give a list of feats
    parser.add_argument("-features", "--features", nargs="+", default=[
        'AADT', 'SPEEDLIMIT', 'Struct_Cnd', 'Surface_Tp', 'F_F_Class'],
        help="List of segment features to include")
    parser.add_argument("-o", "--outputdir", type=str,
                        help="Directory to write output from extramap")
    parser.add_argument("-p", "--extramap3857", type=str,
                        help="Additional shapefile in 3857 projection")

    args = parser.parse_args()

    if args.extramap and (
            args.features is None
            or args.outputdir is None
            or args.extramap3857 is None
    ):
        parser.error(
            "--extramap requires --features, --outputdir, and --extramap3857.")

    # Eventually make this an arg as well:
    city = 'Boston, Massachusetts, USA'
    # Original features, that args.features can add on to
    features = ['width', 'lanes', 'hwy_type', 'osm_speed']

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

    if args.extramap:
        # Extract intersections from the new city file
        # Write to a subdirectory so files created from osm aren't overwritten
        # Eventually, directory of additional files should also be an argument
        subprocess.check_call([
            'python',
            '-m',
            'data.extract_intersections',
            os.path.join(args.extramap),
            '-d',
            DATA_FP,
            '-n',
            args.outputdir
        ])
        # Create segments from the Boston data
        subprocess.check_call([
            'python',
            '-m',
            'data.create_segments',
            '-d',
            DATA_FP,
            '-n',
            args.outputdir,
            '-r',
            args.extramap3857
        ])

        # Map the boston segments to the open street map segments
        # and add features
        subprocess.check_call([
            'python',
            '-m',
            'data.add_map',
            DATA_FP,
            args.outputdir,
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

    if args.features:
        features = features + args.features
        
    # Throw in make canonical dataset here too just to keep track
    # of standardized features
    subprocess.check_call([
        'python',
        '-m',
        'features.make_canon_dataset',
        '-d',
        DATA_FP,
        '-f',
        features
    ])
