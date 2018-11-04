import fiona
import math
from shapely.geometry import Point, shape
import itertools
import pickle
import os
import argparse
from .util import track, prepare_geojson
import geojson

MAP_DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/data/processed/maps/'


def extract_intersections(inter, prop):
    """
    Extracts road intersections, returning coordinates + properties

    Args:
        inter: the intersection of two segments
        prop: a dict where the keys are id_1 and id_2, and the values
            are the segment ids

    Returns:
        Generator
    """

    # A single intersection
    if "Point" == inter.type:
        yield inter, prop
    # If multiple intersections, return each point
    elif "MultiPoint" == inter.type:
        for i in inter:
            yield(i, prop)
    # If line with overlap, find start/end, return
    elif "MultiLineString" == inter.type:
        multiLine = [line for line in inter]
        first_coords = multiLine[0].coords[0]
        last_coords = multiLine[-1].coords[1]
        for i in [
                Point(first_coords[0], first_coords[1]),
                Point(last_coords[0], last_coords[1])]:
            yield(i, prop)
    # If collection points/lines (rare), just re-run on each part
    elif "GeometryCollection" == inter.type:
        for geom in inter:
            for i in extract_intersections(geom, prop):
                yield i


def generate_intersections(lines):
    """
    Runs extract_intersections on all combinations of lines
    Writes the resulting intersections to file as well as returning

    Args:
        lines: the lines from the shapefile

    Returns:
        inters: intersections - a list of point, dict tuples
            the dict contains the newly created ids of the
            intersecting segments
    """
    inters = []
    i = 0

    # Total combinations of two road segments
    def nCr(n, r):
        f = math.factorial
        return f(n) // f(r) // f(n-r)
    tot = nCr(len(lines), 2)
    # Look at all pairs of segments to extract intersections
    for segment1, segment2 in itertools.combinations(lines, 2):
        track(i, 10000, tot)
        if segment1[1].intersects(segment2[1]):
            inter = segment1[1].intersection(segment2[1])
            inters.extend(extract_intersections(
                inter,
                {'id_1': segment1[0], 'id_2': segment2[0]}
            ))
        i += 1

    return inters


def write_intersections(inters, roads):
    """
    Given a list of shapely intersections,
    de-dupe and write shape files

    Args:
        inters: list of points indicating intersections
    """
    output_inters = []

    # De-dupe and add intersection as a property
    seen_points = {}
    for x in inters:
        properties = x[1]

        if str(x[0].x) + str(x[0].y) not in list(seen_points.keys()):
            properties.update({'intersection': 1})
            output_inters.append(geojson.Feature(
                geometry=geojson.Point([x[0].x, x[0].y]),
                properties=properties
            ))
        seen_points[str(x[0].x) + str(x[0].y)] = True

    output_inters = prepare_geojson(output_inters)

    roads_with_ids = []
    # Add ids to the non_intersection segments to use in generating the intersections
    # in the create_segments script
    for road in roads:
        road['properties']['id'] = road['id']
        roads_with_ids.append(road)
    roads = prepare_geojson(roads_with_ids)

    elements = geojson.FeatureCollection(
        output_inters['features'] + roads['features'])

    outfp = os.path.join(MAP_DATA_FP, 'elements.geojson')
    with open(outfp, 'w') as outfile:
        geojson.dump(elements, outfile)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("shp", help="Segments shape file")
    parser.add_argument("-d", "--dir", type=str,
                        help="Can give alternate data directory")

    parser.add_argument("-n", "--newmap", type=str,
                        help="If given, write output to new directory" +
                        "within the maps directory")

    # Can force update
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()

    # Import shapefile specified at commandline
    shp = args.shp

    # Can override the hardcoded maps directory
    if args.dir:
        MAP_DATA_FP = os.path.join(args.dir, 'processed/maps')
    if args.newmap:
        MAP_DATA_FP = os.path.join(MAP_DATA_FP, args.newmap)
        if not os.path.exists(MAP_DATA_FP):
            os.mkdir(MAP_DATA_FP)

    roads = fiona.open(shp)
    # Get all lines, dummy id
    lines = [
        (
            i,
            shape(line['geometry'])
        ) for i, line in enumerate(roads)
    ]

    print('Extracting intersections and writing into ' + MAP_DATA_FP)
    inters = []
    pkl_file = os.path.join(MAP_DATA_FP, 'inters.pkl')

    if not os.path.exists(pkl_file) or args.forceupdate:
        print('Generating intersections...')
        inters = generate_intersections(lines)

        # Save to pickle in case script breaks
        with open(pkl_file, 'wb') as f:
            pickle.dump(inters, f)
    else:
        print('Reading intersections from ' + pkl_file)
        with open(pkl_file, 'rb') as f:
            inters = pickle.load(f)

    print("writing intersections and road segments to geojson")
    write_intersections(inters, roads)
