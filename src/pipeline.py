import argparse
import yaml
import os
import subprocess

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def data_transformation(config, DATA_FP, forceupdate=False):
    """
    Transform data from a csv file into standardized crashes and concerns
    according to a config file
    Args:
        config
        DATA_FP - data directory for this city
    """
    # transform data, if the standardized files don't exist
    # or forceupdate
    if not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'crashes.json')) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_transformation.transform_crashes',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        print "Already transformed crash data, skipping"

    # There has to be concern data in the config file to try processing it
    if (config['concern_files'] and not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'concerns.json'))) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_transformation.transform_concerns',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        if not config['concern_files']:
            print "No concerns defined in config file"
        elif not forceupdate:
            print "Already transformed crash data, skipping"


def data_generation(config_file, DATA_FP, start_year=None, end_year=None,
                    forceupdate=False):
    subprocess.check_call([
        'python',
        '-m',
        'data.make_dataset_osm',
        '-c',
        config_file,
        '-d',
        DATA_FP
    ]
        + (['-s', start_year] if start_year else [])
        + (['-e', end_year] if end_year else [])
    )


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", type=str,
                        help="config file location")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()

    # Read config file
    with open(args.config_file) as f:
        config = yaml.safe_load(f)

    DATA_FP = os.path.join(BASE_DIR, 'data', config['name'])

    data_transformation(config, DATA_FP, forceupdate=args.forceupdate)

    data_generation(args.config_file, DATA_FP, start_year=config['start_year'],
                    end_year=config['end_year'], forceupdate=args.forceupdate)
    # train_model
    # risk map
    # visualize

#    subprocess.check_call([
#        'python',
#        '-m',
#        'data_transformation.extract_intersections',
#        filename])

