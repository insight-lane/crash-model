from .. import util
import os
from shapely.geometry import Point
import pyproj
import fiona
import geojson
import numpy as np


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_read_geojson():
    res = util.read_geojson(TEST_FP + '/data/processed/maps/inters.geojson')
    assert len(res) == 6
    assert type(res[0][0]) == Point


def test_write_shp(tmpdir):
    """
    Just make sure this runs
    """

    tmppath = tmpdir.strpath
    schema = {
        'geometry': 'Point',
        'properties': {
            'STATUS': 'str',
            'X': 'str',
            'Y': 'str'
        }
    }
    data = (
        {
            'point': Point(0, 0),
            'properties': {'X': 1, 'Y': 'a'}
        },
        {
            'point': Point(1, 1),
            'properties': {'X': 2, 'Y': 'b', 'STATUS': 'c'}
        }
    )
    util.write_shp(schema, tmppath + '/test', data, 'point', 'properties')


def test_read_record():
    x = float(-71.07)
    y = float(42.30)
    # Test with no projections given
    record = {'a': 1, 'b': 'x'}

    # Don't project if you don't pass in projections
    result = util.read_record(record, x, y)
    expected = {
        'point': Point(float(x), float(y)),
        'properties': record
    }

    assert result == expected

    orig = pyproj.Proj(init='epsg:4326')
    result = util.read_record(record, x, y, orig)

    # Test projecting
    expected['point'] = Point(
        float(-7911476.210677952), float(5206024.46129235))
    assert result == expected


def find_nearest():
    # todo
    pass


def test_read_segments():
    # todo
    pass


def test_reproject_records():
    start_lines = fiona.open(
        TEST_FP + '/data/processed/maps/test_line_convert.shp')
    result = util.reproject_records(start_lines)

    # Test makes sure that both the LineStrings and MultiLineStrings
    # successfully get reprojected
    assert len(start_lines) == len(result)


def test_group_json_by_location(tmpdir):

    test_json = [{
        'near_id': '001',
        'key1': 'value1',
        'key2': 'value2',
    }, {
        'near_id': '2',
        'key1': 'test',
    }, {
        'near_id': '001',
        'key1': 'testtest',
        'key2': 'abc',
    }]

    result = util.group_json_by_location(test_json)
    assert result == ([
        {'near_id': '001', 'key1': 'value1', 'key2': 'value2'},
        {'near_id': '2', 'key1': 'test'},
        {'near_id': '001', 'key1': 'testtest', 'key2': 'abc'}
    ], {
        '001': {'count': 2}, '2': {'count': 1}
    })

    result = util.group_json_by_location(test_json, otherfields=['key1'])
    assert result == ([
        {'near_id': '001', 'key1': 'value1', 'key2': 'value2'},
        {'near_id': '2', 'key1': 'test'},
        {'near_id': '001', 'key1': 'testtest', 'key2': 'abc'}
    ], {
        '001': {
            'count': 2, 'key1': ['value1', 'testtest']
        }, '2': {
            'count': 1, 'key1': ['test']}
    })


def test_make_schema():
    test_schema = {'X': 1, 'NAME': 'foo'}
    result_schema = util.make_schema(
        'Point', test_schema)
    assert result_schema == {'geometry': 'Point', 'properties':
                             {'X': 'str', 'NAME': 'str'}}


def test_prepare_geojson():
    records = [{
        'geometry': {
            "coordinates": [
                [
                    [-7914260.749231104, 5206877.878672692],
                    [-7914262.982810471, 5206897.741836411]
                ],
                [
                    [-7914262.982810471, 5206897.741836411],
                    [-7914247.3920878805, 5206885.229947844]
                ],
                [
                    [-7914267.358916062, 5206917.238736267],
                    [-7914266.99031214, 5206914.148600942],
                    [-7914262.982810471, 5206897.741836411]
                ]
            ],
            "type": "MultiLineString"
        },
        'properties': {'id': 2}
    }]
    results = util.prepare_geojson(records)
    actual_coords = results['features'][0]['geometry']['coordinates']
    actual_properties = results['features'][0]['properties']
    assert actual_properties == {"id": 2}

    expected = {
        "features": [{
            "geometry": {
                "coordinates": [
                    [
                        [-71.09501393541515, 42.30567003680977],
                        [-71.095034, 42.30580199999999]
                    ],
                    [
                        [-71.095034, 42.30580199999999],
                        [-71.09489394615605, 42.30571887587566]
                    ],
                    [
                        [-71.09507331122536, 42.30593152960553],
                        [-71.09507, 42.30591099999999],
                        [-71.095034, 42.30580199999999]
                    ]
                ],
                "type": "MultiLineString"
            },
            "id": 2,
            "properties": {"id": 2},
            "type": "Feature"
        }],
        "type": "FeatureCollection"
    }

    expected_coords = [
        [
            [-71.09501393541515, 42.30567003680977],
            [-71.095034, 42.30580199999999]
        ],
        [
            [-71.095034, 42.30580199999999],
            [-71.09489394615605, 42.30571887587566]
        ],
        [
            [-71.09507331122536, 42.30593152960553],
            [-71.09507, 42.30591099999999],
            [-71.095034, 42.30580199999999]
        ]
    ]

    # assert almost equals in case of small precision differences
    for i in range(len(actual_coords)):
        for j in range(len(actual_coords[i])):
            np.testing.assert_almost_equal(
                actual_coords[i][j], expected_coords[i][j])


def test_get_center_point():
    assert util.get_center_point(
        geojson.Feature(
            geometry=geojson.LineString([[1, 0], [3, 0]]))) == (2.0, 0.0)

    assert util.get_center_point(geojson.Feature(
        geometry=geojson.MultiLineString(
            [[[2, 0], [2, 4]], [[0, 2], [4, 2]]]))) == (2.0, 2.0)
    assert util.get_center_point(
        geojson.Feature(geometry=geojson.Point([0, 0]))) == (None, None)


def test_get_roads_and_inters():

    path = os.path.join(
        TEST_FP, 'data',
        'test_get_roads_and_inters.geojson')
    print(path)
    roads, inters = util.get_roads_and_inters(path)
    assert len(roads) == 4
    assert len(inters) == 1


def test_output_from_shapes(tmpdir):
    tmppath = tmpdir.strpath

    path = os.path.join(tmppath, 'test_output.geojson')
    records = [
        {
            'geometry': {
                'coordinates': (-71.112940, 42.370110),
                'type': 'Point'
            },
            'properties': {}
        },
        {
            'geometry': {
                'coordinates': (-71.112010, 42.371440),
                'type': 'Point'
            },
            'properties': {}
        }
    ]
    
    records = util.reproject_records(records)
    polys = [
        (records[0]['geometry'].buffer(3), {}),
        (records[1]['geometry'].buffer(3), {})
    ]

    util.output_from_shapes(polys, path)
    # Read in the output, and just validate a couple of coordinates
    with open(path) as f:
        items = geojson.load(f)

        assert items['features'][0]['geometry']['type'] == 'Polygon'
        np.testing.assert_almost_equal(
            items['features'][0]['geometry']['coordinates'][0][0],
            [-71.11291305054148, 42.370109999999976])

        assert items['features'][1]['geometry']['type'] == 'Polygon'
        np.testing.assert_almost_equal(
            items['features'][1]['geometry']['coordinates'][0][0],
            [-71.11198305054148, 42.37143999999999])


def test_get_feature_list():

    config = {
        'openstreetmap_features': {
            'categorical': {
                'width': 'Width',
                'cycleway_type': 'Bike lane',
                'signal': 'Signal',
                'oneway': 'One Way',
                'lanes': 'Number of lanes'
            },
            'continuous': {
                'width_per_lane': 'Average width per lane'
            }
        },
    }
    results = util.get_feature_list(config)

    assert results == {
        'f_cat': ['width', 'cycleway_type', 'signal', 'oneway', 'lanes'],
        'f_cont': [
            'width_per_lane'
        ]
    }

    config['waze_features'] = {
        'categorical': {'jam': 'Existence of a jam'},
        'continuous': {'jam_percent': 'Percent of time there was a jam'}
    }
    results = util.get_feature_list(config)
    assert results == {
        'f_cat': [
            'width', 'cycleway_type', 'signal', 'oneway', 'lanes', 'jam'],
        'f_cont': [
            'width_per_lane', 'jam_percent']
    }
    
    additional_features = {
        'extra_map': 'test',
        'continuous': {'AADT': 'test name'},
        'categorical': {
            'SPEEDLIMIT': 'test name2',
            'Struct_Cnd': 'test name3',
            'Surface_Tp': 'test name4',
            'F_F_Class': 'test name5'
            }
    }

    results = util.get_feature_list({
        'additional_map_features': additional_features})
    assert results == {
        'f_cat': [
            'SPEEDLIMIT',
            'Struct_Cnd',
            'Surface_Tp',
            'F_F_Class'
        ],
        'f_cont': [
            'AADT'
        ]
    }
