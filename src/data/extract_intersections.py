import fiona
import math
from shapely.geometry import Point, shape
import itertools
import cPickle
import os
import argparse
from util import track, write_points

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
    Runs extract_intersections on all combinations of points
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
        return f(n) / f(r) / f(n-r)
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


def write_intersections(inters):
    """
    Given a list of shapely intersections,
    de-dupe and write shape files

    Args:
        inters: list of points indicating intersections
    """
    # schema of the shapefile
    schema = {
        'geometry': 'Point',
        'properties': {
            'id_1': 'int',
            'id_2': 'int'
        }
    }
    write_points(inters, schema, os.path.join(MAP_DATA_FP, 'inters.shp'))


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

    # Get all lines, dummy id
    lines = [
        (
            line[0],
            shape(line[1]['geometry'])
        ) for line in enumerate(fiona.open(shp))
    ]

    print 'Extracting intersections and writing into ' + MAP_DATA_FP
    inters = []
    pkl_file = os.path.join(MAP_DATA_FP, 'inters.pkl')
    if not os.path.exists(pkl_file) or args.forceupdate:
        print 'Generating intersections...'
        inters = generate_intersections(lines)
        # Save to pickle in case script breaks
        with open(pkl_file, 'w') as f:
            cPickle.dump(inters, f)
    else:
        print 'Reading intersections from ' + pkl_file
        with open(pkl_file, 'r') as f:
            inters = cPickle.load(f)
    write_intersections(inters)
