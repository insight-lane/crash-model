import os
import subprocess
import shutil


def test_add_map(tmpdir):

    # Copy test data into temp directory in appropriate place
    base_path = os.path.dirname(
        os.path.abspath(__file__)) + '/data/'
    orig_path = base_path + 'test_add_map'
    path = tmpdir.strpath + '/data'

    data_path = os.path.join(path, "processed/maps")
    shutil.copytree(orig_path, data_path)

    # To test the mapping, use much smaller versions of the osm
    # and osm3857 files, as well as much smaller versions of boston data

    # Then as in the standard workflow, extract_intersections
    # and create_segments need to be run (in the test directory)
    # and then the mapping can be run and tested

    # Extract and create on osm data
    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        os.path.join(data_path, 'osm3857.shp'),
        '-d',
        path
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        path,
        '-r',
        os.path.join(data_path, 'elements.geojson'),
        '-c',
        os.path.join(base_path, 'config_features.yml')
    ])

    # Extract and create on supplemental map
    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        os.path.join(data_path, 'ma_cob_small.shp'),
        '-d',
        path,
        '-n',
        'boston'
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
        '-d',
        path,
        '-r',
        os.path.join(data_path, 'boston/elements.geojson'),
        '-n',
        'boston',
        '-c',
        os.path.join(base_path, 'config_features.yml')

    ])

    # Above was all set up, now the testing part
    # and add features
    subprocess.check_call([
        'python',
        '-m',
        'data.add_map',
        path,
        'boston',
    ])
