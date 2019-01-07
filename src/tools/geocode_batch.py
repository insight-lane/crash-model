
import argparse
import os
import csv
from data.util import lookup_address, read_geocode_cache


def parse_addresses(directory, filename, city, addressfield,
                    mapboxtoken=None):

    cached = read_geocode_cache(filename=os.path.join(
        directory, 'processed', 'geocoded_addresses.csv'))

    results = []
    geocoded_count = [0, 0, 0]

    # Read in the csv file
    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            address = r[addressfield] + ' ' + city
            geocoded_add, lat, lng, status = lookup_address(
                address, cached, mapboxtoken=mapboxtoken)
            cached[address] = [geocoded_add, lat, lng, status]

            if status == 'S':
                geocoded_count[0] += 1
            elif status == 'F':
                geocoded_count[1] += 1
            else:
                geocoded_count[2] += 1

    print('Number successfully geocoded: {}'.format(geocoded_count[0]))
    print('Unable to geocode: {}'.format(geocoded_count[1]))
    print('Timed out on {} addresses'.format(geocoded_count[2]))

    # Write out the cache
    with open(os.path.join(directory, 'processed',
                           'geocoded_addresses.csv'), 'w') as csvfile:

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str, required=True)
    parser.add_argument("-f", "--filename", type=str, required=True)
    parser.add_argument("-c", "--city", type=str, required=True)
    parser.add_argument("-a", "--address", type=str, required=True,
                        help="Address column name")
    parser.add_argument('-m', '--mapboxtoken', type=str,
                        help="mapbox token")
    args = parser.parse_args()
    parse_addresses(args.directory, args.filename, args.city,
                    args.address, args.mapboxtoken)

