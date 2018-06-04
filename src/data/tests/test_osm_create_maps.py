import os
import shutil
from .. import osm_create_maps

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

