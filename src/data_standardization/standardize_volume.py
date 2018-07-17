import argparse
import os
import yaml
from . import ATR_util
import sys
from data.util import read_geocode_cache, lookup_address
import csv
from collections import OrderedDict
from jsonschema import validate
import json

BASE_FP = None
PROCESSED_DATA_FP = None
CURR_FP = os.path.dirname(
    os.path.abspath(__file__))


def Boston_ATRs(atrs, ATR_FP):

    if not os.path.exists(os.path.join(BASE_FP, 'processed',
                                       'geocoded_addresses.csv')):
        print("No geocoded_addresses.csv found, geocoding addresses")

    cached = read_geocode_cache(filename=os.path.join(BASE_FP,
                                'processed', 'geocoded_addresses.csv'))

    results = []
    json_results = []
    for atr in atrs[0:10]:
        if ATR_util.is_readable_ATR(os.path.join(ATR_FP, atr)):
            atr_address = ATR_util.clean_ATR_fname(
                os.path.join(ATR_FP, atr))
            print(atr_address)
            geocoded_add, lat, lng, status = lookup_address(
                atr_address, cached)

            cached[atr_address] = [geocoded_add, lat, lng, status]
        
            print(str(geocoded_add) + ',' + str(lat) + ',' + str(lng))
            vol, speed, motos, light, heavy, date = ATR_util.read_ATR(
                os.path.join(ATR_FP, atr))
#            import ipdb; ipdb.set_trace()

            r = OrderedDict([
                ("date", date),
                ("location", OrderedDict([
                    ("latitude", float(lat)),
                    ("longitude", float(lng)),
                    ("address", geocoded_add)
                ])),
                ("volume", OrderedDict([
                    ("totalVolume", vol),
                    ("totalLightVehicles", light),
                    ("totalHeavyVehicles", heavy),
                    ("bikes", motos),
                ])),
                ("speed", OrderedDict([
                    ("averageSpeed", speed)
                ]))
            ])
            results.append(r)

    print(('Number geocoded: {}'.format(len(results))))
    # Write out the cache
    with open(os.path.join(
            PROCESSED_DATA_FP, 'geocoded_addresses.csv'), 'w') as csvfile:

        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([
            'Input Address',
            'Output Address',
            'Latitude',
            'Longitude',
            'Status'
        ])

        for name, value in cached.items():
            writer.writerow([name] + value)
    return results


def parse_ATRs(ATR_FP, city):
    """
    Looks in a directory for ATRs, then calls city-appropriate
    ATR parsing function.
    This is hugely hardcoded, but unavoidable given such different
    standards for different cities
    Args:
        city - the city's folder name, e.g. boston
        dirname - directory for the ATRs
    Returns:
        json for the ATR volumes
    """
    if not os.path.exists(ATR_FP):
        print("NO ATR directory found, skipping...")
        sys.exit()
    atrs = os.listdir(ATR_FP)
    if city == 'boston':
        ATRs = Boston_ATRs(atrs, ATR_FP)
        schema_path = os.path.join(os.path.dirname(os.path.dirname(
            CURR_FP)), "standards", "volume-schema.json")
        with open(schema_path) as volume_schema:
            validate(ATRs, json.load(volume_schema))
        volume_output = os.path.join(BASE_FP, "standardized", "volume.json")
        with open(volume_output, "w") as f:
            json.dump(ATRs, f)

    print("- output written to {}".format(volume_output))
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--city", type=str,
                        help="city short name, e.g. boston")
    parser.add_argument("-d", "--datadir", type=str,
                        help="data directory")

    args = parser.parse_args()

    BASE_FP = os.path.join(args.datadir)
    PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')

    raw_path = os.path.join(BASE_FP, "raw/volume")
    if not os.path.exists(raw_path):
        print(raw_path+" not found, exiting")
        exit(1)

#    # load config for this city
#    config_file = os.path.join(BASE_FP, 'src/config',
#                               "config_"+args.destination+".yml")
#    with open(config_file) as f:
#        config = yaml.safe_load(f)

    parse_ATRs(os.path.join(raw_path, 'ATRs'), args.city)