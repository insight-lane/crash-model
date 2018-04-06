import os
from .. import analysis_util
from .. import util
import json

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_summary_crash_rate():

    items = json.load(open(
        os.path.join(TEST_FP, 'data', 'crash_test_dummy.json')))
    crash_data, crashes = util.group_json_by_location(items)
    total_count, total_loc, results = analysis_util.summary_crash_rate(
        crashes)
    assert total_count == 8
    assert total_loc == 4
    assert results == {
        'no_match': 0,
        'inter': 2,
        'inter_plus': 1,
        'non_inter': 2,
        'non_inter_plus': 1
    }


def test_concerns():

    items = json.load(open(
        os.path.join(TEST_FP, 'data', 'crash_test_dummy.json')))
    crash_data, crashes = util.group_json_by_location(items)
    items = json.load(open(
        os.path.join(TEST_FP, 'data', 'concern_test_dummy.json')))
    concern_data, concerns = util.group_json_by_location(items)

    # Summary concerns
    total_count, total_loc, inter_total, inter_loc, non_inter_total, \
        non_inter_loc, results = analysis_util.summary_concern_counts(
            crashes, concerns)
    assert total_count == 10
    assert total_loc == 8
    assert inter_total == 3
    assert inter_loc == 3
    assert non_inter_total == 7
    assert non_inter_loc == 5
    assert results == [(1,
                        {'inter': {'no_crash': 2, 'crash': 1},
                         'non_inter': {'no_crash': 3, 'crash': 1}}),
                       (3,
                        {'inter': {'no_crash': 0, 'crash': 0},
                         'non_inter': {'no_crash': 0, 'crash': 1}})]

    results = analysis_util.concern_percentages(results)
    # percentage of total vision zero complaints with a crash at that location
    assert results[0][1] == 38.0
    # percentage of intersections with at least this many concerns that
    # had a crash
    assert results[0][3] == 33.0
    # number of intersections with at least this many concerns
    assert results[0][4] == 3
    # percentage of non-intersections with at least this many concerns
    # that had a crash
    assert results[0][5] == 40.0
    # number of non-intersections with at least this many concerns
    assert results[0][6] == 5
    # percentage of vision zero concerns that occurred at an intersection
    assert results[0][7] == 38.0

    assert results[1][1] == 100.0
    assert results[1][5] == 100.0
