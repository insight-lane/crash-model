import os
import argparse
import csv


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


MAP_FP = BASE_DIR + '/data/processed/maps'
RAW_DATA_FP = BASE_DIR + '/data/raw'
PROCESSED_DATA_FP = BASE_DIR + '/data/processed'

# filepaths of raw crash data (hardcoded for now)
CRASH_DATA_FPS = [
    '/2015motorvehicles_formatted.csv',
    '/cad_crash_events_with_transport_2016_wgs84.csv',
    '/2017motorvehicles_formatted.csv'
]
ADDITIONAL_CRASH_INFO_FPS = [
    '/2015motorvehicles_with_modetype.csv',
    '/2017motorvehicles_with_modetype.csv'
]


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-c", "--crashfiles", nargs='+',
                        help="Can give alternate list of crash files. " +
                        "Only use filename, don't include path")
    parser.add_argument("-a", "--additionalfiles", nargs='+',
                        help="Can give alternate list of additional files. " +
                        "Only use filename, don't include path")
    parser.add_argument("-o", "--outfile", type=str,
                        help="Can give alternate output file. " +
                        "Default is all_crash_data.csv")

    args = parser.parse_args()

    # Can override the hardcoded data directory
    if args.datadir:
        RAW_DATA_FP = args.datadir + '/raw/'
        PROCESSED_DATA_FP = args.datadir + '/processed/'
        MAP_FP = args.datadir + '/processed/maps/'
    if args.crashfiles:
        CRASH_DATA_FPS = args.crashfiles
    if args.additionalfiles:
        ADDITIONAL_CRASH_INFO_FPS = args.additional_files
    outfile = 'all_crash_data.csv'
    if args.outfile:
        outfile = args.outfile
    outfile = RAW_DATA_FP + '/' + outfile

    # Read in additional info files, create dict to look up by common id
    additional_info = {}
    for filename in ADDITIONAL_CRASH_INFO_FPS:
        with open(RAW_DATA_FP + filename) as f:
            csv_reader = csv.DictReader(f)
            for r in csv_reader:
                additional_info[r['CAD_EVENT_REL_COMMON_ID']] = r

    # Read in CAD crash data
    crashes = []
    fieldnames = set(['EMS', 'mode_type'])
    for fp in CRASH_DATA_FPS:
        with open(RAW_DATA_FP + fp) as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                fieldnames.update(row.keys())
                common_id = row['CAD_EVENT_REL_COMMON_ID']
                if common_id in additional_info.keys():
                    row['mode_type'] = \
                        additional_info[common_id]['mode_type']

                # while we're in here, add field for whether EMS was called
                # as defined by (E) existing in the FIRST_EVENT_SUBTYPE field
                if '(E)' in row['FIRST_EVENT_SUBTYPE']:
                    row['EMS'] = True
                else:
                    row['EMS'] = False
                crashes.append(row)

    with open(outfile, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in crashes:
            missing_fields = [field for field in fieldnames
                              if field not in row.keys()]
            for f in missing_fields:
                row[f] = ''
            writer.writerow(row)

print len(crashes)
