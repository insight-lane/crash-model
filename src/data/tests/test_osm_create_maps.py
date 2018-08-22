import os
import shutil
from .. import osm_create_maps

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_width():
    assert osm_create_maps.get_width('15.2') == 15
    assert osm_create_maps.get_width('') == 0
    assert osm_create_maps.get_width("['14.9', '12.2']") == 0
    assert osm_create_maps.get_width('t') == 0


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

