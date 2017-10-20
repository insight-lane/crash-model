import re
import csv

import fiona
from shapely.geometry import Point, shape, mapping
import pyproj


PROJ = pyproj.Proj(init='epsg:3857')


def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)


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


