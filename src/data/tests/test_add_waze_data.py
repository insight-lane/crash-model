import os
import shutil
import geojson
from .. import add_waze_data

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_make_map(tmpdir):
    add_waze_data.make_map(
        os.path.join(TEST_FP, 'data', 'test_waze', 'test_waze.json'),
        tmpdir.strpath
    )


def test_map_segments(tmpdir):

    # Copy test data into temp directory
    orig_path = os.path.join(TEST_FP, 'data', 'test_waze')
    path = os.path.join(tmpdir.strpath, 'processed', 'maps')

    os.makedirs(path)
    shutil.copyfile(
        os.path.join(orig_path, 'osm_elements.geojson'),
        os.path.join(path, 'osm_elements.geojson')
    )
    
    add_waze_data.map_segments(
        tmpdir.strpath,
        os.path.join(orig_path, 'waze_test_set.json')
    )

    # Read back in the jams information
    with open(os.path.join(path, 'jams.geojson')) as f:
        items = geojson.load(f)
    # Test that the number of jams is consistent
    assert len(items['features']) == 54
