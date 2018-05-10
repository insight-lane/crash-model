
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
                non_int_lines.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [x for x in diff.coords],
                    },
                    'properties': road['properties']
                })
            elif 'MultiLineString' == diff.type:

                coords = []
                for l in diff:
                    for coord in l.coords:
                        coords.append(coord)

                non_int_lines.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coords,
                    },
                    'properties': road['properties']
                })

    return non_int_lines, inter_segments


def reproject_and_read(infile, outfile):
    """
    Reprojects points from the inters shapefile to a new projection
        and writes to file
    Args:
        infile - shapefile to read from
        outfile - shapefile to write to, in new projection
    Returns:
        inters - the reprojected intersections
    """

    # Reproject to 3857
    # Necessary because original intersection extraction had null projection
    print "Reprojecting map file " + infile
    inters = fiona.open(infile)

    reprojected_records = util.reproject_records(inters)

    # Write the reprojected (to 3857) intersections to file
    with fiona.open(outfile, 'w', crs=from_epsg(3857),
                    schema=inters.schema, driver='ESRI Shapefile') as output:
        for record in reprojected_records:
            output.write(record)

    # Read in reprojected intersection
    reprojected_inters = [(shape(inter['geometry']), inter['properties'])
                          for inter in fiona.open(outfile)]
    print "read in {} intersection points".format(len(reprojected_inters))
    return reprojected_inters


def backup_files():
    """
    Make a copy of inters_segments, non_inters_segments, and inters_data
    Since we'll be modifying these files if we add features from another source
    """
    shp_files = [
        file for file in os.listdir(MAP_FP) if 'inters_segments.' in file]

    for file in shp_files:
        file_segs = file.split('.')
        shutil.copyfile(
            os.path.join(MAP_FP, file),
            os.path.join(MAP_FP, file_segs[0] + '_orig.' + file_segs[1]))
    # Also copy inters_data.json
    shutil.copyfile(
        os.path.join(DATA_FP, 'inters_data.json'),
        os.path.join(DATA_FP, 'inters_data_orig.json')
    )


def add_point_based_features(non_inters, inters, inter_data, filename):
    """
    Add any point-based set of features to existing segment data.
    If it isn't already attached to the segments
    Point-based features need to be in 3857 projection
    Args:
        inter_data
        filename - shape file for the osm signals data
    """

    features = util.read_records(filename, 'Record')

    seg, segments_index = util.index_segments(
        inters + non_inters
    )

    util.find_nearest(features, seg, segments_index, 20, type_record=True)
    import ipdb; ipdb.set_trace()


    matches = {}
    for feature in features:
        near = feature.near_id
        feat_type = feature.properties['feature']
        if near:
            matches[near] = feat_type

#    import ipdb; ipdb.set_trace()
    new_inter_data = {}
    for key, segments in inter_data.iteritems():
        updated_segments = []
        for segment in segments:
            signal = '0'
            if key in matches.keys():
                signal = '1'
            segment.update({'signal': signal})
            updated_segments.append(segment)
        new_inter_data[key] = updated_segments

    with open(os.path.join(DATA_FP, 'inters_data.json'), 'w') as f:
        json.dump(inter_data, f)


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
        coords = []
        shape = unary_union(lines)

        for line in shape:
            for coord in line.coords:
                coords.append(coord)

        union_inter.append({
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': coords,
            },
            # Properties will consist of an id, and the data elements, for now
            'properties': {
                'id': idx,
                'data': inter_segments['data'][idx]
            }
        })

    return non_int_w_ids, union_inter, inter_segments['data']


def write_segments(non_int_w_ids, union_inter, inter_data):

    # Store the combined segments with all properties
    segments = non_int_w_ids + union_inter

    import ipdb; ipdb.set_trace()

    with open(os.path.join(MAP_FP, 'inter_and_non_int.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': segments
        }, outfile)

    # Store the individual intersections without properties, since QGIS appears
    # to have trouble with dicts of dicts, and viewing maps can be helpful
    with open(os.path.join(MAP_FP, 'inters_segments.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': union_inter
        }, outfile)

    with open(os.path.join(MAP_FP, 'non_inters_segments.geojson'), 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': non_int_w_ids
        }, outfile)

    with open(os.path.join(DATA_FP, 'inters_data.json'), 'w') as f:
        json.dump(inter_data, f)



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-r", "--altroad", type=str,
                        help="Can give alternate road shape file")
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

    roads_shp_path = os.path.join(
        MAP_FP, 'osm_elements.geojson')
    if args.altroad:
        roads_shp_path = args.altroad

    elements = os.path.join(MAP_FP, 'osm_elements.geojson')
    non_int_w_ids, inter_w_ids, inter_data \
        = create_segments_from_json(elements)

#    add_point_based_features(non_int_w_ids,
#                             inter_w_ids,
#                             inter_data,
#                             os.path.join(MAP_FP, 'features.json'))
    write_segments(non_int_w_ids, inter_w_ids, inter_data)


#    inter_data = create_segments(roads_shp_path)

    # Once the intersections and non_intersection segments exist,
    # other features can be added
#    signal_file = os.path.join(MAP_FP, 'osm_signals.shp')
#    if os.path.exists(signal_file):
#        add_signals(inter_data, signal_file)

#    backup_files()
