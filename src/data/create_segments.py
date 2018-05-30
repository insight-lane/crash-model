
# coding: utf-8

# Segment (intersection and non-intersection) creation
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import fiona
import rtree
import json
import copy
from fiona.crs import from_epsg
from shapely.geometry import shape, Point, LineString
from shapely.ops import unary_union
from collections import defaultdict
import util
import argparse
import os
import shutil
import geojson

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def get_intersection_buffers(intersections, intersection_buffer_units):
    """
    Buffers intersection according to proj units
    Args:
        intersections
        intersection_buffer_units - in meters
    Returns:
        a list of polygons, buffering the intersections
        these are circles, or groups of overlapping circles
    """

    buffered_intersections = [Point(intersection[
        'geometry']['coordinates']).buffer(intersection_buffer_units)
        for intersection in intersections]

    return unary_union(buffered_intersections)


def find_non_ints(roads, int_buffers):
    """
    Find the segments that aren't intersections
    Args:
        roads - a list of tuples of shapely shape and dict of segment info
        int_buffers - a list of polygons that buffer intersections
    Returns:
        tuple consisting of:
            non_int_lines - list in same format as input roads, just a subset
                each element in the list is a tuple of LineString or
                MultiLineString and dict of properties
            inter_segments - dict of lists with keys data and lines
                each element in the lines list is one of the lines
                overlapping the intersection buffer, and each element
                each element in the data list is a dict of properties
                corresponding to the lines
    """

    # Create index for quick lookup
    print "creating rindex"

    int_buffers_index = rtree.index.Index()

    for idx, intersection_buffer in enumerate(int_buffers):
        int_buffers_index.insert(idx, intersection_buffer.bounds)

    # Split intersection lines (within buffer) and non-intersection lines
    # (outside buffer)
    print "splitting intersection/non-intersection segments"
    inter_segments = {'lines': defaultdict(list), 'data': defaultdict(list)}

    non_int_lines = []

    for road in roads:
        road_int_buffers = []
        # For each intersection whose buffer intersects road
        road_line = LineString(road['geometry']['coordinates'])
        for idx in int_buffers_index.intersection(road_line.bounds):

            int_buffer = int_buffers[idx]
            if int_buffer.intersects(road_line):
                # Add intersecting road segment line
                inter_segments['lines'][idx].append(
                    int_buffer.intersection(road_line))
                # Add intersecting road segment data
                road['properties']['inter'] = 1
                inter_segments['data'][idx].append(road['properties'])

                road_int_buffers.append(int_buffer)

        # If intersection buffers intersect roads
        if len(road_int_buffers) > 0:
            # Find part of road outside of the intersecting parts
            diff = road_line.difference(unary_union(road_int_buffers))
            if 'LineString' == diff.type:
                non_int_lines.append(geojson.Feature(
                    geometry=geojson.LineString([x for x in diff.coords]),
                    properties=road['properties'])
                )
            elif 'MultiLineString' == diff.type:
                coords = []
                for l in diff:
                    for coord in l.coords:
                        coords.append(coord)
                non_int_lines.append(geojson.Feature(
                    geometry=geojson.LineString(coords),
                    properties=road['properties'])
                )

    return non_int_lines, inter_segments


def add_point_based_features(non_inters, inters, feats_filename):
    """
    Add any point-based set of features to existing segment data.
    If it isn't already attached to the segments
    Point-based features need to be in 3857 projection
    Args:
        non_inters
        inters
        feats_filename - geojson file for point-based features data
    """

    features = util.read_records_from_geojson(feats_filename)

    seg, segments_index = util.index_segments(
        inters + non_inters
    )

    util.find_nearest(features, seg, segments_index, 20, type_record=True)

    matches = {}

    for feature in features:
        near = feature.near_id
        feat_type = feature.properties['feature']
        if near:
            if str(near) not in matches.keys():
                matches[str(near)] = []
            matches[str(near)].append(feat_type)

    # Add point data to intersections
    for i, inter in enumerate(inters):
        if str(inter['properties']['id']) in matches.keys():
            matched_features = set(matches[str(inter['properties']['id'])])
            # Since intersections consist of multiple segments, add the
            # point-based properties to each of them
            for prop in inter['properties']['data']:
                for feat in matched_features:
                    prop[feat] = 1

    # Add point data to non-intersections
    for i, non_inter in enumerate(non_inters):
        if str(non_inter['properties']['id']) in matches.keys():
            matched_features = set(matches[non_inter['properties']['id']])
            n = copy.deepcopy(non_inter)
            for feat in matched_features:
                n[feat] = 1
            non_inters[i] = n

    return non_inters, inters


def create_segments_from_json(roads_shp_path):

    with open(roads_shp_path) as f:
        data = json.load(f)

    # All the line strings are roads
    roads = [x for x in data['features']
             if x['geometry']['type'] == 'LineString']

    print "read in {} road segments".format(len(roads))

    # unique id did not get included in shapefile, need to add it for adjacency
    for i, road in enumerate(roads):
        road['properties']['orig_id'] = int(str(99) + str(i))

    # Get the intersection list by excluding anything that's not labeled
    # as an intersection
    inters = [x for x in data['features'] if x['geometry']['type'] == 'Point'
              and 'intersection' in x['properties'].keys()
              and x['properties']['intersection']]

    # Initial buffer = 20 meters
    int_buffers = get_intersection_buffers(inters, 20)
    polys = []
    for buffer in int_buffers:
        coords = [[x for x in buffer.exterior.coords]]
        polys.append(geojson.Feature(
            geometry=geojson.Polygon(coords), properties={}))

    buff = geojson.FeatureCollection(polys)
    with open(os.path.join(
            MAP_FP, 'buffers.geojson'), 'w') as outfile:
        geojson.dump(buff, outfile)

    non_int_lines, inter_segments = find_non_ints(
        roads, int_buffers)

    non_int_w_ids = []

    for i, l in enumerate(non_int_lines):
        value = copy.deepcopy(l)
        value['type'] = 'Feature'
        value['properties']['id'] = '00' + str(i)
        value['properties']['inter'] = 0
        non_int_w_ids.append(value)

    print "extracted {} non-intersection segments".format(len(non_int_w_ids))

    # Planarize intersection segments
    # Turns the list of LineStrings into a MultiLineString
    union_inter = []
    for idx, lines in inter_segments['lines'].items():

        lines = unary_union(lines)

        coords = []
        for line in lines:
            coords += [[x for x in line.coords]]

        properties = {
            'id': idx,
            'data': inter_segments['data'][idx]
        }
        union_inter.append(geojson.Feature(
            geometry=geojson.MultiLineString(coords),
            id=idx,
            properties=properties,
        ))

    return non_int_w_ids, union_inter


def write_segments(non_inters, inters):

    # Store non-intersection segments
    with open(os.path.join(
            MAP_FP, 'non_inters_segments.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': non_inters
        }, outfile)

    # Get just the properties for the intersections
    inter_data = [x['properties']['data'] for x in inters]

    with open(os.path.join(DATA_FP, 'inters_data.json'), 'w') as f:
        json.dump(inter_data, f)

    # Store the individual intersections without properties, since QGIS appears
    # to have trouble with dicts of dicts, and viewing maps can be helpful
    int_w_ids = [{
        'geometry': x['geometry'],
        'properties': {'id': x['properties']['id']}
    } for x in inters]

    with open(os.path.join(MAP_FP, 'inters_segments.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': int_w_ids
        }, outfile)

    # Store the combined segments with all properties
    segments = non_inters + inters

    with open(os.path.join(MAP_FP, 'inter_and_non_int.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': segments
        }, outfile)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-r", "--altroad", type=str,
                        help="Can give alternate road elements geojson file")
    parser.add_argument("-n", "--newmap", type=str,
                        help="If given, write output to new directory" +
                        "within the maps directory")

    args = parser.parse_args()
    DATA_FP = os.path.join(args.datadir, 'processed')
    MAP_FP = os.path.join(args.datadir, 'processed/maps')

    if args.newmap:
        DATA_FP = os.path.join(MAP_FP, args.newmap)
        MAP_FP = DATA_FP

    print "Creating segments.........................."

    elements = os.path.join(
        MAP_FP, 'osm_elements.geojson')
    if args.altroad:
        elements = args.altroad

    non_inters, inters = create_segments_from_json(elements)

    feats_file = os.path.join(MAP_FP, 'features.geojson')
    if os.path.exists(feats_file):
        non_inters, inters = add_point_based_features(
            non_inters,
            inters,
            os.path.join(MAP_FP, 'features.geojson')
        )
    write_segments(non_inters, inters)

