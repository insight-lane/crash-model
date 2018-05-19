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


def test_concerns_by_type():

    items = json.load(open(
        os.path.join(TEST_FP, 'data', 'crash_test_dummy.json')))
    crash_data, crashes = util.group_json_by_location(items)
    items = json.load(open(
        os.path.join(TEST_FP, 'data', 'concern_test_dummy.json')))
    concern_data, concerns = util.group_json_by_location(items)

    results = analysis_util.concern_counts_by_type(
        concern_data, crashes)

    assert results['bike facilities'] == {
        'total': 3,
        'crashes': 2,
        'inter_crashes': 0,
        'inter_total': 0,
        'non_inter_crashes': 2,
        'non_inter_total': 3
    }
    assert results['other'] == {
        'total': 1,
        'crashes': 0,
        'inter_crashes': 0,
        'inter_total': 1,
        'non_inter_crashes': 0,
        'non_inter_total': 0
    }
    assert results["people don't yield while going straight"] == {
        'total': 3,
        'crashes': 2,
        'inter_crashes': 1,
        'inter_total': 1,
        'non_inter_crashes': 1,
        'non_inter_total': 2
    }
    assert results["people don't yield while turning"] == {
        'total': 1,
        'crashes': 0,
        'inter_crashes': 0,
        'inter_total': 0,
        'non_inter_crashes': 0,
        'non_inter_total': 1
    }
    assert results["low visibility"] == {
        'total': 1,
        'crashes': 0,
        'inter_crashes': 0,
        'inter_total': 1,
        'non_inter_crashes': 0,
        'non_inter_total': 0
    }

    results = analysis_util.concern_percentages_by_type(results, cutoff=1)
    results.sort()
    assert results == [
        ['bike facilities', 67.0, 2, 3, 0.0, 0, 0, 67.0, 2, 3],
        ['low visibility', 0.0, 0, 1, 0.0, 0, 1, 0.0, 0, 0],
        ['other', 0.0, 0, 1, 0.0, 0, 1, 0.0, 0, 0],
        ["people don't yield while going straight",
         67.0, 2, 3, 100.0, 1, 1, 50.0, 1, 2],
        ["people don't yield while turning", 0.0, 0, 1, 0.0, 0, 0, 0.0, 0, 1]
    ]
