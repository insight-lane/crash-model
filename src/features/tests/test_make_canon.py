import os
import warnings
import pandas as pd
from .. import make_canon_dataset

TEST_FP = os.path.dirname(os.path.abspath(__file__))
DATA_FP = os.path.join(TEST_FP, 'data', 'processed')


def test_read_concerns():
    result = make_canon_dataset.read_concerns(
        os.path.join(DATA_FP, 'concern_joined.json'),
        'near_id'
    )
    expected = [(
        'visionzero',
        pd.DataFrame([3, 1, 1, 1], index=['008', '006', '004', '003']),
    ), (
        'seeclickfix',
        pd.DataFrame([11, 21, 32, 19, 15, 5, 9, 28, 17, 28, 8, 2]),
        )]
    assert expected == result
                

def test_aggregate_roads():

    aggregated, cr_con = make_canon_dataset.aggregate_roads(
        ['width', 'lanes', 'hwy_type', 'osm_speed', 'signal', 'oneway'],
        datadir=DATA_FP)

    cr_con_roads = make_canon_dataset.combine_crash_with_segments(
        cr_con, aggregated)
#    assert len(cr_con_roads.year.unique()) == 2
    

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
