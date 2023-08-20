import argparse
import os
import shutil
import tzlocal
from data.geocoding_util import geocode_address
from distutils.dir_util import copy_tree

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def print_feat_set(f, features):
    for feat_type in features:
        f.write("  {}:\n".format(feat_type))
        for feature in features[feat_type]:
            f.write("    {}\n".format(feature))
    f.write("\n")
    f.write("# Speed limit is a required feature\n" +
            "# If you choose to override OpenStreetMaps' speed limit, replace 'osm_speed' with the feature name here\n" +
            "speed_limit: osm_speed\n\n"
            )
    
def write_default_features(f, waze=False, supplemental=[],
                           additional_map=None):
    """
    Writes the default features to the config file
    args:
        f - file handle
    """

    # To change the default features, modify this data structure
    osm = {
        "categorical": [
            'width: Width',
            'cycleway_type: Bike lane',
            'signal: Signal',
            'oneway: One Way',
            'lanes: Number of lanes'
        ],
        "continuous": [
            'width_per_lane: Average width per lane'
        ]
    }
    f.write(
        "#################################################################\n" +
        "# Configuration for default features\n\n" +
        "# Default features from open street map. You can remove features you don't want\n"
        "# Note: we don't support adding features in the config file.\n" +
        "# If there is an additional feature you want from open street map, contact the development team\n" +
        "openstreetmap_features:\n")

    print_feat_set(f, osm)
    f.write("\n\n")
    if waze:
        # To change the default waze features, modify this data structure
        waze_feats = {
            "categorical": ['jam: Existence of a jam'],
            "continuous": ['jam_percent: Percent of time there was a jam']
        }
        f.write(
            "# Configuration for default waze features\n" +
            "waze_features:\n"
        )
        print_feat_set(f, waze_feats)
        f.write("\n\n")
    if additional_map:
        f.write(
            "# Additional city-specific features can be added from alternate map\n" +
            "additional_map_features:\n" +
            "  # The path to the extra map, must be in 3857 projection\n" +
            "  extra_map: {}\n\n".format(additional_map) +
            "  continuous: \n" +
            "  categorical: \n\n\n")

    if supplemental:
        f.write(
            "# Additional point based features sources\n" +
            "# Any csv file with rows corresponding to location points\n" +
            "# See README for details on format (https://github.com/insight-lane/crash-model/tree/master/src#point-based-features)\n" +
            "data_source:\n"
        )

        for filename in supplemental:
            f.write(
                " copy-paste the block below for each additional data source\n" +
                "  - filename: {}\n".format(filename) +
                "    # Provide either lat/long or address (address will be geocoded): \n" +
                "    latitude: \n" +
                "    longitude: \n" +
                "    address: \n" +
                "    date: \n" +
                "    time: \n" +
                "    feats: \n" +
                "    # copy-paste the block below for each additional feature for this file\n" +
                "      - name: \n" +
                "        category: \n" +
                "        notes: \n" +
                "        # Feature is 'categorical' or 'continuous' (numeric), default is continuous'\n" +
                "        feat_type: \n" +
                "        # feat_agg (feature aggregation), only option is 'latest' (latest value), default is count\n" +
                "        feat_agg: \n"
                "        # if 'latest' above, provide column name where the value can be found \n" +
                "        value: \n"
                )
        f.write("\n")


def make_config_file(yml_file, city, timezone, folder, crash,
                     waze, additional_map=None, supplemental=[]):
    address = geocode_address(city)
    city_segments = city.split()
    speed_unit = 'kph'
    if city_segments[-1] == 'USA':
        speed_unit = 'mph'

    f = open(yml_file, 'w')

    f.write(
        "# City name\n" +
        "city: {}\n".format(city) +
        "# City centerpoint latitude & longitude (default geocoded values set)\n" +
        "city_latitude: {}\n".format(address[1]) +
        "city_longitude: {}\n\n".format(address[2]) +
        "# City's time zone: defaults to the local time zone of computer initializing the city's config file\n" +
        "timezone: {}\n".format(timezone) +
        "# Radius of city's road network from centerpoint in km, required if OSM has no polygon data (defaults to 20km)\n" +
        "city_radius: 20\n" +
        "speed_unit: {}\n\n".format(speed_unit) +
        "# By default, maps are created from OSM's polygon data and fall back to radius\n" +
        "# if there is no polygon data, but but you can change the openstreetmap_geography\n" +
        "# to 'radius' if preferred\n" +
        "map_geography: polygon\n\n" +
        "# The folder under data where this city's data is stored\n" +
        "name: {}\n\n".format(folder) +
        "# If given, limit crashes to after startdate and no later than enddate\n" +
        "# Recommended to limit to just a few years for now\n" +
        "startdate: \n" +
        "enddate: \n\n" +
        "#################################################################\n" +
        "# Configuration for data standardization\n\n" +
        "# crash file configurations\n" +
        "crashes_files:\n" +
        "  {}:\n".format(crash) +
        "    required:\n" +
        "      id: \n" +
        "      latitude: \n" +
        "      longitude: \n" +
        "      # If date supplied in single column:\n" +
        "      date_complete: \n" +
        "      # If date is separated into year/month/day:\n" +
        "      date_year: \n" +
        "      date_month: \n" +
        "      # Leave date_day empty if not available\n" +
        "      date_day: \n"+
        "      # If time is available and separate from date:\n" +
        "      time: \n" +
        "      # If time specified, time_format is one of:\n" +
        "      # default (HH:MM:SS)\n" +
        "      # seconds (since midnight)\n" +
        "      # military (HHMM)\n" +
        "      time_format: \n"+
        "    optional:\n" +
        "      summary: \n" +
        "      # If the crash file doesn't have a lat/lon, you must give the address field\n" +
        "      # and you will need to run the geocode_batch script - see the README\n" +
        "      address: \n" +
        "      # This section allows you to specify additional feature in the crash file\n" +
        "      # (split_columns) to go into the training set\n" +
        "      # Most commonly split_columns are used for mode (pedestrian/bike/vehicle)\n" +
        "      # but you can specify other fields in the crash data file.\n" +
        "      # See the README for examples\n\n"
    )

    write_default_features(f, waze, supplemental, additional_map)
    f.write("")
    f.close()

    print("Wrote new configuration file in {}".format(yml_file))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-city", "--city", type=str, required=True,
                        help="city name, e.g. 'Boston, Massachusetts, USA'")
    parser.add_argument("-f", "--folder", type=str, required=True,
                        help="folder name, e.g. 'boston'")
    parser.add_argument('-crash', '--crash_file', type=str, required=True,
                        help="crash file path")
    parser.add_argument('-supplemental', '--supplemental', type=str,
                        help="additional point-based feature files" +
                        "comma separated")
    parser.add_argument('-m', '--additionalmap', type=str,
                        help="additional shape file" +
                        "from which to extract features")
    parser.add_argument('-waze', '--waze', type=str,
                        help="a directory containing waze snapshots "
                        "(.json or .json.gz files)")

    args = parser.parse_args()

    DATA_FP = os.path.join(BASE_DIR, 'data', args.folder)

    crash = args.crash_file.split('/')[-1]
    crash_dir = os.path.join(DATA_FP, 'raw', 'crashes')
    supplemental_paths = []
    supplemental_files = []
    waze = False
    if args.waze:
        waze = True

    if args.supplemental:
        supplemental_paths = args.supplemental.split(',')
        for point_file in supplemental_paths:
            filename = point_file.split('/')[-1]
            supplemental_files.append(filename)

    # Check to see if the directory exists
    # if it does, it's already been initialized, so do nothing
    if not os.path.exists(DATA_FP):
        print("Making directory structure under " + DATA_FP)
        os.makedirs(DATA_FP)
        os.makedirs(os.path.join(DATA_FP, 'raw'))
        os.makedirs(crash_dir)
        os.makedirs(os.path.join(DATA_FP, 'processed'))
        os.makedirs(os.path.join(DATA_FP, 'processed', 'maps'))
        os.makedirs(os.path.join(DATA_FP, 'standardized'))
        shutil.copyfile(args.crash_file, os.path.join(crash_dir, crash))

        # If a waze directory was given, copy
        if args.waze:
            waze_dir = os.path.join(DATA_FP, 'raw', 'waze')
            os.makedirs(waze_dir)
            print("Including waze data")
            copy_tree(args.waze, waze_dir)

        if args.supplemental:
            os.makedirs(os.path.join(DATA_FP, 'raw', 'supplemental'))
            for point_file in supplemental_paths:
                shutil.copyfile(point_file, os.path.join(
                    DATA_FP, 'raw', 'supplemental', filename))
    else:
        print(args.folder + " directory already initialized, skipping")

    yml_file = os.path.join(
        BASE_DIR, 'src/config/config_' + args.folder + '.yml')
    if not os.path.exists(yml_file):
        make_config_file(yml_file, args.city, tzlocal.get_localzone().zone,
                         args.folder, crash, waze,
                         additional_map=args.additionalmap,
                         supplemental=supplemental_files)

