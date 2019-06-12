import os
import warnings
import pandas as pd
from .. import make_canon_dataset

TEST_FP = os.path.dirname(os.path.abspath(__file__))
DATA_FP = os.path.join(TEST_FP, 'data', 'processed')


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

    expected = pd.DataFrame({
        'id': ['000', '001', '002', '003', '004', '005', '006',
               '007', '008', '009', '0', '1', '2', '3'],
        'width': [24, 24, 24, 15, 15, 24, 5, 24, 12, 12, 24, 24, 24, 24],
        'lanes': [2, 3, 3, 3, 3, 2, 1, 2, 1, 1, 2, 3, 3, 3],
        'hwy_type': [6, 6, 6, 3, 6, 6, 1, 6, 1, 1, 1, 1, 3, 1],
        'osm_speed': [0, 0, 0, 0, 25, 0, 25, 0, 25, 25, 25, 25, 25, 25]
    })
    expected.set_index('id', inplace=True)
    assert expected.equals(result)

