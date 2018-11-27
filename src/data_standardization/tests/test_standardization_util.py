from .. import standardization_util
import json
import os
import pytz

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_parse_date():
    timezone = pytz.timezone('America/New_York')
    assert standardization_util.parse_date(
        '01/08/2009 08:53:00 PM', timezone) == '2009-01-08T20:53:00-05:00'

    assert standardization_util.parse_date(
        '01/08/2009',
        timezone,
        time='08:53:00 PM') == '2009-01-08T20:53:00-05:00'

    assert standardization_util.parse_date(
        '01/08/2009',
        timezone,
        time='75180',
        time_format='seconds') == '2009-01-08T20:53:00-05:00'

    assert standardization_util.parse_date('01/08/2009 unk', timezone) \
        is None

    assert standardization_util.parse_date(
        '01/08/2009',
        timezone,
        time='0201',
        time_format='military') == '2009-01-08T02:01:00-05:00'
        
    assert standardization_util.parse_date(
        '01/08/2009',
        timezone,
        time='1201',
        time_format='military') == '2009-01-08T12:01:00-05:00'

    assert standardization_util.parse_date(
        '01/08/2009',
        timezone,
        time='9999',
        time_format='military') == '2009-01-08T00:00:00-05:00'

    # Test daylight savings time
    assert standardization_util.parse_date(
        '08/08/2009 08:53:00 PM', timezone) == '2009-08-08T20:53:00-04:00'

    # Test UTC conversion
    assert standardization_util.parse_date(
        '2009-01-08T08:53:00.000Z', timezone) == '2009-01-08T03:53:00-05:00'


def test_parse_address():

    address = "29 OXFORD ST\n" + \
        "Cambridge, MA\n" + \
        "(42.37857940800046, -71.11657724799966)"

    lat, lon = standardization_util.parse_address(address)
    assert lat == 42.37857940800046
    assert lon == -71.11657724799966


def test_validate_and_write_schema(tmpdir):
    tmppath = tmpdir.strpath
    
    values = [{
        "id": "1",
        "dateOccurred": "2009-01-08T20:53:00Z",
        "location": {
            "latitude": 42.37857940800046,
            "longitude": -71.11657724799966
        }
    }]
    print(values)
    standardization_util.validate_and_write_schema(
        os.path.join(TEST_FP, 'test-schema.json'),
        values,
        os.path.join(tmppath, 'test.json')
    )

    # Now load the json back and make sure it matches
    items = json.load(open(os.path.join(tmppath, 'test.json')))
    assert items == values

        
    
