from .. import create_segments
import fiona
import os
import geojson
from .. import util
import shutil

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
    Use small test version of inters.shp to test
    """

    inters = fiona.open(
        TEST_FP + '/data/processed/maps/inters.geojson')
    inters = util.reproject_records([x for x in inters])

    assert len(inters) == 6

    # Two test intersections overlap with the regular buffer
    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    assert len(int_buffers) == 5

    # No intersections overlap with a small buffer
    int_buffers = create_segments.get_intersection_buffers(inters, 5)
    assert len(int_buffers) == 6


def test_find_non_ints():

    roads = fiona.open(TEST_FP +
                       '/data/processed/maps/boston_test_elements.geojson')

    roads = util.reproject_records([x for x in roads])

    inters = fiona.open(TEST_FP + '/data/processed/maps/inters.geojson')
    inters = util.reproject_records([x for x in inters])

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)
    assert len(non_int_lines) == 7


def test_create_segments_from_json(tmpdir):
    """
    Just test that this runs, for now
    """
    # Copy test data into temp directory
    orig_path = os.path.dirname(
        os.path.abspath(__file__)) + '/data/'
    path = tmpdir.strpath + '/data/processed/maps/'
    os.makedirs(path)
    shutil.copyfile(
        orig_path + 'missing_segments_test.geojson',
        path + 'osm_elements.geojson'
    )
    non_inters, inters = create_segments.create_segments_from_json(
        path + 'osm_elements.geojson',
        path
    )
    create_segments.write_segments(
        non_inters, inters, path, tmpdir.strpath + '/data/')


def test_get_intersection_name():
    inter_segments = [{
        'id': 1,
        'name': 'Test Street',
    }, {
        'id': 2,
        'name': 'Test Street',
    }, {
        'id': 3,
        'name': '[Another Street, One More Road]',
    }]
    name = create_segments.get_intersection_name(inter_segments)
    assert name == 'Another Street near One More Road and Test Street'


def test_get_non_intersection_name():
    non_inter_segment = {'properties': {
        'osmid': 1,
        'name': 'Main Street',
        'from': '100',
        'to': '200'
    }}
    inters_by_id = {
    }
    name = create_segments.get_non_intersection_name(
        non_inter_segment, inters_by_id)
    assert name == 'Main Street'

    inters_by_id['100'] = 'From Street'
    name = create_segments.get_non_intersection_name(
        non_inter_segment, inters_by_id)
    assert name == 'Main Street from From Street'

    inters_by_id['100'] = None
    inters_by_id['200'] = 'To Street, Another Street'
    name = create_segments.get_non_intersection_name(
        non_inter_segment, inters_by_id)
    assert name == 'Main Street from To Street/Another Street'

    inters_by_id['100'] = 'From Street'
    name = create_segments.get_non_intersection_name(
        non_inter_segment, inters_by_id)
    assert name == 'Main Street between From Street and To Street/Another Street'

    
