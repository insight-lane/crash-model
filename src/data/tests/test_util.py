from .. import util
import os
from shapely.geometry import Point
import pyproj
import csv

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_read_shp():
    res = util.read_shp(TEST_FP + '/data/processed/maps/inters.shp')
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


def test_csv_to_projected_records(tmpdir):
    x = float(-71.07)
    y = float(42.3)
    print tmpdir
    file = str(tmpdir) + '/test.csv'
    with open(file, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['col1', 'col2', 'col3'])
        writer.writerow(['test', x, y])
    results = util.csv_to_projected_records(file,
                                            'col2', 'col3')
    expected_props = {
        'col1': 'test',
        'col2': '-71.07',
        'col3': '42.3'
    }
    expected_point = Point(float(-7911476.210677952), float(5206024.46129235))

    assert results[0]['point'] == expected_point
    assert results[0]['properties'] == expected_props


def find_nearest():
    pass


def test_read_segments():
    pass
