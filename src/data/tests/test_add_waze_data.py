import os
import shutil
import geojson
from .. import add_waze_data

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_make_map(tmpdir):

    original_filename = os.path.join(
            TEST_FP, 'data', 'test_waze', 'test_waze.json')
    with open(original_filename) as f:
        original = geojson.load(f)

    add_waze_data.make_map(original_filename, tmpdir.strpath)

    # Read back in the resulting map
    with open(os.path.join(tmpdir.strpath, 'waze.geojson')) as f:
        items = geojson.load(f)

    # The number of lines in the original json file should
    # equal the number of linestrings in the resulting geojson map
    assert len(original) == len(items['features'])


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
        os.path.join(orig_path, 'test_waze.json')
    )

    # Read back in the jams information
    with open(os.path.join(path, 'jams.geojson')) as f:
        items = geojson.load(f)
    # Test that the number of jam segments is consistent
    # This is not the number of jams total, since jams can
    # encompass more than one segment from osm_elements
    assert len(items['features']) == 22
    
    # Read back in the osm_elements, make sure number of elements
    # with a jam percentage matches the number of jam segments
    with open(os.path.join(path, 'osm_elements.geojson')) as f:
        osm_items = geojson.load(f)
    assert len([x for x in osm_items['features']
                if x['geometry']['type'] == 'LineString'
                and x['properties']['jam_percent'] > 0]) == 22

    # Test that the points in the file still exist
    # after modifying the linestrings
    assert len(osm_items['features']) == 90
