import os
import warnings
import pandas as pd
from .. import make_canon_dataset


TEST_FP = os.path.dirname(os.path.abspath(__file__))
DATA_FP = os.path.join(TEST_FP, 'data', 'processed')


def test_read_records(tmpdir):

    result = make_canon_dataset.read_records(
        os.path.join(DATA_FP, 'crash_joined.json'),
        'near_id',
        ['bike', 'pedestrian', 'vehicle']
    )
    expected = pd.DataFrame({
        'near_id': [1, 2, 3, '000', '002', '003', '004', '005', '007', '008'],
        'crash': [2, 18, 2, 5, 3, 14, 2, 11, 1, 4],
        'bike': [0, 3, 0, 0, 1, 1, 0, 3, 0, 1],
        'pedestrian': [0, 3, 1, 1, 0, 0, 1, 0, 0, 0],
        'vehicle': [2, 12, 1, 4, 2, 13, 1, 8, 1, 3]
    })
    pd.testing.assert_frame_equal(result, expected, check_dtype=False)


def test_aggregate_roads():
    """
    Test case for the aggregate_roads function in the make_canon_dataset module.

    This test case verifies that the aggregate_roads function correctly aggregates road data
    and combines it with crash data.

    It performs the following checks:
    - Verifies that the expected columns are present in the resulting dataframe.
    - Verifies that the inferred dtype of the 'segment_id' column is 'string'.
    - Verifies the shape of the resulting dataframe.
    - Verifies the values of the 'width' column in the resulting dataframe.

    """

    aggregated, cr_con = make_canon_dataset.aggregate_roads(
        ['width', 'lanes', 'hwy_type', 'signal', 'oneway'],
        ['osm_speed'],
        DATA_FP,
        ['bike', 'pedestrian', 'vehicle']
    )
    expected_columns = set(['width', 'lanes', 'hwy_type', 'osm_speed', 'signal', 'oneway',
       'segment_id', 'crash', 'bike', 'pedestrian', 'vehicle'])

    expected_width = set([24, 24, 24, 15, 15, 24, 5, 24, 12, 12, 24, 24, 24, 24])

    cr_con_roads = make_canon_dataset.combine_crash_with_segments(
        cr_con, aggregated)
    
    import pandas.testing as pd_testing

    assert pd.api.types.infer_dtype(cr_con_roads.segment_id) == 'string'
    assert set(cr_con_roads.columns.tolist()) == expected_columns
    assert cr_con_roads.shape == (14, 11)
    assert set(cr_con_roads.width) == expected_width
    

def test_road_make():
    with warnings.catch_warnings(record=True) as w:
        result = make_canon_dataset.road_make(
            ['test1', 'test2', 'width', 'lanes', 'hwy_type', 'osm_speed'],
            os.path.join(DATA_FP, 'maps', 'inter_and_non_int.geojson'))
        assert len(w) == 1
        assert str(w[0].message) \
            == "2 feature(s) missing, skipping (test1, test2)"
    assert list(result.columns) == [
        'width', 'lanes', 'hwy_type', 'osm_speed']

    expected = pd.DataFrame({
        'id': ['000', '001', '002', '003', '004', '005', '006',
               '007', '008', '009', '0', '1', '2', '3'],
        'width': [24, 24, 24, 15, 15, 24, 5, 24, 12, 12, 24, 24, 24, 24],
        'lanes': [2, 3, 3, 3, 3, 2, 1, 2, 1, 1, 2, 3, 3, 3],
        'hwy_type': [6, 6, 6, 3, 6, 6, 1, 6, 1, 1, 1, 1, 3, 1],
        'osm_speed': [0, 0, 0, 0, 25, 0, 25, 0, 25, 25, 25, 25, 25, 25]
    })
    expected.set_index('id', inplace=True)
    pd.testing.assert_frame_equal(expected, result)

