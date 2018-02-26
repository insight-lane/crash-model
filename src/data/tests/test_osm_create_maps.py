import os
import shutil
from .. import osm_create_maps

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_reproject_and_clean_feats(tmpdir):

    tmppath = tmpdir.strpath
    exts = ['shp', 'shx', 'dbf', 'cpg']
    for ext in exts:
        shutil.copy(
            TEST_FP + '/data/processed/maps/osm.' + ext,
            tmppath
        )

    # For now, just make sure it runs
    osm_create_maps.reproject_and_clean_feats(
        tmppath + '/osm.shp',
        tmppath + '/osm3857.shp',
        tmppath + '/docs'
    )

