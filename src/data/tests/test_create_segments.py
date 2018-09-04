from .. import create_segments
import fiona
import os
from .. import util
import shutil
import json

TEST_FP = os.path.dirname(os.path.abspath(__file__))


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
    print(path)
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


def test_add_point_based_features(tmpdir):

    test_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'data',
        'test_create_segments')
    test_file = os.path.join(test_path, 'points_test.json')

    # The points test file contains non_inters and one inter,
    # in the same format as add_point_based_features requires
    with open(test_file, 'r') as f:
        non_inters = json.load(f)
    inters = [non_inters.pop()]

    featsfile = os.path.join(test_path, 'points.geojson')
    outputfile = os.path.join(tmpdir.strpath, 'result.json')
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile)

    # Check whether the segments we expected got the properties
    assert inters[0]['properties']['data'][0]['crosswalk'] == 1
    signalized = [x for x in non_inters if x['properties']['signal']]
    assert len(signalized) == 1
    assert signalized[0]['properties']['id'] == '001556'

    # Run again (to read from file) and make sure everything looks the same
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile)

    assert inters[0]['properties']['data'][0]['crosswalk'] == 1
    signalized = [x for x in non_inters if x['properties']['signal']]
    assert len(signalized) == 1
    assert signalized[0]['properties']['id'] == '001556'

    # Test writing to the file is as expected
    expected = [{
        "feature": "signal",
        "location": {"latitude": 42.383125, "longitude": -71.138121},
        "near_id": "001556"
    }, {
        "feature": "signal",
        "location": {"latitude": 42.386904, "longitude": -71.1161581},
        "near_id": ""
    }, {
        "feature": "crosswalk",
        "location": {"latitude": 42.3834466, "longitude": -71.1377047},
        "near_id": 975
    }]
    with open(outputfile, 'r') as f:
        output = json.load(f)
        assert output == expected

    # Now test with adding additional_features, and use forceupdate
    additional_feats_file = os.path.join(test_path, 'additional_points.json')
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile,
        additional_feats_filename=additional_feats_file, forceupdate=True)
    assert non_inters[4]['properties']['parking_tickets'] == 2
    
    expected = expected + [{
        "feature": "parking_tickets",
        "date": "2016-05-17T00:00:00Z",
        "location": {"latitude": 42.38404209999999, "longitude": -71.1370766},
        "category": "NO PARKING",
        "near_id": "001557"
    }, {
        "feature": "parking_tickets",
        "date": "2014-01-04T15:50:00Z",
        "location": {"latitude": 42.38404209999999, "longitude": -71.1370766},
        "category": "METER EXPIRED", "near_id": "001557"
    }]

    with open(outputfile, 'r') as f:
        output = json.load(f)
        assert output == expected
