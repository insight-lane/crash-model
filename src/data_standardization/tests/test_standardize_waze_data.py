import ruamel.yaml
from .. import standardize_waze_data
import data.config
import os
import pytz

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_datetime():
    timezone = pytz.timezone("America/New_York")

    result = standardize_waze_data.get_datetime(
        '2018-10-04 12:13:00:000', timezone)
    assert result.isoformat() == '2018-10-04T08:13:00-04:00'

    result = standardize_waze_data.get_datetime(
        '2018-11-04 01:13:00:000', timezone)
    assert result.isoformat() == '2018-11-03T21:13:00-04:00'

    result = standardize_waze_data.get_datetime(
        '2018-11-04 06:13:00:000', timezone)
    assert result.isoformat() == '2018-11-04T01:13:00-05:00'


def test_read_snapshots(tmpdir):
    config_dict = {
        'name': 'cambridge',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'timezone': 'America/New_York',
        'crashes_files': 'dummy',
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York"
    }
    filename = os.path.join(tmpdir, 'test.yml')
    with open(filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(filename)

    results = standardize_waze_data.read_snapshots(os.path.join(
        TEST_FP, 'data', 'waze'), config)

    expected_results = [
        {
            'pubMillis': 1539632995870,
            'city': 'Cambridge, MA',
            'eventType': 'jam',
            'pubTimeStamp': '2018-10-15 15:49:55',
            'snapshotId': 1
        },
        {
            'country': 'US',
            'subtype': '',
            'pubMillis': 1539632447442,
            'city': 'Cambridge, MA',
            'type': 'JAM',
            'reportRating': 2,
            'location': {
                'latitude': 42.373807,
                'longitude': -71.112465
            },
            'eventType': 'alert',
            'pubTimeStamp': '2018-10-15 15:40:47',
            'snapshotId': 1
        },
        {
            'roadType': 1,
            'city': 'Cambridge, MA',
            'pubMillis': 1539670005835,
            'eventType': 'jam',
            'pubTimeStamp': '2018-10-16 02:06:45',
            'snapshotId': 2
        },
        {
            'type': 'WEATHERHAZARD',
            'subtype': 'HAZARD_ON_ROAD_CONSTRUCTION',
            'city': 'Cambridge, MA',
            'pubMillis': 1539607721062,
            'location': {
                'latitude': 42.371072,
                'longitude': -71.1143
            },
            'eventType': 'alert',
            'pubTimeStamp': '2018-10-15 08:48:41',
            'snapshotId': 2
        },
        {
            'updateDate': 'Wed Oct 17 16:14:17 +0000 2018',
            'speed': 3.79,
            'city': 'Cambridge, MA',
            'detectionDateMillis': 1539788890781,
            'detectionDate': 'Wed Oct 17 15:08:10 +0000 2018',
            'type': 'Small',
            'eventType': 'irregularity',
            'snapshotId': 3
        }
    ]
    assert results == expected_results

    results = standardize_waze_data.read_snapshots(
        os.path.join(TEST_FP, 'data', 'waze'),
        config,
        startdate='2018-10-16',
        enddate='2018-10-16'
    )
    assert results == [
        {
            'roadType': 1,
            'city': 'Cambridge, MA',
            'pubMillis': 1539670005835,
            'eventType': 'jam',
            'pubTimeStamp': '2018-10-16 02:06:45',
            'snapshotId': 1
        },
        {
            'type': 'WEATHERHAZARD',
            'subtype': 'HAZARD_ON_ROAD_CONSTRUCTION',
            'city': 'Cambridge, MA',
            'pubMillis': 1539607721062,
            'location': {
                'latitude': 42.371072,
                'longitude': -71.1143
            },
            'eventType': 'alert',
            'pubTimeStamp': '2018-10-15 08:48:41',
            'snapshotId': 1
        },
    ]
