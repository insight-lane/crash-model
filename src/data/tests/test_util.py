from .. import util
import os
from shapely.geometry import Point
import pyproj

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_read_shp():
    res = util.read_shp(TEST_FP + '/data/inters.shp')
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
    x = float(42.30)
    y = float(-71.07)
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
        float(4708814.460555471), float(-11426249.391937567))
    assert result == expected
