import argparse
import os
import subprocess
import shutil
import data.config

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def data_standardization(config_file, DATA_FP, forceupdate=False):
    """
    Standardize data from a csv file into compatible crashes
    according to a config file
    Args:
        config_file
        DATA_FP - data directory for this city
    """

    # standardize data, if the files don't already exist
    # or forceupdate
    if not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'crashes.json')) or forceupdate:
        print("Standardizing crash data..")
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_crashes',
            '-c',
            config_file,
            '-d',
            DATA_FP
        ])
    else:
        print("Already standardized crash data, skipping")

    # Handling volume data
    if (not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'volume.json'))) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_volume',
            '-c',
            config_file,
            '-d',
            DATA_FP
        ])
    else:
        print("Already standardized volume data, skipping")

    if not os.path.exists(os.path.join(
           DATA_FP, 'standardized', 'points.json')) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_point_data',
            '-c',
            config_file,
            '-d',
            DATA_FP
        ])
    else:
        print("Already standardized point data, skipping")
    forceupdate = True

    if os.path.exists(os.path.join(DATA_FP, 'raw', 'waze')) and \
       (not os.path.exists(os.path.join(BASE_DIR, 'standardized', 'waze.json')
                           or forceupdate)):
        subprocess.check_call([
            'python',
            '-m',
            'data_standardization.standardize_waze_data',
            '-c',
            config_file,
            '-d',
            DATA_FP,
            # The script can filter by dates, but if this is something
            # we'd like to add, dates should probably be specified
            # Might be better to just only store the waze snapshots force
            # the desired weeks in the raw waze directory
        ])
    elif not os.path.exists(os.path.join(DATA_FP, 'raw', 'waze')):
        print("No waze data, skipping")
    else:
        print("Already standardized waze data, skipping")


def data_generation(config_file, DATA_FP, startdate=None, enddate=None,
                    forceupdate=False):
    """
    Generate the map and feature data for this city
    Args:
        config_file - path to config file
        DATA_FP - path to data directory, e.g. ../data/boston/
        startdate (optional)
        enddate (optional)
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
        + (['-s', str(startdate)] if startdate else [])
        + (['-e', str(enddate)] if enddate else [])
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


def visualize(DATA_FP, config_file):
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
        DATA_FP,
        '-c',
        config_file
    ])
    print("Generating risk map")
    subprocess.check_call([
        'python',
        '-m',
        'visualization.risk_map',
        '-c',
        config_file
    ])


def copy_files(base_dir, data_fp, config):
    """
    Copy necessary files into showcase directory
    Args:
        base_dir - top level directory
        data_fp - data directory
        config
    """

    showcase_dir = os.path.join(base_dir, 'src', 'showcase', 'data')
    if not os.path.exists(showcase_dir):
        os.makedirs(showcase_dir)

    showcase_dir = os.path.join(showcase_dir, config.name)
    if not os.path.exists(showcase_dir):
        os.makedirs(showcase_dir)

    files = []
    if config.split_columns:
        for column in config.split_columns:
            files.append('preds_viz_' + column + '.geojson')
            files.append('crashes_rollup_' + column + ".geojson")
    else:
        files.append('preds_viz.geojson')
        files.append('crashes_rollup.geojson')

    for file in files:
        shutil.copyfile(
            os.path.join(data_fp, 'processed', file),
            os.path.join(showcase_dir, file))


def make_js_config(BASE_DIR, config):
    """
    Make a city specific js config file in the showcase's data directory
    Args:
        BASE_DIR - city's data directory
        config - configuration object
    Returns:
        nothing, just writes the js file in showcase/data/
    """

    showcase_data = os.path.join(
        BASE_DIR, 'src', 'showcase', 'data')
    if not os.path.exists(showcase_data):
        os.makedirs(showcase_data)

    jsfile = os.path.join(showcase_data, 'config_' + config.name + '.js')
    print ("writing javascript config file in {}".format(jsfile))

    f = open(jsfile, 'w')
    f.write(
        'var config = [\n')

    if config.split_columns:
        for split_column in config.split_columns:
            name = config.city + " (" + split_column + ")"
            f.write(
                '    {\n' +
                '        name: "{}",\n'.format(name) +
                '        id: "{}",\n'.format(config.name + '_' + split_column) +
                '        latitude: {},\n'.format(config.city_latitude) +
                '        longitude: {},\n'.format(config.city_longitude) +
                '        speed_unit: "{}",\n'.format(config.speed_unit) +
                '        file: "data/{}/preds_viz_{}.geojson",\n'.format(config.name, split_column) +
                '        crashes: "data/{}/crashes_rollup_{}.geojson"\n'.format(config.name, split_column) +
                '    },\n'
            )
    else:
        f.write(
            '    {\n' +
            '        name: "{}",\n'.format(config.city) +
            '        id: "{}",\n'.format(config.name) +
            '        latitude: {},\n'.format(config.city_latitude) +
            '        longitude: {},\n'.format(config.city_longitude) +
            '        speed_unit: "{}",\n'.format(config.speed_unit) +
            '        file: "data/{}/preds_viz.geojson",\n'.format(config.name) +
            '        crashes: "data/{}/crashes_rollup.geojson"\n'.format(config.name) +
            '    }\n'
        )
        
    f.write(']')
    f.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", required=True, type=str,
                        help="config file location")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps and standard data')
    # Can also choose which steps of the process to run
    parser.add_argument('--onlysteps',
                        help="Give list of steps to run, as comma-separated " +
                        "string.  Has to be among 'standardization'," +
                        "'generation', 'model', 'visualization'")

    args = parser.parse_args()
    if args.onlysteps:
        steps = args.onlysteps.split(',')

    # Read config file
    config = data.config.Configuration(args.config_file)

    DATA_FP = os.path.join(BASE_DIR, 'data', config.name)

    if not args.onlysteps or 'standardization' in args.onlysteps:
        data_standardization(args.config_file, DATA_FP, forceupdate=args.forceupdate)

    startdate = config.startdate
    enddate = config.enddate
    if not args.onlysteps or 'generation' in args.onlysteps:
        data_generation(args.config_file, DATA_FP,
                        startdate=startdate,
                        enddate=enddate,
                        forceupdate=args.forceupdate)

    if not args.onlysteps or 'model' in args.onlysteps:
        train_model(args.config_file, DATA_FP)

    if not args.onlysteps or 'visualization' in args.onlysteps:
        visualize(DATA_FP, args.config_file)
        copy_files(BASE_DIR, DATA_FP, config)
        make_js_config(BASE_DIR, config)
