
# coding: utf-8

# Segment (intersection and non-intersection) creation
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import rtree
import json
import copy
from shapely.ops import unary_union
from collections import defaultdict
from . import util
import argparse
import os
import geojson
import re
from shapely.geometry import MultiLineString, LineString
from .segment import Segment


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')
DATA_FP = None


def get_intersection_buffers(intersections, intersection_buffer_units,
                             debug=False):
    """
    Buffers intersection according to proj units
    Args:
        intersections
        intersection_buffer_units - in meters
        debug - if true, will output the buffers to file for debugging
    Returns:
        a list of polygons, buffering the intersections
        these are circles, or groups of overlapping circles
    """

    buffered_intersections = [intersection['geometry'].buffer(
        intersection_buffer_units) for intersection in intersections]

    buffered_intersections = unary_union(buffered_intersections)
    if debug:
        util.output_from_shapes(
            [(x, {}) for x in buffered_intersections],
            os.path.join(MAP_FP, 'int_buffers.geojson')
        )

    results = []

    # Index the intersection points for fast lookup
    inter_index = rtree.index.Index()
    for idx, inter_point in enumerate(intersections):
        inter_index.insert(idx, inter_point['geometry'].bounds)

    # Get the points that overlap with the buffers
    for buff in buffered_intersections:
        matches = []
        for idx in inter_index.intersection(buff.bounds):
            if intersections[idx]['geometry'].within(buff):
                matches.append(intersections[idx]['geometry'])
        results.append([buff, matches])

    return results


def get_connections(points, segments):
    """
    Gets intersections by looking at the connections between points
    and segments that fall within an intersection buffer
    Args:
        points - a list of points
        segments - a list of segment objects
    Returns:
        A list of tuples for each intersection.
        Each tuple contains a set of segment objects
        and the buffer of the unary_union of the segment objects
        with a little bit of padding, because of a slight precision error
        in shapely operations
    """
    # Create a dict with each intersection point's coords as key
    # The values are the point itself and an empty list that will
    # store all the linestrings with a connection to the point
    inters = []
    for p in points:
        inters.append([p, []])

    # Get a starting list of all lines that touch any of the
    # intersection points
    for line in segments:
        for i, (curr_shape, _) in enumerate(inters):
            if line.geometry.distance(curr_shape) < .0001:
                inters[i][1].append(line)
                inters[i][0] = unary_union([inters[i][0], line.geometry])

    # Merge connected components
    resulting_inters = []
    connected_lines = []
    while inters:
        curr = inters.pop(0)
        if inters:
            connected = [x[1] for x in inters if x[0].intersects(
                    curr[0]
            )]

            if connected:
                connected_lines = set(
                    curr[1] + [x for y in connected for x in y]
                )
            else:
                connected_lines = set(curr[1])
        else:
            connected_lines = set(curr[1])
        inters = [x for x in inters if not x[0].intersects(curr[0])]
        
        resulting_inters.append((connected_lines, unary_union(
            [x.geometry for x in connected_lines]).buffer(.001)
        ))

    return resulting_inters


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
    print("creating rindex")

    road_lines_index = rtree.index.Index()
    buffered_lines = []
    for idx, road in enumerate(roads):
        b = road.geometry.buffer(20)
        buffered_lines.append((b, road))
        road_lines_index.insert(idx, b.bounds)

    inter_segments = {'lines': defaultdict(list), 'data': defaultdict(list)}
    roads_with_int_segments = {}
    count = 0
    print("Generating intersection segments")
    for i, int_buffer in enumerate(int_buffers):
        util.track(i, 1000, len(int_buffers))
        match_segments = []
        matched_roads = []
        for idx in road_lines_index.intersection(int_buffer[0].bounds):
            road = roads[idx]
            match_segments.append(Segment(road.geometry.intersection(
                int_buffer[0]), road.properties))
            matched_roads.append(road)

        int_segments = get_connections(int_buffer[1], match_segments)

        # Each road_with_int is a road segment and a list of lists of segments
        # representing the intersections
        # to-do: turn these into intersection objects
        for r in matched_roads:
            if r.properties['id'] not in roads_with_int_segments:
                roads_with_int_segments[r.properties['id']] = []
            roads_with_int_segments[r.properties['id']] += int_segments

        for int_segment in int_segments:
            inter_segments['lines'][count] = [
                x.geometry for x in int_segment[0]]
            inter_segments['data'][count] = [
                x.properties for x in int_segment[0]]
            count += 1
    non_int_lines = []
    print("Generating non-intersection segments")
    for i, road in enumerate(roads):
        util.track(i, 1000, len(roads))
        # If there's no overlap between the road segment and any intersections
        if road.properties['id'] not in roads_with_int_segments:
            non_int_lines.append(geojson.Feature(
                geometry=geojson.LineString([x for x in road.geometry.coords]),
                properties=road.properties
            ))
        else:

            # Check against each separate intersection
            road_info = roads_with_int_segments[road.properties['id']]

            diff = road.geometry
            for inter in road_info:
                buffered_int = inter[1]
                diff = diff.difference(buffered_int)
            if 'LineString' == diff.type:
                non_int_lines.append(geojson.Feature(
                    geometry=geojson.LineString([x for x in diff.coords]),
                    properties=road.properties)
                )
            elif 'MultiLineString' == diff.type:
                coords = []
                for l in diff:
                    for coord in l.coords:
                        coords.append(coord)
                non_int_lines.append(geojson.Feature(
                    geometry=geojson.LineString(coords),
                    properties=road.properties)
                )
            else:
                # There may be no sections of the segment that fall outside
                # of an intersection, in which case it's skipped
                if len(diff) == 0:
                    continue
                print("{} found, skipping".format(diff.type))

    return non_int_lines, inter_segments


def add_point_based_features(non_inters, inters, jsonfile,
                             feats_filename=None,
                             additional_feats_filename=None,
                             forceupdate=False):
    """
    Add any point-based set of features to existing segment data.
    If it isn't already attached to the segments
    Args:
        non_inters
        inters
        jsonfile - points_joined.json, storing the results of snapping
        feats_filename - geojson file for point-based features data
        addtiional_feats_filename (optional) - file for additional
            points-based data, in json format
        forceupdate - if True, re-snap points and write to file
    """

    if forceupdate or not os.path.exists(jsonfile):
        features = []
        if feats_filename:
            features = util.read_records_from_geojson(feats_filename)
        if additional_feats_filename:
            features += util.read_records(
                additional_feats_filename, 'record')
        print('Snapping {} point-based features'.format(len(features)))
        seg, segments_index = util.index_segments(
            inters + non_inters
        )

        util.find_nearest(features, seg, segments_index, 20, type_record=True)

        # Dump to file
        print("output {} point-based features to {}".format(
            len(features), jsonfile))
        with open(jsonfile, 'w') as f:
            json.dump([r.properties for r in features], f)

    else:
        features = util.read_records(jsonfile, None)
        print("Read {} point-based features from file".format(len(features)))
    matches = {}


    aggregation_values = defaultdict(dict)

    for feature in features:
        near = feature.near_id
        feat_type = feature.properties['feature']
        feat_agg_type = ""

        if 'feat_agg' in feature.properties and 'value' in feature.properties:
            feat_agg_type = feature.properties['feat_agg']
            date = feature.properties['date']

        if near:
            if str(near) not in matches:
                matches[str(near)] = {}

            if feat_agg_type == 'latest':  
                aggregation_values[(str(near), feat_type)][date] = feature.properties['value']
            else:
                if feat_type not in matches[str(near)]:
                    matches[str(near)][feat_type] = 0
                matches[str(near)][feat_type] += 1

    # if latest, sorts dates for each near/feat_type and puts latest in proper loc. in matches dict 
    for str_near, feat_type in aggregation_values.keys(): 
        values_all_dates = aggregation_values[(str_near, feat_type)]
        latest_date = max(values_all_dates.keys())
        matches[str_near][feat_type] = values_all_dates[latest_date]

    # Add point data to intersections
    for i, inter in enumerate(inters):
        if str(inter['properties']['id']) in list(matches.keys()):
            matched_features = matches[str(inter['properties']['id'])]
            
            # Since intersections consist of multiple segments, add the
            # point-based properties to each of them

            for prop in inter['properties']['data']:
                for feat in matched_features:
                    prop[feat] = matched_features[feat]

    # Add point data to non-intersections
    for i, non_inter in enumerate(non_inters):
        if str(non_inter['properties']['id']) in list(matches.keys()):
            matched_features = matches[non_inter['properties']['id']]

            n = copy.deepcopy(non_inter)

            for feat in matched_features:
                n['properties'][feat] = matched_features[feat]

            non_inters[i] = n

    return non_inters, inters


def get_intersection_name(inter_segments):
    """
    Get an intersection name from a set of intersection segment names
    Args:
        inter_segments - a list of properties
    Returns:
        intersection name - a string, e.g. First St and Second St
    """

    streets = []
    # Some open street maps segments have more than one name in them
    for street in [x['name'] if 'name' in x.keys() else None
                   for x in inter_segments]:
        if street:
            if '[' in street:
                streets.extend(re.sub("['\[\]]", '', street).split(', '))
            else:
                streets.append(street)
    streets = sorted(list(set(streets)))

    name = ''
    if not streets:
        return name
    if len(streets) == 2:
        name = streets[0] + " and " + streets[1]
    else:
        name = streets[0] + " near "
        name += ', '.join(streets[1:-1]) + ' and ' + streets[-1]

    return name


def get_non_intersection_name(non_inter_segment, inters_by_id):
    """
    Get non-intersection segment names. Mostly in the form:
    X Street between Y Street and Z Street, but sometimes the
    intersection has streets with two different names, in which case
    it will be X Street between Y Street/Z Street and A Street,
    or it's a dead end, in which case it will be X Street from Y Street
    Args:
        non_inter_segment - a geojson non intersection segment
        inters_by_id - a dict with osm node ids as keys
    Returns:
        The display name string
    """

    properties = non_inter_segment['properties']

    if 'name' not in properties or not properties['name']:
        return ''
    segment_street = properties['name']
    from_streets = None
    to_streets = None
    if properties['from'] in inters_by_id and inters_by_id[properties['from']]:
        from_street = inters_by_id[properties['from']]
        from_streets = from_street.split(', ')

        # Remove any street that's part of the named street sections
        if segment_street in from_streets:
            from_streets.remove(segment_street)
    if properties['to'] in inters_by_id and inters_by_id[properties['to']]:
        to_street = inters_by_id[properties['to']]
        to_streets = to_street.split(', ')

        # Remove any street that's part of the named street sections
        if segment_street in to_streets:
            to_streets.remove(segment_street)

    if not from_streets and not to_streets:
        return segment_street

    from_street = None
    if from_streets:
        from_street = '/'.join(from_streets)
    to_street = None
    if to_streets:
        to_street = '/'.join(to_streets)

    if not to_streets:
        return segment_street + ' from ' + from_street
    if not from_streets:
        return segment_street + ' from ' + to_street

    return segment_street + ' between ' + from_street + \
        ' and ' + to_street

    return segment_street


def create_segments_from_json(roads_shp_path, mapfp):
    roads, inters = util.get_roads_and_inters(roads_shp_path)
    print("read in {} road segments".format(len(roads)))

    # unique id did not get included in shapefile, need to add it for adjacency
    for i, road in enumerate(roads):
        road.properties['orig_id'] = int(str(99) + str(i))

    # Initial buffer = 20 meters
    int_buffers = get_intersection_buffers(inters, 20)
    print("Found {} intersection buffers".format(len(int_buffers)))
    non_int_lines, inter_segments = find_non_ints(
        roads, int_buffers)

    non_int_w_ids = []

    # Allow intersections that don't have osmids, because this
    # happens when we generate alternate maps from city data
    # They won't have display names, and this is okay, because
    # we only use them to map to the osm segments
    inters_by_id = {
        x['properties']['osmid'] if 'osmid' in x['properties'] else '0':
        x['properties']['streets']
        if 'streets' in x['properties'] else None
        for x in inters
    }

    for i, l in enumerate(non_int_lines):
        value = copy.deepcopy(l)
        value['type'] = 'Feature'
        value['properties']['id'] = '00' + str(i)
        value['properties']['inter'] = 0
        value['properties']['display_name'] = get_non_intersection_name(
            l, inters_by_id)
        non_int_w_ids.append(value)

        x, y = util.get_center_point(value)
        x, y = util.reproject([[x, y]], inproj='epsg:3857',
                              outproj='epsg:4326')[0]['coordinates']
        value['properties']['center_y'] = y
        value['properties']['center_x'] = x

    print("extracted {} non-intersection segments".format(len(non_int_w_ids)))

    # Planarize intersection segments
    # Turns the list of LineStrings into a MultiLineString
    union_inter = []
    for idx, lines in list(inter_segments['lines'].items()):

        lines = unary_union(lines)
        coords = []
        # Fixing issue where we had previously thought a dead-end node
        # was an intersection. Once this is fixed in osmnx
        # (or we have a better work around), this should be able to
        # be taken out
        if type(lines) == LineString:
            lines = MultiLineString([lines.coords])
        for line in lines:
            coords += [[x for x in line.coords]]

        name = get_intersection_name(inter_segments['data'][idx])
        # Add the number of segments coming into this intersection
        segment_data = []
        for segment in list(inter_segments['data'][idx]):
            segment['intersection_segments'] = len(
                inter_segments['data'][idx])
            segment_data.append(segment)

        properties = {
            'id': idx,
            'data': segment_data,
            'display_name': name
        }
        value = geojson.Feature(
            geometry=geojson.MultiLineString(coords),
            id=idx,
            properties=properties,
        )
        x, y = util.get_center_point(value)
        x, y = util.reproject([[x, y]], inproj='epsg:3857',
                              outproj='epsg:4326')[0]['coordinates']

        value['properties']['center_x'] = x
        value['properties']['center_y'] = y
        union_inter.append(value)

    return non_int_w_ids, union_inter


def write_segments(non_inters, inters, mapfp, datafp):

    # Store non-intersection segments

    # Project back into 4326 for storage

    non_inters = util.prepare_geojson(non_inters)

    with open(os.path.join(
            mapfp, 'non_inters_segments.geojson'), 'w') as outfile:
        geojson.dump(non_inters, outfile)

    # Get just the properties for the intersections
    inter_data = {
        str(x['properties']['id']): x['properties']['data'] for x in inters}

    with open(os.path.join(datafp, 'inters_data.json'), 'w') as f:
        json.dump(inter_data, f)

    # Store the individual intersections without properties, since QGIS appears
    # to have trouble with dicts of dicts, and viewing maps can be helpful
    int_w_ids = [{
        'geometry': x['geometry'],
        'properties': {
            'id': x['properties']['id'],
            'display_name': x['properties']['display_name']
                if 'display_name' in x['properties'] else '',
            'center_x': x['properties']['center_x']
                if 'center_x' in x['properties'] else '',
            'center_y': x['properties']['center_y']
                if 'center_y' in x['properties'] else ''
        }
    } for x in inters]
    
    int_w_ids = util.prepare_geojson(int_w_ids)

    with open(os.path.join(mapfp, 'inters_segments.geojson'), 'w') as outfile:
        geojson.dump(int_w_ids, outfile)

    # Store the combined segments with all properties
    segments = non_inters['features'] + int_w_ids['features']

    with open(os.path.join(mapfp, 'inter_and_non_int.geojson'), 'w') as outfile:
        geojson.dump(geojson.FeatureCollection(segments), outfile)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-r", "--altroad", type=str,
                        help="Can give alternate road elements geojson file." +
                        " This is generated by extract_intersections.py")
    parser.add_argument("-n", "--newmap", type=str,
                        help="If given, write output to new directory" +
                        "within the maps directory")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the points-based data')

    args = parser.parse_args()
    DATA_FP = args.datadir
    PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
    MAP_FP = os.path.join(args.datadir, 'processed/maps')

    if args.newmap:
        PROCESSED_DATA_FP = os.path.join(MAP_FP, args.newmap)
        MAP_FP = PROCESSED_DATA_FP

    print("Creating segments..........................")

    elements = os.path.join(
        MAP_FP, 'osm_elements.geojson')
    if args.altroad:
        elements = args.altroad

    non_inters, inters = create_segments_from_json(elements, MAP_FP)

    feats_file = os.path.join(MAP_FP, 'features.geojson')
    additional_feats_file = os.path.join(
        DATA_FP, 'standardized', 'points.json')
    if not os.path.exists(feats_file):
        feats_file = None
    if not os.path.exists(additional_feats_file):
        additional_feats_file = None

    if feats_file or additional_feats_file:
        jsonfile = os.path.join(DATA_FP, 'processed', 'points_joined.json')
        non_inters, inters = add_point_based_features(
            non_inters,
            inters,
            jsonfile,
            feats_filename=feats_file,
            additional_feats_filename=additional_feats_file,
            forceupdate=args.forceupdate
        )
    write_segments(non_inters, inters, MAP_FP, PROCESSED_DATA_FP)

