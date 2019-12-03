import os
from time import sleep
from os.path import exists as path_exists
import csv
import geocoder

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))
PROCESSED_DATA_FP = BASE_DIR + '/data/processed/'


def read_geocode_cache(filename=PROCESSED_DATA_FP+'geocoded_addresses.csv'):
    """
    Read in a csv file with columns:
        Input address
        Output address
        Latitude
        Longitude
        Status (whether the geocoding was successful 'S', or the address
            could not be found 'F', or there was an intermittent error such as
            a time out, '')
    Args:
        filename
    Results:
        dict of input address to list of output address, latitude, longitude
    """

    if not path_exists(filename):
        return {}
    cached = {}
    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            cached[r['Input Address']] = [
                r['Output Address'],
                r['Latitude'],
                r['Longitude'],
                r['Status'],
            ]
    return cached


def write_geocode_cache(results,
                        filename=PROCESSED_DATA_FP + 'geocoded_addresses.csv'):
    """
    Write a csv file with columns:
        Input address
        Output address
        Latitude
        Longitude
    Args:
        results - dict of geocoded results
        filename - file to write to (defaults to geocoded_addresses.csv)
    """

    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Input Address',
            'Output Address',
            'Latitude',
            'Longitude',
            'Status',
        ])
        for key, value in results.items():
            writer.writerow([key, value[0], value[1], value[2], value[3]])


def lookup_address(intersection, cached, mapboxtoken=None):
    """
    Look up an intersection first in the cache, and if it
    doesn't exist, geocode it

    Args:
        intersection: string
        cached: dict
    Returns:
        tuple of original address, geocoded address, latitude, longitude
    """

    # If we've cached this either successfully or were unable to find
    # the address previously
    if intersection in list(cached.keys()) and cached[intersection][3]:
        print(intersection + ' is cached')
        return cached[intersection]
    else:
        print('geocoding ' + intersection)
        return list(geocode_address(intersection, {}, mapboxtoken))


def geocode_address(address, cached={}, mapboxtoken=None):
    """
    Check an optional cache to see if we already have the geocoded address
    Otherwise, use google's API to look up the address
    Due to rate limiting, try a few times with an increasing
    wait if no address is found

    Args:
        address
        cached (optional)
    Returns:
        address, latitude, longitude, status
    """

    if address in list(cached.keys()):
        return cached[address]
    if mapboxtoken:
        g = geocoder.mapbox(address, key=mapboxtoken)
    else:
        g = geocoder.arcgis(address)
    attempts = 0
    while g.address is None and attempts < 3:
        attempts += 1
        sleep(attempts ** 2)
        g = geocoder.google(address)

    status = ''

    if g.status == 'OK':
        status = 'S'
    elif g.status == 'ZERO_RESULTS':
        status = 'F'
    return g.address, g.lat, g.lng, status

