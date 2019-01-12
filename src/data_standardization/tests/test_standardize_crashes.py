from .. import standardize_crashes
from data.util import write_geocode_cache
from jsonschema import validate
import json
import os
import csv
import pytz
import pytest

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
    }, {
        "id": "A1B2C3D4E5",
        "dateOccurred": "2016-01-01T02:30:23-05:00",
        "location": {
            "latitude": 42.317987926802246,
            "longitude": -71.06188127008645
        }
    }
    ]

    validate(
        test_crashes,
        json.load(open(
            os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.abspath(__file__))))), "standards", "crashes-schema.json"))))


def test_standardize_with_cache(tmpdir):

    fields = {
        "id": "id",
        "date_complete": "date_of_crash",
        "time": "",
        "time_format": "",
        "latitude": "lat",
        "longitude": "lng",
        "address": 'location'
    }
    # Confirm crashes without coordinates or a geocoded address file are skipped
    crashes_no_coords = [{
        "id": "A1B2C3D4E5",
        "date_of_crash": "2016-01-01T02:30:23-05:00",
        "lat": "",
        "lng": "",
        'location': 'test',
    }]
    assert len(standardize_crashes.read_standardized_fields(
        crashes_no_coords, fields, {'address': 'location'},
        pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 0

    fields['latitude'] = ''
    fields['longitude'] = ''

    # Confirm crashes with a geocoded address are included
    os.mkdir(os.path.join(tmpdir, 'processed'))
    write_geocode_cache({'test test_city': ['test st', 42, -71, 'S']},
                        filename=tmpdir + '/processed/geocoded_addresses.csv')
    assert len(standardize_crashes.read_standardized_fields(
        crashes_no_coords, fields, {'address': 'location'},
               pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 1
    

def test_date_formats(tmpdir):
    """
    Test various combinations of supplying dates.
    """

    fields_date_constructed = {
        "id": "id",
        "date_complete": "date_of_crash",
        "time": "",
        "time_format": "",
        "latitude": "lat",
        "longitude": "lng"
    }

    # Confirm crashes without coordinates and no address are skipped
    crashes_no_coords = [{
        "id": "A1B2C3D4E5",
        "date_of_crash": "2016-01-01T02:30:23-05:00",
        "lat": "",
        "lng": ""
    }]

    assert len(standardize_crashes.read_standardized_fields(
            crashes_no_coords, fields_date_constructed, {},
            pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 0

    # Confirm crashes using date_complete but without a value are skipped
    crashes_no_date = [{
        "id": "A1B2C3D4E5",
        "date_of_crash": "",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    }]

    assert len(standardize_crashes.read_standardized_fields(
        crashes_no_date, fields_date_constructed, {},
        pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 0

    # Confirm crashes using date_complete with a value are standardized
    crashes_with_date = [{
        "id": "A1B2C3D4E5",
        "date_of_crash": "2016-01-01T02:30:23-05:00",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    }]

    assert len(standardize_crashes.read_standardized_fields(
        crashes_with_date, fields_date_constructed, {},
        pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 1

    # Confirm crashes using deconstructed date with all values are standardized
    fields_date_deconstructed = {
        "id": "id",
        "date_complete": "",
        "date_year": "year_of_crash",
        "date_month": "month_of_crash",
        "date_day": "day_of_crash",
        "time": "",
        "time_format": "",
        "latitude": "lat",
        "longitude": "lng"
    }

    crashes_with_date = [{
        "id": "A1B2C3D4E5",
        "year_of_crash": "2016",
        "month_of_crash": "01",
        "day_of_crash": "01",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    }]

    assert len(standardize_crashes.read_standardized_fields(
        crashes_with_date, fields_date_deconstructed, {},
        pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 1

    # Confirm crashes outside of specified start & end year ranges are dropped
    crashes_in_different_years = [{
        "id": "1",
        "date_of_crash": "2016-12-31T02:30:23-05:00",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    },
        {
        "id": "2",
        "date_of_crash": "2017-01-01T02:30:23-05:00",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    },
        {
        "id": "3",
        "date_of_crash": "2018-01-01T02:30:23-05:00",
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    }]

    # filter crashes prior to a start year
    assert len(standardize_crashes.read_standardized_fields(
        crashes_in_different_years, fields_date_constructed, {},
        pytz.timezone("America/New_York"), tmpdir, 'test_city',
        startdate='2017-01-01T00:00:00-05:00')) == 2

    # filter crashes after an end year
    assert len(standardize_crashes.read_standardized_fields(
        crashes_in_different_years, fields_date_constructed, {},
        pytz.timezone("America/New_York"),
        tmpdir, 'test_city',
        enddate='2016-12-31')) == 1

    # filter crashes after an end year
    assert len(standardize_crashes.read_standardized_fields(
        crashes_in_different_years, fields_date_constructed, {},
        pytz.timezone("America/New_York"),
        tmpdir, 'test_city',
        enddate='2017-01-01')) == 2

    # filter crashes between a start and end year
#    assert len(standardize_crashes.read_standardized_fields(
#        crashes_in_different_years, fields_date_constructed, {}, 2016, '2017-01-01T00:00:00-05:00')) == 1

    # Confirm crashes using deconstructed date but missing a day are standardized with a random day
    fields_date_no_day = {
        "id": "id",
        "date_complete": "",
        "date_year": "year_of_crash",
        "date_month": "month_of_crash",
        "date_day": "",
        "time": "",
        "time_format": "",
        "latitude": "lat",
        "longitude": "lng"
    }

    crashes_with_date = [{
        "id": "A1B2C3D4E5",
        "year_of_crash": 2017,
        "month_of_crash": 1,
        "lat": 42.317987926802246,
        "lng": -71.06188127008645
    }]

    assert len(standardize_crashes.read_standardized_fields(
        crashes_with_date, fields_date_no_day, {},
        pytz.timezone("America/New_York"), tmpdir, 'test_city')) == 1
