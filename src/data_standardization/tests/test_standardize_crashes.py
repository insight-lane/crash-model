from .. import standardize_crashes
from jsonschema import validate
import json
import os
import csv

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def create_test_csv(tmpdir, filename):
    tmppath = tmpdir.strpath

    test = [{
        'key1': 'value1',
        'key2': 'value2'
    }, {
        'key1': 'another value',
        'key2': 5
    }]
    with open(os.path.join(tmppath, filename), 'w') as f:
        writer = csv.DictWriter(f, list(test[0].keys()))
        writer.writeheader()
        for row in test:
            writer.writerow(row)
    return tmppath


def test_add_id(tmpdir):
    """
    Create a dummy csv file without ID fields, add IDs to it
    """
    tmppath = create_test_csv(tmpdir, 'test.csv')
    filename = os.path.join(tmppath, 'test.csv')
    standardize_crashes.add_id(filename, 'ID')

    expected = [{
        'ID': '1',
        'key1': 'value1',
        'key2': 'value2'
    }, {
        'ID': '2',
        'key1': 'another value',
        'key2': '5'
    }]

    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for i, row in enumerate(csv_reader):
            assert row == expected[i]

    # Test calling it again and make sure it doesn't change
    standardize_crashes.add_id(filename, 'ID')
    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for i, row in enumerate(csv_reader):
            assert row == expected[i]


def test_numeric_and_string_ids():
    """
    Confirm that crashes with both numeric and string ids pass validation
    """
    test_crashes = [{
        "id": 12345,
        "dateOccurred": "2016-01-01T02:30:23-05:00",
        "location": {
            "latitude": 42.317987926802246,
            "longitude": -71.06188127008645
        }
    },
    {
        "id": "A1B2C3D4E5",
        "dateOccurred": "2016-01-01T02:30:23-05:00",
        "location": {
            "latitude": 42.317987926802246,
            "longitude": -71.06188127008645
        }
    }
    ]

    validate(test_crashes, json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "standards", "crashes-schema.json"))))
