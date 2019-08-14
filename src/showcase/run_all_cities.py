# -*- coding: utf-8 -*-
import os
import subprocess
import argparse


DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/data/'


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')
    # Can also choose which steps of the process to run
    parser.add_argument('--onlysteps',
                        help="Give list of steps to run, as comma-separated " +
                        "string.  Has to be among 'standardization'," +
                        "'generation', 'model', 'visualization'")
    args = parser.parse_args()

    cities = os.listdir(DATA_FP)
    for city in cities:
        config_file = os.path.join('config', 'config_{}.yml'.format(city))

        print("Running pipeline for {}".format(city))
        print(args.onlysteps)
        subprocess.check_call([
            'python',
            'pipeline.py',
            '-c',
            config_file,
        ] + (['--forceupdate'] if args.forceupdate else []) +
            (['--onlysteps', args.onlysteps] if args.onlysteps else [])
        )
    city_list = ", ".join(cities)
    print("Ran pipeline on {}".format(city_list))
