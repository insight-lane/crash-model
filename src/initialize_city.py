import argparse
import os
import shutil
import tzlocal
from data.util import geocode_address

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def make_config_file(yml_file, city, timezone, folder, crash, concern, supplemental=[]):
    address = geocode_address(city)

    f = open(yml_file, 'w')

    f.write(
        "# City name\n" +
        "city: {}\n".format(city) +
        "# City centerpoint latitude & longitude (default geocoded values set)\n" +
        "city_latitude: {}\n".format(address[1]) +
        "city_longitude: {}\n".format(address[2]) +
        "# City's time zone: defaults to the local time zone of computer initializing the city's config file\n" +
        "timezone: {}\n".format(timezone) +
        "# Radius of city's road network from centerpoint in km, required if OSM has no polygon data (defaults to 20km)\n" +
        "city_radius: 20\n" +
        "# The folder under data where this city's data is stored\n" +
        "name: {}\n".format(folder) +
        "# If given, limit crashes to after startdate and no later than enddate\n" +
        "# Recommended to limit to just a few years for now\n" +
        "startdate: \n" +
        "enddate: \n" +
        "# The type of predictions to generate, 'segment' is default, 'week' is legacy\n" +
        "level: 'segment'\n\n" +
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
        "      address: \n" +
        "      vehicles: \n" +
        "      bikes: \n\n"
    )

    if concern:
        f.write(
            "# List of concern type information\n" +
            "concern_files:\n" +
            "  - name: concern\n" +
            "      filename: {}\n".format(concern) +
            "      latitude: \n" +
            "      longitude: \n" +
            "      time: \n\n"
        )
    if supplemental:
        f.write("# Additional data sources\n" +
                "data_source:\n")

        for filename in supplemental:
            f.write(
                "  - name: \n" +
                "    filename: {}\n".format(filename) +
                "    address: \n" +
                "    date: \n" +
                "    time: \n" +
                "    category: \n" +
                "    notes: \n" +
                "    # Feature is categorical (f_cat) or continuous (f_cont) \n" +
                "    feat: \n" + 
                "    # feat_agg (feature aggregation) can be total count 'default' or 'latest value' \n" +
                "    feat_agg: \n"
                "    # if latest, the column name where the value can be found \n" +
                "    value: \n"
                )
        f.write("\n")
    f.write(
        "# If using legacy 'week' predictions:\n"+
        "# specify year & week on which to predict crashes (best practice is year & week towards the end of your crash data set\n" +
        "# in format [month, year]\n" +
        "time_target: [30, 2017]\n" +
        "# specify how many weeks back to predict in output of train_model\n" +
        "weeks_back: 1"
    )
    f.close()
    print("Wrote new configuration file in {}".format(yml_file))


def make_js_config(jsfile, city, folder):
    address = geocode_address(city)

    f = open(jsfile, 'w')
    f.write(
        'var config = {\n' +
        '    MAPBOX_TOKEN: "",\n' +
        '    cities: [\n' +
        '        {\n' +
        '            name: "{}",\n'.format(city) +
        '            id: "{}",\n'.format(folder) +
        '            latitude: {},\n'.format(str(address[1])) +
        '            longitude: {},\n'.format(str(address[2])) +
        '        }\n' +
        '    ]\n' +
        '}\n'
    )
    f.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-city", "--city", type=str, required=True,
                        help="city name, e.g. 'Boston, Massachusetts, USA'")
    parser.add_argument("-f", "--folder", type=str, required=True,
                        help="folder name, e.g. 'boston'")
    parser.add_argument('-crash', '--crash_file', type=str, required=True,
                        help="crash file path")
    parser.add_argument('-concern', '--concern_file', type=str,
                        help="concern file path")
    parser.add_argument('-supplemental', '--supplemental', type=str,
                        help="additional point-based feature files" +
                        "comma separated")

    args = parser.parse_args()

    DATA_FP = os.path.join(BASE_DIR, 'data', args.folder)

    crash = args.crash_file.split('/')[-1]
    crash_dir = os.path.join(DATA_FP, 'raw', 'crashes')
    concern = None
    supplemental_paths = []
    supplemental_files = []
    if args.concern_file:
        concern = args.concern_file.split('/')[-1]

    # Check to see if the directory exists
    # if it does, it's already been initialized, so do nothing
    if not os.path.exists(DATA_FP):
        print("Making directory structure under " + DATA_FP)
        os.makedirs(DATA_FP)
        os.makedirs(os.path.join(DATA_FP, 'raw'))
        os.makedirs(crash_dir)
        concern_dir = os.path.join(DATA_FP, 'raw', 'concerns')
        os.makedirs(concern_dir)
        os.makedirs(os.path.join(DATA_FP, 'processed'))
        os.makedirs(os.path.join(DATA_FP, 'standardized'))
        shutil.copyfile(args.crash_file, os.path.join(crash_dir, crash))

        if args.concern_file:
            shutil.copyfile(args.concern_file, os.path.join(
                concern_dir, concern))

        if args.supplemental:
            supplemental_paths = args.supplemental.split(',')
            os.makedirs(os.path.join(DATA_FP, 'raw', 'supplemental'))
            for point_file in supplemental_paths:
                filename = point_file.split('/')[-1]
                supplemental_files.append(filename)

                shutil.copyfile(point_file, os.path.join(
                    DATA_FP, 'raw', 'supplemental', filename))
    else:
        print(args.folder + " already initialized, skipping")

    yml_file = os.path.join(
        BASE_DIR, 'src/config/config_' + args.folder + '.yml')
    if not os.path.exists(yml_file):
        make_config_file(yml_file, args.city, tzlocal.get_localzone().zone,
                         args.folder, crash, concern, supplemental_files)

    js_file = os.path.join(
        BASE_DIR, 'reports/config.js')
    if not os.path.exists(js_file):
        print("Writing config.js")
        make_js_config(js_file, args.city, args.folder)
