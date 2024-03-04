import data.config
from .. import create_segments
from ..record import Record
from ..segment import Segment, Intersection
import fiona
import os
from .. import util
import shutil
import json
from shapely.geometry import LineString, MultiLineString

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

    roads, inters = util.get_roads_and_inters(os.path.join(
        TEST_FP,
        'data/processed/maps/boston_test_elements.geojson'
    ))

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)
    assert len(non_int_lines) == 7

    # Test that when a segment falls entirely within an intersection buffer
    # it is not included as a non intersection segment
    roads, inters = util.get_roads_and_inters(os.path.join(
        TEST_FP,
        'data/test_create_segments/no_non_inter.geojson'
    ))

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)
    assert len(non_int_lines) == 8
    assert len(inter_segments) == 2

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

    # Now test for the issue where we thought a dead end was an intersection
    # Just make sure that doesn't die
    shutil.copyfile(
        orig_path + 'bad_intersection_test.geojson',
        path + 'osm_elements.geojson'
    )
    create_segments.create_segments_from_json(
        path + 'osm_elements.geojson',
        path
    )

    
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
    non_inter_segment = Segment(None, {
        'osmid': 1,
        'name': 'Main Street',
        'from': '100',
        'to': '200'
    })
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


def _create_point_test(tmpdir):
    base_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'data')
    test_path = os.path.join(
        base_path,
        'test_create_segments'
    )

    with open(os.path.join(test_path, 'points_test.json'), 'r') as f:
        data = json.load(f)

    # All the line strings are roads
    non_inters = [Segment(LineString(
        x['geometry']['coordinates']), x['properties']
    ) for x in data if x['geometry']['type'] == 'LineString']
    # There's only one test intersection
    inter = [x for x in data if x['geometry']['type'] == 'MultiLineString'][0]
    lines = [LineString(x) for x in inter['geometry']['coordinates']]
    inters = [Intersection(
        975,
        lines,
        inter['properties']['data'],
        {'id': inter['properties']['id']}
    )]
    coords = []
    for line in inters[0].lines:
        coords.append(line.coords)
    inters[0].geometry = MultiLineString(
        coords)

    featsfile = os.path.join(test_path, 'points.geojson')
    outputfile = os.path.join(tmpdir.strpath, 'result.json')
    return base_path, non_inters, inters, outputfile, featsfile


def test_update_intersection_properties(tmpdir):
    base_path, non_inters, inters, outputfile, featsfile = _create_point_test(
        tmpdir)
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile)
    config = data.config.Configuration(
        os.path.join(base_path, 'config_features.yml'))
    results = create_segments.update_intersection_properties(
        inters, config)
    print(results[0].properties)
    assert results[0].properties == {
        'id': 975,
        'osm_speed': '25',
        'width': 13,
        'cycleway_type': None,
        'oneway': 1,
        'lanes': 2,
        'signal': 0,
        'crosswalk': 1,
        'jam': None,
        'width_per_lane': 6,
        'jam_percent': None,
        'connected_segments': []
    }
                                             

def test_add_point_based_features(tmpdir):

    base_path, non_inters, inters, outputfile, featsfile = _create_point_test(
        tmpdir)
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile)

    # Check whether the segments we expected got the properties
    assert inters[0].data[0]['crosswalk'] == 1
    signalized = [x for x in non_inters if x.properties['signal']]
    assert len(signalized) == 1
    assert signalized[0].properties['id'] == '001556'

    # Run again (to read from file) and make sure everything looks the same
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile)

    assert inters[0].data[0]['crosswalk'] == 1
    signalized = [x for x in non_inters if x.properties['signal']]
    assert len(signalized) == 1
    assert signalized[0].properties['id'] == '001556'

    # Test writing to the file is as expected
    expected = [{
        "feature": "signal",
        "location": {"latitude": 42.383125, "longitude": -71.138121},
        "near_id": "001556"
    }, {
        "feature": "signal",
        "location": {"latitude": 42.386904, "longitude": -71.116158},
        "near_id": ""
    }, {
        "feature": "crosswalk",
        "location": {"latitude": 42.383447, "longitude": -71.137705},
        "near_id": 975
    }]
    with open(outputfile, 'r') as f:
        output = json.load(f)
        assert output == expected

    # Now test with adding additional_features, and use forceupdate
    additional_feats_file = os.path.join(
        base_path, 'test_create_segments', 'additional_points.json')
    non_inters, inters = create_segments.add_point_based_features(
        non_inters, inters, outputfile, featsfile,
        additional_feats_filename=additional_feats_file, forceupdate=True)
    assert non_inters[4].properties['parking_tickets'] == 2
    assert non_inters[4].properties['traffic_volume'] == 200

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
    }, {
        "feature": "traffic_volume",
        "date": "2014-01-04T15:50:00Z",
        "location": {"latitude": 42.38404209999999, "longitude": -71.1370766},
        "feat_agg": "latest", "value": 100, "near_id": "001557"
    }, {
        "feature": "traffic_volume",
        "date": "2015-01-04T15:50:00Z",
        "location": {"latitude": 42.38404209999999, "longitude": -71.1370766},
        "feat_agg": "latest", "value": 200, "near_id": "001557"
    }]

    with open(outputfile, 'r') as f:
        output = json.load(f)
        assert output == expected


def test_get_connections():
    test_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        'data',
        'test_create_segments')

    test_file = os.path.join(test_path, 'test_get_connections1.geojson')

    roads, inters = util.get_roads_and_inters(test_file)

    # Test the segment on the other side of the median
    # getting dropped from the intersection
    connections = create_segments.get_connections(
        [Record(inters[0]['properties'], point=inters[0]['geometry'])], roads)

    # One intersection is found
    assert len(connections) == 1
    # And it only has three components
    assert len(connections[0][0]) == 3
    ids = [int(x.properties['id']) for x in connections[0][0]]
    ids.sort()
    assert ids == [263, 1167, 1168]

    # Test an intersection with two connected points getting merged
    # into one intersection
    test_file = os.path.join(test_path, 'test_get_connections2.geojson')
    roads, inters = util.get_roads_and_inters(test_file)
    # The initial file should have 7 roads and 2 intersections
    assert len(roads) == 7
    assert len(inters) == 2
    connections = create_segments.get_connections(
        [Record(x['properties'], point=x['geometry']) for x in inters], roads)

    assert len(connections) == 1
    assert len(connections[0][0]) == 7

    # Test that the case with two unconnected intersections works
    test_file = os.path.join(test_path, 'unconnected.geojson')
    roads, inters = util.get_roads_and_inters(test_file)
    connections = create_segments.get_connections(
        [Record(x['properties'], point=x['geometry']) for x in inters], roads)
    assert len(connections) == 2
    assert connections[0][0]
    assert connections[1][0]

    test_file = os.path.join(test_path, 'missing_int_segments.geojson')
    roads, inters = util.get_roads_and_inters(test_file)
    connections = create_segments.get_connections(
        [Record(x['properties'], point=x['geometry']) for x in inters], roads)
    assert len(connections) == 1
    assert len(connections[0][0]) == 7

    # Test an edge case where the point is slightly off from the line
    # This happens at least once in the Boston data, although it should
    # never happen in the openstreetmap data
    test_file = os.path.join(test_path, 'empty_set_inter.geojson')

    roads, inters = util.get_roads_and_inters(test_file)

    # Test the segment on the other side of the median
    # getting dropped from the intersection
    connections = create_segments.get_connections(
        [Record(inters[0]['properties'], point=inters[0]['geometry'])], roads)
    assert connections[0][0]
    

def test_connected_segments():
    """
    Test of the connected components for intersections and non intersections
    """

    roads, inters = util.get_roads_and_inters(os.path.join(
        TEST_FP,
        'data/test_create_segments/test_adjacency.geojson'
    ))

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)

    # This tests a bugfix where lines that almost but not quite intersect
    # are correctly left out of set of intersection lines
    assert len(inter_segments[1].lines) == 3

    # Test connected segments
    # TODO: this matches the assertion set, but previously was idx 0, not 2
    assert set(inter_segments[2].connected_segments) == set([
        '0011', '007', '005', '000'])
    assert set(non_int_lines[8].properties['connected_segments']) == set([
        3, 4])


def test_multilinestring():
    """
    Test that MultiLineStrings get converted into LineStrings
    """
    roads, inters = util.get_roads_and_inters(os.path.join(
        TEST_FP,
        'data/test_create_segments/test_linestring.geojson'
    ))

    for i, road in enumerate(roads):
        road.properties['orig_id'] = int(str(99) + str(i))

    int_buffers = create_segments.get_intersection_buffers(inters, 20)
    non_int_lines, inter_segments = create_segments.find_non_ints(
        roads, int_buffers)
    assert all([x.geometry.type == 'LineString' for x in non_int_lines])

def test_get_connections_empty():
    """
    Test issue with empty polygons in get connections function
    """
    import pickle
    points = pickle.load(open(os.path.join(TEST_FP, 'data/int_buffer_empty.pkl'), 'rb'))
    segments = pickle.load(open(os.path.join(TEST_FP, 'data/match_segments_empty.pkl'), 'rb'))
    int_segments = create_segments.get_connections(points, segments)

    # assert no empty polygons
    all([~x[1].is_empty for x in int_segments])

