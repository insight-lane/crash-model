import argparse
import yaml
import os
import subprocess

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def data_standardization(config, DATA_FP, forceupdate=False):
    """
    Standardize data from a csv file into compatible crashes and concerns
    according to a config file
    Args:
        config
        DATA_FP - data directory for this city
    """
    # standardize data, if the files don't already exist
    # or forceupdate
    print("Standardizing data...")
    if not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'crashes.json')) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_crashes',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        print("Already standardized crash data, skipping")

    # There has to be concern data in the config file to try processing it
    if ('concern_files' in list(config.keys())
        and config['concern_files'] and not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'concerns.json'))) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_concerns',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        if 'concern_files' not in list(config.keys()) or not config['concern_files']:
            print("No concerns defined in config file")
        elif not forceupdate:
            print("Already standardized concern data, skipping")

    # Handling volume data
    if (not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'volume.json'))) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_volume',
            '-c',
            config['name'],
            '-d',
            DATA_FP
        ])
    else:
        print("Already standardized volume data, skipping")

    if 'data_source' in config and config['data_source'] and \
       (not os.path.exists(os.path.join(
           DATA_FP, 'standardized', 'points.json')) or forceupdate):
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_point_data',
            '-c',
            os.path.join(BASE_DIR, 'src', 'config',
                         'config_' + config['name'] + '.yml'),
            '-d',
            DATA_FP
        ])
    else:
        print("Already standardized point data, skipping")


def data_generation(config_file, DATA_FP, start_year=None, end_year=None,
                    forceupdate=False):
    """
    Generate the map and feature data for this city
    Args:
        config_file - path to config file
        DATA_FP - path to data directory, e.g. ../data/boston/
        start_year (optional)
        end_year (optional)
    """
    print("Generating data and features...")
    subprocess.check_call([
        'python',
        '-m',
        'data.make_dataset',
        '-c',
        config_file,
        '-d',
        DATA_FP
    ]
        + (['-s', str(start_year)] if start_year else [])
        + (['-e', str(end_year)] if end_year else [])
        + (['--forceupdate'] if forceupdate else [])
    )


def train_model(config_file, DATA_FP):
    """
    Trains the model
    Args:
        config_file - path to config file
        DATA_FP - path to data directory, e.g. ../data/boston/
    """
    print("Training model...")
    subprocess.check_call([
        'python',
        '-m',
        'models.train_model',
        '-c',
        config_file,
        '-d',
        DATA_FP
    ])


def visualize(DATA_FP):
    """
    Creates the visualization data set for a city
    Args:
        DATA_FP - path to data directory, e.g. ../data/boston/
    """
    print("Generating visualization data")
    subprocess.check_call([
        'python',
        '-m',
        'data.make_preds_viz',
        '-d',
        DATA_FP
    ])


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", required=True, type=str,
                        help="config file location")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')
    # Can also choose which steps of the process to run
    parser.add_argument('--onlysteps',
                        help="Give list of steps to run, as comma-separated " +
                        "string.  Has to be among 'standardization'," +
                        "'generation', 'model', 'visualization'")

    args = parser.parse_args()
    if args.onlysteps:
        steps = args.onlysteps.split(',')

    # Read config file
    with open(args.config_file) as f:
        config = yaml.safe_load(f)

    DATA_FP = os.path.join(BASE_DIR, 'data', config['name'])

    if not args.onlysteps or 'standardization' in args.onlysteps:
        data_standardization(config, DATA_FP, forceupdate=args.forceupdate)

    start_year = config['start_year']
    if start_year:
        start_year = '01/01/{} 00:00:00Z'.format(start_year)
    end_year = config['end_year']
    if end_year:
        end_year = '01/01/{} 00:00:00Z'.format(end_year)
    if not args.onlysteps or 'generation' in args.onlysteps:
        data_generation(args.config_file, DATA_FP,
                        start_year=start_year,
                        end_year=end_year,
                        forceupdate=args.forceupdate)

    if not args.onlysteps or 'model' in args.onlysteps:
        train_model(args.config_file, DATA_FP)

    if not args.onlysteps or 'visualization' in args.onlysteps:
        visualize(DATA_FP)
