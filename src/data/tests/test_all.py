import os
import subprocess
import json


def test_all():

    path = os.path.dirname(
        os.path.abspath(__file__)) + '/data/'
    filename = path + '/raw/Boston_Segments.shp'

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
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.join_segments_crash_concern',
        '-d',
        'data/tests/data/',
        '-c',
        'crashes.csv'
    ])
    data = json.load(open(path + '/processed/crash_joined.json'))
    assert data[0]['near_id'] == 2

    data = json.load(open(path + '/processed/concern_joined.json'))
    assert data[0]['near_id'] == 3


