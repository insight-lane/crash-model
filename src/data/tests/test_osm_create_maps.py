import os
import shutil
from shapely.geometry import Polygon
from .. import osm_create_maps
from .. import util

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_reproject_and_clean_feats(tmpdir):

    tmppath = tmpdir.strpath
    shutil.copy(
        TEST_FP + '/data/processed/maps/osm_elements.geojson',
        tmppath
    )

    # For now, just make sure it runs
    osm_create_maps.clean_ways(
        tmppath + '/osm_elements.geojson',
        tmppath + '/docs'
    )


def test_expand_polygon():

    test_polygon = {
        'type': 'Polygon',
        'coordinates': [[[-71.0770265, 42.3364517], [-71.0810509, 42.3328703],
                         [-71.0721386, 42.3325241]]]
    }
    # Too many points fall outside of the polygon to buffer
    result = osm_create_maps.expand_polygon(test_polygon, os.path.join(
        TEST_FP, 'data', 'osm_crash_file.json'))
    assert result is None

    polygon_coords = [util.get_reproject_point(
        x[1], x[0], coords=True) for x in test_polygon['coordinates'][0]]
    poly_shape = Polygon(polygon_coords)

    result = osm_create_maps.expand_polygon(test_polygon, os.path.join(
        TEST_FP, 'data', 'osm_crash_file.json'), max_percent=.7)

    # Check whether the new polygon has a larger area than the old one
    assert Polygon(test_polygon['coordinates'][0]).area < poly_shape.area

