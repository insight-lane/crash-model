
from .. import make_map_subset
from data.util import get_reproject_point, reproject_records
import os


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_buffer():
    results = make_map_subset.get_buffer(
        os.path.join(TEST_FP, 'data', 'test_make_map.geojson'),
        42.3693239,
        -71.10103649999999,
        20
    )
    assert len(results['features']) == 5
    lines = [x for x in results['features']
             if x['geometry']['type'] == 'LineString']
    assert len(lines) == 4
    point = [x for x in results['features']
             if x['geometry']['type'] == 'Point']
    assert len(point) == 1

    # Make sure that all the resulting features are at least partially
    # within the buffer
    center_point = get_reproject_point(42.3693239, -71.10103649999999)
    buff_poly = center_point.buffer(20)

    # To do this, have to convert the points and linestrings back to 3857
    reprojected_lines = reproject_records(lines)
    for r in reprojected_lines:
        assert r['geometry'].intersects(buff_poly)

    point_3857 = get_reproject_point(
        point[0]['geometry']['coordinates'][1],
        point[0]['geometry']['coordinates'][0])
    assert point_3857.within(buff_poly)

    results = make_map_subset.get_buffer(
        os.path.join(TEST_FP, 'data', 'test_make_map.geojson'),
        42.3601,
        71.0589,
        20
    )
    assert results == []
