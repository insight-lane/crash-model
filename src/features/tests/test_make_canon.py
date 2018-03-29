from .. import make_canon_dataset
import os

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_aggregate_roads():

    aggregated, adjacent, cr_con = make_canon_dataset.aggregate_roads(
        ['width', 'lanes', 'hwy_type', 'osm_speed', 'signal', 'oneway'],
        datadir=os.path.join(TEST_FP, 'data', 'processed'))

    cr_con_roads = make_canon_dataset.group_by_date(cr_con, aggregated)

    assert len(cr_con_roads.year.unique()) == 2
    

