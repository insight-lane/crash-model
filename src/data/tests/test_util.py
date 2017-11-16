from .. import util
import os
from shapely.geometry import Point

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
