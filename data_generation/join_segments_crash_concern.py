
# coding: utf-8


# Joining segments (intersection and non-intersection) to crash/concern data
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import fiona
import json
import os
import pyproj
import rtree
import csv
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point, MultiPoint, shape, mapping

# Project projection = EPSG:3857
PROJ = pyproj.Proj(init='epsg:3857')
MAP_FP = './data/maps'
DATA_FP = './data'


def read_record(record, x, y, orig=None, new=PROJ):
    """
    Reads record, outputs dictionary with point and properties
    Specify orig if reprojecting
    """
    if (orig is not None):
        x, y = pyproj.transform(orig, new, x, y)
    r_dict = {
        'point': Point(float(x), float(y)),
        'properties': r
    }
    return(r_dict)


def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)
def make_schema(geometry, properties):
    """
    Utility for making schema with 'str' value for each key in properties
    """
    properties_dict = {k: 'str' for k, v in properties.items()}
    schema = {
        'geometry': geometry,
        'properties': properties_dict
    }
    return(schema)
    
def write_shp(schema, fp, data, shape_key, prop_key):
    # Write a new Shapefile
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

# Read in CAD crash data
crash = []
with open(DATA_FP + '/cad_crash_events_with_transport_2016_wgs84.csv') as f:
    csv_reader = csv.DictReader(f)
    for r in csv_reader:
        # Some crash 0 / blank coordinates
        if r['X'] != '':
            crash.append(
                read_record(r, r['X'], r['Y'],
                            orig=pyproj.Proj(init='epsg:4326'))
            )
print "Read in data from {} crashes".format(len(crash))

# Read in vision zero data
concern = []
# Have to use pandas read_csv, unicode trubs
concern_raw = pd.read_csv(DATA_FP + '/Vision_Zero_Entry.csv')
concern_raw = concern_raw.to_dict('records')
for r in concern_raw:
    concern.append(
        read_record(r, r['X'], r['Y'],
                    orig=pyproj.Proj(init='epsg:4326'))
    )
print "Read in data from {} concerns".format(len(concern))

#Read in segments
inter = read_shp(MAP_FP + '/inters_segments.shp')
non_inter = read_shp(MAP_FP + '/non_inters_segments.shp')
print "Read in {} intersection, {} non-intersection segments".format(len(inter), len(non_inter))

# Combine inter + non_inter
combined_seg = inter + non_inter

# Create spatial index for quick lookup
segments_index = rtree.index.Index()
for idx, element in enumerate(combined_seg):
    segments_index.insert(idx, element[0].bounds)

# Find nearest crashes - 30 tolerance
print "snapping crashes to segments"
find_nearest(crash, combined_seg, segments_index, 30)

# Find nearest concerns - 20 tolerance
print "snapping concerns to segments"
find_nearest(concern, combined_seg, segments_index, 20)

# Write concerns
concern_schema = make_schema('Point', concern[0]['properties'])
print "output concerns shp to ", MAP_FP
write_shp(concern_schema, MAP_FP + '/concern_joined.shp',
          concern, 'point', 'properties')
print "output concerns data to ", DATA_FP
with open(DATA_FP + '/concern_joined.json', 'w') as f:
    json.dump([c['properties'] for c in concern], f)

# Write crash
crash_schema = make_schema('Point', crash[0]['properties'])
print "output crash shp to ", MAP_FP
write_shp(crash_schema, MAP_FP + '/crash_joined.shp',
          crash, 'point', 'properties')
print "output crash data to ", DATA_FP
with open(DATA_FP + '/crash_joined.json', 'w') as f:
    json.dump([c['properties'] for c in crash], f)

