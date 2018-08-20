import os
import csv
import json
from .. import standardize_point_data


def create_test_csv(tmpdir, filename):
    tmppath = tmpdir.strpath
    
    test = [{
        'Ticket Issue Date': '09/02/2014',
        'Issue Time': '9:10 AM',
        'Location': "1100 CAMBRIDGE ST\nCambridge, MA\n" +
            "(42.37304187600046, -71.09569369699966)",
        'Violation Description': 'METER EXPIRED',
    }, {
        'Ticket Issue Date': '01/09/2014',
        'Issue Time': '9:33 AM',
        'Location': "CAMBRIDGE ST / OAKLAND ST\n" +
            "Cambridge, MA\n(42.374105433000466, -71.12219272199962)",
        'Violation Description': 'HYDRANT WITHIN 10 FT',
    }]
    os.makedirs(os.path.join(tmpdir, 'raw'))
    os.makedirs(os.path.join(tmpdir, 'raw', 'supplemental'))
    os.makedirs(os.path.join(tmpdir, 'standardized'))

    with open(os.path.join(tmppath, 'raw', 'supplemental',
                           filename), 'w') as f:
        writer = csv.DictWriter(f, list(test[0].keys()))
        writer.writeheader()
        for row in test:
            writer.writerow(row)
    return tmppath


def test_read_file_info(tmpdir):
    tmppath = create_test_csv(tmpdir, 'test.csv')

    config = {
        'data_source': [{
            'name': 'test',
            'filename': 'test.csv',
            'address': 'Location',
            'date': 'Ticket Issue Date',
            'time': 'Issue Time',
            'category': 'Violation Description',
        }]
    }

    standardize_point_data.read_file_info(config, tmppath)
    filename = os.path.join(tmppath, 'standardized', 'points.json')
    with open(filename) as data_file:
        result = json.load(data_file)

    assert result == [{
        'feature': 'test',
        'date': '2014-09-02T09:10:00Z',
        'location': {
            'latitude': 42.37304187600046,
            'longitude': -71.09569369699966
        },
        'category': 'METER EXPIRED'
        },
        {
            'feature': 'test',
            'date': '2014-01-09T09:33:00Z',
            'location': {
                'latitude': 42.374105433000466,
                'longitude': -71.12219272199962
            },
            'category': 'HYDRANT WITHIN 10 FT'
        }]



