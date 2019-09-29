import geopandas as gpd
from shapely.geometry import Point
from pandas.util.testing import assert_frame_equal
from .. import join_segments_crash


def test_make_rollup():
    """
    Tests total number of crashes per crash location is correctly calculated and
    list of unique crash dates per location is correctly generated
    """
    standardized_crashes = [{
        "id": 1,
        "dateOccurred": "2015-01-01T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "vehicle": 1
    }, {
        "id": 1,
        "dateOccurred": "2015-04-15T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "pedestrian": 1
    }, {
        "id": 1,
        "dateOccurred": "2015-10-20T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "vehicle": 1
    }, {
        "id": 2,
        "dateOccurred": "2015-01-01T01:12:00-05:00",
        "location": {
                "latitude": 42.361,
                "longitude": -71.097
        },
        "address": "LANDSDOWNE ST & MASSACHUSETTS AVE",
        "bike": 1
    }, {
        "id": 3,
        "dateOccurred": "2015-01-01T01:54:00-05:00",
        "location": {
                "latitude": 42.396,
                "longitude": -71.127
        },
        "address": "LOCKE ST & SHEA RD",
        "bike": 1
    }, {
        "id": 3,
        "dateOccurred": "2015-01-01T01:54:00-05:00",
        "location": {
                "latitude": 42.396,
                "longitude": -71.127
        },
        "address": "LOCKE ST & SHEA RD",
        "vehicle": 1
    }]
    expected_rollup_total = gpd.GeoDataFrame()
    expected_rollup_total["coordinates"] = [
        Point(-71.106, 42.365),
        Point(-71.097, 42.361),
        Point(-71.127, 42.396)]
    expected_rollup_total["total_crashes"] = [3, 1, 2]
    expected_rollup_total["crash_dates"] = [
        "2015-01-01T00:45:00-05:00,2015-04-15T00:45:00-05:00,2015-10-20T00:45:00-05:00",
        "2015-01-01T01:12:00-05:00",
        "2015-01-01T01:54:00-05:00"
    ]

    expected_rollup_pedestrian = gpd.GeoDataFrame()
    expected_rollup_pedestrian["coordinates"] = [
        Point(-71.106, 42.365)
    ]
    expected_rollup_pedestrian["total_crashes"] = [1]
    expected_rollup_pedestrian["crash_dates"] = [
        "2015-04-15T00:45:00-05:00"
    ]

    expected_rollup_bike = gpd.GeoDataFrame()
    expected_rollup_bike["coordinates"] = [
        Point(-71.097, 42.361),
        Point(-71.127, 42.396)
    ]
    expected_rollup_bike["total_crashes"] = [1, 1]
    expected_rollup_bike["crash_dates"] = [
        "2015-01-01T01:12:00-05:00",
        "2015-01-01T01:54:00-05:00"
    ]

    expected_rollup_vehicle = gpd.GeoDataFrame()
    expected_rollup_vehicle["coordinates"] = [
        Point(-71.106, 42.365),
        Point(-71.127, 42.396)
    ]
    expected_rollup_vehicle["total_crashes"] = [2, 1]
    expected_rollup_vehicle["crash_dates"] = [
        "2015-01-01T00:45:00-05:00,2015-10-20T00:45:00-05:00",
        "2015-01-01T01:54:00-05:00"
    ]
    split_columns = ['pedestrian', 'bike', 'vehicle']

    results = join_segments_crash.make_crash_rollup(standardized_crashes, split_columns)

    assert_frame_equal(results['all'], expected_rollup_total)
    assert_frame_equal(results['pedestrian'], expected_rollup_pedestrian)
    assert_frame_equal(results['bike'], expected_rollup_bike)
