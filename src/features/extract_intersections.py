import fiona
import sys
import math
from shapely.geometry import Point, shape, mapping
import itertools
import cPickle
import os

MAP_DATA_FP = '../data/processed/maps/'


def track(index, step, tot):
    """
    Prints progress at interval
    """
    if index % step == 0:
        print "finished {} of {}".format(index, tot)


def extract_intersections(inter, prop):
    """
    Extracts road intersections, returning coordinates + properties

    Args:
        inter: the intersection of two segments
        prop: ??

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
        for i in [Point(first_coords[0], first_coords[1]),Point(last_coords[0], last_coords[1])]:
            yield(i, prop)
    # If collection points/lines (rare), just re-run on each part
    elif "GeometryCollection" == inter.type:
        for geom in inter:
            for i in extract_intersections(geom, prop):
                yield i


def generate_intersections(lines):
    """
    Runs extract_intersections on all combinations of points

    Args:
        lines: the lines from the shapefile

    Returns:
        inters: intersections
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

    # Save to pickle in case script breaks
    with open(MAP_DATA_FP + 'inters.pkl', 'w') as f:
        cPickle.dump(inters, f)
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

    points = {}
    # remove duplicate points
    for pt, prop in inters:
        if (pt.x, pt.y) not in points.keys():
            points[(pt.x, pt.y)] = pt, prop

    with fiona.open('../data/processed/maps/inters.shp', 'w', 'ESRI Shapefile', schema) as output:
        for i, (pt, prop) in enumerate(points.values()):
            track(i, 500, len(points))
            output.write({'geometry': mapping(pt), 'properties': prop})


if __name__ == '__main__':

    # Import shapefile specified at commandline
    shp = sys.argv[1]

    # Get all lines, dummy id
    lines = [
        (
            line[0],
            shape(line[1]['geometry'])
        ) for line in enumerate(fiona.open(shp))
    ]

    inters = []
    if not os.path.exists(MAP_DATA_FP + 'inters.pkl'):
        inters = generate_intersections(lines)
    else:
        with open(MAP_DATA_FP + 'inters.pkl', 'r') as f:
            inters = cPickle.load(f)
    write_intersections(inters)
