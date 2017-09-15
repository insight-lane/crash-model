# coding: utf-8

# Functions to deal with shape files

import fiona
import csv
import pyproj
from shapely.geometry import mapping, Point, shape
import os
import re
import geocoder


# Project projection = EPSG:3857
PROJ = pyproj.Proj(init='epsg:3857')
RAW_DATA_FP = '../data/raw'
PROCESSED_DATA_FP = '../data/processed'


def read_record(record, x, y, orig=None, new=PROJ):
    """
    Reads record, outputs dictionary with point and properties
    Specify orig if reprojecting
    """
    if (orig is not None):
        x, y = pyproj.transform(orig, new, x, y)
    r_dict = {
        'point': Point(float(x), float(y)),
        'properties': record
    }
    return(r_dict)


def read_csv(file):
    # Read in CAD crash data
    crash = []
    with open(file) as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            # Some crash 0 / blank coordinates
            if r['X'] != '':
                crash.append(
                    read_record(r, r['X'], r['Y'],
                                orig=pyproj.Proj(init='epsg:4326'))
                )
    return crash


def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)


def write_shp(schema, fp, data, shape_key, prop_key):
    """ Write Shapefile
    schema : schema dictionary
    shape_key : column name or tuple index of Shapely shape
    prop_key : column name or tuple index of properties
    """
    with fiona.open(fp, 'w', 'ESRI Shapefile', schema) as c:
        for i in data:
            c.write({
                'geometry': mapping(i[shape_key]),
                'properties': i[prop_key],
            })


def find_nearest(records, segments, segments_index, tolerance):
    """ Finds nearest segment to records
    tolerance : max units distance from record point to consider
    """

    print "Using tolerance {}".format(tolerance)

    for record in records:
        record_point = record['point']
        record_buffer_bounds = record_point.buffer(tolerance).bounds
        nearby_segments = segments_index.intersection(record_buffer_bounds)
        segment_id_with_distance = [
            # Get db index and distance to point
            (
                segments[segment_id][1]['id'],
                segments[segment_id][0].distance(record_point)
            )
            for segment_id in nearby_segments
        ]
        # Find nearest segment
        if len(segment_id_with_distance):
            nearest = min(segment_id_with_distance, key=lambda tup: tup[1])
            db_segment_id = nearest[0]
            # Add db_segment_id to record
            record['properties']['near_id'] = db_segment_id
        # If no segment matched, populate key = ''
        else:
            record['properties']['near_id'] = ''


def geocode_atrs(atr_address):

    # GEOCODE
    # check if there's already a geocoded file, if not, geocode
    # this uses Google, which may not play nice all the time
    # definitely check your data.zip, it should have a geocoded file
    if not os.path.exists(PROCESSED_DATA_FP + '/geocoded_atrs.csv'):
        print "No geocoded_atrs.csv found, geocoding addresses"
        g = geocoder.google(atr_address[0] + ' Boston, MA')

        # geocode, parse result - address, lat long
        results = []
        for add in atr_address:
            print "{}% done".format(1.*atr_address.index(add)/len(atr_address))
            g = geocoder.google(add + ' Boston, MA')
            r = [add, g.address, g.lat, g.lng]
            results.append(r)

        with open(PROCESSED_DATA_FP+'/geocoded_atrs.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(['orig', 'geocoded', 'lat', 'lng'])
            for r in results:
                writer.writerow(r)


def parse_atrs():
    # parse out clean addresses
    atrs = os.listdir(RAW_DATA_FP + r'/AUTOMATED TRAFFICE RECORDING/')
    atr_split = [x.split('_') for x in atrs]
    atr_address = [' '.join(x[3:5]) for x in atr_split]
    atr_address = [re.sub('-', ' ', x) for x in atr_address]
    # just get the unique addresses
    atr_address = list(set(atr_address))
    return atr_address


def read_atrs():
    # Read in atr lats
    atrs = []
    with open(PROCESSED_DATA_FP + '/geocoded_atrs.csv') as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            # Some crash 0 / blank coordinates
            if r['lat'] != '':
                atrs.append(
                    read_record(r, r['lng'], r['lat'],
                                orig=pyproj.Proj(init='epsg:4326'))
                )
    print "Read in data from {} atrs".format(len(atrs))
    return atrs
