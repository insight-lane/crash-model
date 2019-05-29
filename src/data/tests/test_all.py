import os
import subprocess
import json
import shutil


def test_all(tmpdir):

    # Copy test data into temp directory
    orig_path = os.path.dirname(
        os.path.abspath(__file__)) + '/data/'
    path = tmpdir.strpath + '/data'
    shutil.copytree(orig_path, path)
    filename = path + '/raw/ma_cob_spatially_joined_streets.shp'

    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        filename,
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
        path + '/processed/maps/elements.geojson',
        '-c',
        path + '/config_features.yml'
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.join_segments_crash',
        '-d',
        path,
    ])
    data = json.load(open(path + '/processed/crash_joined.json'))
    assert data[0]['near_id'] == 2


