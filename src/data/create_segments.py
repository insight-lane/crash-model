
# coding: utf-8

# Segment (intersection and non-intersection) creation
# Draws on: http://bit.ly/2m7469y
# Developed by: bpben

import fiona
import pyproj
import rtree
import json
import copy
from fiona.crs import from_epsg
from shapely.geometry import Point, shape, mapping
from shapely.ops import unary_union
from collections import defaultdict
from util import write_shp


def get_intersection_buffers(intersections, intersection_buffer_units):
    """ Buffers intersection according to proj units """
    buffered_intersections = [intersection[0].buffer(intersection_buffer_units)
                              for intersection in intersections]
    return unary_union(buffered_intersections)


def find_non_ints(roads):
    non_int_lines = []
    for road in roads:
        road_int_buffers = []
        # For each intersection whose buffer intersects road
        for idx in int_buffers_index.intersection(road[0].bounds):
            int_buffer = int_buffers[idx]
            if int_buffer.intersects(road[0]):
                # Add intersecting road segment line
                inter_segments['lines'][idx].append(
                    int_buffer.intersection(road[0]))
                # Add intersecting road segment data
                inter_segments['data'][idx].append(road[1])
                road_int_buffers.append(int_buffer)
        # If intersection buffers intersect roads
        if len(road_int_buffers) > 0:
            # Find part of road outside of the intersecting parts
            diff = road[0].difference(unary_union(road_int_buffers))
            if 'LineString' == diff.type:
                non_int_lines.append((diff, road[1]))
            elif 'MultiLineString' == diff.type:
                non_int_lines.extend([(line, road[1]) for line in diff])
        else:
            non_int_lines.append(road)
    return non_int_lines


if __name__ == '__main__':

    MAP_FP = '../../data/processed/maps'
    DATA_FP = '../../data/processed'

    print "Map data at ", MAP_FP
    print "Output intersection data to ", DATA_FP

    inters_shp_path_raw = MAP_FP + '/inters.shp'
    inters_shp_path = MAP_FP + '/inters_3857.shp'

    # Reproject to 3857
    # Necessary because original intersection extraction had null projection
    print "reprojecting raw intersection shapefile"
    inters = fiona.open(inters_shp_path_raw)
    inproj = pyproj.Proj(init='epsg:4326')
    outproj = pyproj.Proj(init='epsg:3857')

    with fiona.open(inters_shp_path, 'w', crs=from_epsg(3857),
                    schema=inters.schema, driver='ESRI Shapefile') as output:
        for inter in inters:
            coords = inter['geometry']['coordinates']
            re_point = pyproj.transform(inproj, outproj, coords[0], coords[1])
            point = Point(re_point)
            output.write({'geometry': mapping(point),
                          'properties': inter['properties']})

    # Read in boston segments + mass DOT join
    roads_shp_path = MAP_FP + '/ma_cob_spatially_joined_streets.shp'
    roads = [(shape(road['geometry']), road['properties'])
             for road in fiona.open(roads_shp_path)]
    print "read in {} road segments".format(len(roads))

    # unique id did not get included in shapefile, need to add it for adjacency
    for i, road in enumerate(roads):
        road[1]['orig_id'] = int(str(99) + str(i))

    # Read in reprojected intersection
    inters = [(shape(inter['geometry']), inter['properties'])
              for inter in fiona.open(inters_shp_path)]
    print "read in {} intersection points".format(len(inters))

    # Initial buffer = 20 meters
    int_buffers = get_intersection_buffers(inters, 20)

    # Create index for quick lookup
    print "creating rindex"
    int_buffers_index = rtree.index.Index()
    for idx, intersection_buffer in enumerate(int_buffers):
        int_buffers_index.insert(idx, intersection_buffer.bounds)

    # Split intersection lines (within buffer) and non-intersection lines
    # (outside buffer)
    print "splitting intersection/non-intersection segments"
    inter_segments = {}
    inter_segments['lines'] = defaultdict(list)
    inter_segments['data'] = defaultdict(list)

    non_int_lines = find_non_ints(roads)

    # Planarize intersection segments
    union_inter = [({'id': idx}, unary_union(l))
                   for idx, l in inter_segments['lines'].items()]
    print "extracted {} intersection segments".format(len(union_inter))

    # Intersections shapefile
    inter_schema = {
        'geometry': 'LineString',
        'properties': {'id': 'int'},
    }

    write_shp(inter_schema, MAP_FP + '/inters_segments.shp', union_inter, 1, 0)

    # Output inters_segments properties as json
    with open(DATA_FP + '/inters_data.json', 'w') as f:
        json.dump(inter_segments['data'], f)

    # add non_inter id format = 00+i
    non_int_w_ids = []
    i = 0
    for l in non_int_lines:
        prop = copy.deepcopy(l[1])
        prop['id'] = '00' + str(i)
        non_int_w_ids.append(tuple([l[0], prop]))
        i += 1
    print "extracted {} non-intersection segments".format(len(non_int_w_ids))

    # Non-intersection shapefile
    road_properties = {k: 'str' for k, v in non_int_w_ids[0][1].items()}
    road_schema = {
        'geometry': 'LineString',
        'properties': road_properties
    }
    write_shp(
        road_schema,
        MAP_FP + '/non_inters_segments.shp',
        non_int_w_ids,
        0,
        1
    )

    # Create shapefile that combines intersections and non-intersections while
    # preserving their newly created IDs

    # need to make the schema consistent between the two
    # for now, just keep the ids for the non-intersection segments
    # to keep things simple
    non_int_no_prop = []
    for i in non_int_w_ids:
        id = i[1]['id']

        # reverse the order of the tuple
        # while we're at it to make it
        # consistent with union_inter
        non_int_no_prop.append((
            {'id': id},
            i[0]))

    # concatenate the two datasets
    inter_and_non_int = union_inter + non_int_no_prop

    # create new schema that has only an 'id' property of type string
    all_schema = {
        'geometry': 'LineString',
        'properties': {'id': 'str'},
    }

    # write out shapefile that has intersection and non-intersection segments
    # along with their new IDs
    write_shp(
        all_schema,
        MAP_FP + '/inter_and_non_int.shp', inter_and_non_int, 1, 0)
