import argparse
import os
import shutil
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def make_config_file(city, folder, crash, concern):
    yml_file = os.path.join(BASE_DIR, 'src/config/config_' + folder + '.yml')
    f = open(yml_file, 'w')
    f.write(
        "# City name\n" +
        "city: {}\n".format(city) +
        "# The folder under data where this city's data is stored\n" +
        "name: {}\n".format(folder) +
        "# If given, limit crashes to after start_year and before end_year\n" +
        "# Recommended to limit to just a few years for now\n" +
        "start_year: \n" +
        "end_year: \n\n\n" +
        "#################################################################\n" +
        "# Configuration for data transformation\n\n" +
        "# crash file configurations\n" +
        "crashes_files:\n" +
        "  {}:\n".format(crash) +
        "    required:\n" +
        "      id: \n" +
        "      latitude: \n" +
        "      longitude: \n" +
        "      date: \n" +
        " # Time is only required if date and time are in different columns" +
        "      time: \n" +
        "    optional:\n" +
        "      summary: \n" +
        "      address: \n\n"
    )

    if concern:
        f.write(
            "# List of concern type information" +
            "concern_files:\n" +
            "- name: concern\n" +
            "filename: {}\n".format(concern) +
            "latitude: \n" +
            "longitude: \n" +
            "time: \n\n\n"
        )
    f.write(
        "# week on which to predict crashes (week, year)\n" +
        "# will output predictions for all weeks up to this week\n" +
        "# Choose a week towards the end of your crash data set\n" +
        "# in format [month, year]\n" +
        "time_target: [30, 2017]\n"
    )
    f.close()
    print yml_file


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-city", "--city", type=str,
                        help="city name")
    parser.add_argument("-f", "--folder", type=str,
                        help="folder name")
    parser.add_argument('-crash', '--crash_file', type=str,
                        help="crash file path")
    parser.add_argument('-concern', '--concern_file', type=str,
                        help="concern file path")

    args = parser.parse_args()
    if not args.city:
        print "city required"
        sys.exit()
    if not args.folder:
        print "folder required"
        sys.exit()
    if not args.crash_file:
        print "crash file required"
        sys.exit()

    DATA_FP = os.path.join(BASE_DIR, 'data', args.folder)

    # Check to see if the directory exists
    # if it does, it's already been initialized, so do nothing
    if not os.path.exists(DATA_FP):
        os.makedirs(DATA_FP)
        os.makedirs(os.path.join(DATA_FP, 'raw'))
        crash = args.crash_file.split('/')[-1]
        crash_dir = os.path.join(DATA_FP, 'raw', 'crashes')
        os.makedirs(crash_dir)
        concern_dir = os.path.join(DATA_FP, 'raw', 'concerns')
        os.makedirs(concern_dir)
        os.makedirs(os.path.join(DATA_FP, 'processed'))
        os.makedirs(os.path.join(DATA_FP, 'standardized'))
        shutil.copyfile(args.crash_file, os.path.join(crash_dir, crash))

        concern = None
        if args.concern_file:
            concern = args.concern_file.split('/')[-1]
            shutil.copyfile(args.concern_file, os.path.join(
                concern_dir, concern))

        make_config_file(args.city, args.folder, crash, concern)

    else:
        print args.folder + " already initialized, skipping"
