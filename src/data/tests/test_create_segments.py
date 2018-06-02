from .. import create_segments
import fiona
from shapely.geometry import shape
import os
import geojson
from .. import util

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def make_shape_file(tmpdir):
    tmppath = tmpdir.strpath

    with open(tmppath, 'w') as outfile:
        geojson.dump(geojson.FeatureCollection(
            geojson.Feature(
                geometry=geojson.Point(-71.08724754844711, 42.352043744961),
                properties={'id_1': 1, 'id_2': 2})), outfile)


def test_get_intersection_buffers():
    """
    Use small test version of inters_3857.shp to test
    """

    inters = fiona.open(
        TEST_FP + '/data/processed/maps/inters_3857.geojson')
    inters = util.reproject_records([x for x in inters])

    assert len(inters) == 6

    # Two test intersections overlap with the regular buffer
    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    assert len(int_buffers) == 5

    # No intersections overlap with a small buffer
    int_buffers = create_segments.get_intersection_buffers(inters, 5)
    assert len(int_buffers) == 6


def test_find_non_ints():
    roads_shp_path = TEST_FP + \
        '/data/processed/maps/ma_cob_spatially_joined_streets.shp'
    roads = [(shape(road['geometry']), road['properties'])
             for road in fiona.open(roads_shp_path)]
    inters = [
        (shape(inter['geometry']), inter['properties'])
        for inter in fiona.open(
            TEST_FP + '/data/processed/maps/inters_3857.shp'
        )]

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)
    assert len(non_int_lines) == 7


