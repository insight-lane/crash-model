import ruamel.yaml
import data.config
import os
import csv
import json
from .. import standardize_point_data


def create_test_csv(test_list, tmpdir, filename):
    tmppath = tmpdir.strpath
    
    os.makedirs(os.path.join(tmpdir, 'raw'))
    os.makedirs(os.path.join(tmpdir, 'raw', 'supplemental'))
    os.makedirs(os.path.join(tmpdir, 'standardized'))

    with open(os.path.join(tmppath, 'raw', 'supplemental',
                           filename), 'w') as f:
        writer = csv.DictWriter(f, list(test_list[0].keys()))
        writer.writeheader()
        for row in test_list:
            writer.writerow(row)
    return tmppath


def test_read_file_info_default(tmpdir):

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
    tmppath = create_test_csv(test, tmpdir, 'test.csv')

    config_dict = {
        'name': 'cambridge',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'crashes_files': {'test': {}},
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York",
        'data_source': [{
            'name': 'test',
            'filename': 'test.csv',
            'address': 'Location',
            'date': 'Ticket Issue Date',
            'time': 'Issue Time',
            'category': 'Violation Description'
        }]
    }
    config_filename = os.path.join(tmpdir, 'test.yml')
    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)
    
    standardize_point_data.read_file_info(config, tmppath)
    filename = os.path.join(tmppath, 'standardized', 'points.json')
    with open(filename) as data_file:
        result = json.load(data_file)

    assert result == [{
        'feature': 'test',
        'date': '2014-09-02T09:10:00-04:00',
        'location': {
            'latitude': 42.37304187600046,
            'longitude': -71.09569369699966
        },
        'category': 'METER EXPIRED'
        },
        {
            'feature': 'test',
            'date': '2014-01-09T09:33:00-05:00',
            'location': {
                'latitude': 42.374105433000466,
                'longitude': -71.12219272199962
            },
            'category': 'HYDRANT WITHIN 10 FT'
        }]


def test_read_file_info_agg(tmpdir):
    test = [{
        'SETDATE': '2012-03-15T00:00:00.000Z',
        'LATITUDE': '39.74391',
        'LONGITUDE': '-75.22693',
        'RECORDNUM': '87081',
    }, {
        'SETDATE': '2012-05-02T00:00:00.000Z',
        'LATITUDE': '39.90415873',
        'LONGITUDE': '-75.19348751',
        'RECORDNUM': '87679',
    }]

    tmppath = create_test_csv(test, tmpdir, 'test2.csv')

    config_dict = {
        'name': 'cambridge',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'crashes_files': {'test': {}},
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York",
        'data_source': [{
            'name': 'aggtest',
            'filename': 'test2.csv',
            'latitude': 'LATITUDE',
            'longitude': 'LONGITUDE',
            'date': 'SETDATE',
            'feat': 'f_cont',
            'feat_agg': 'latest',
            'value': 'RECORDNUM',
        }]
    }
    config_filename = os.path.join(tmpdir, 'test.yml')
    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    standardize_point_data.read_file_info(config, tmppath)
    filename = os.path.join(tmppath, 'standardized', 'points.json')
    with open(filename) as data_file:
        result = json.load(data_file)

    assert result == [{
        'feature': 'aggtest',
        'date': '2012-03-14T20:00:00-04:00',
        'location': {
            'latitude': 39.74391,
            'longitude': -75.22693000000001
        },
        'feat_agg': 'latest',
        'value': 87081
        },
        {
        'feature': 'aggtest',
        'date': '2012-05-01T20:00:00-04:00',
        'location': {
            'latitude': 39.90415873,
            'longitude': -75.19348751
        },
        'feat_agg': 'latest',
        'value': 87679
        }]
