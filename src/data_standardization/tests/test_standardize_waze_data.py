from .. import standardize_waze_data
import os


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_read_snapshots():
    results = standardize_waze_data.read_snapshots(os.path.join(
        TEST_FP, 'data', 'waze'), {'city': "Cambridge, Massachusetts, USA"})
    assert results == [
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

    results = standardize_waze_data.read_snapshots(
        os.path.join(TEST_FP, 'data', 'waze'),
        {'city': "Cambridge, Massachusetts, USA"},
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
            'eventType': 'alert',
            'pubTimeStamp': '2018-10-15 08:48:41',
            'snapshotId': 1
        },
    ]
