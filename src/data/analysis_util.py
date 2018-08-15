# Util file solely for analysis.  If you find yourself using any of these
# during the data generation process, you should probably move that
# function to util.py instead
from .util import is_inter
from . import util
BASE_DIR = ''


def summary_crash_rate(crashes):
    """
    Info about intersections vs non intersections and their crash rate
     """

    counts = {
        'inter': 0,
        'non_inter': 0,
        'no_match': 0,
        'inter_plus': 0,
        'non_inter_plus': 0,
    }
    total_crashes = 0
    total_crash_locations = 0
    for k, v in crashes.items():
        total_crash_locations += 1
        total_crashes += v['count']
        if str(k) == '':
            # Sometimes crashes can't be snapped to a segment, probably due to
            # bad data entry from the crash
            counts['no_match'] += 1
        elif is_inter(k):
            if int(v['count']) > 1:
                counts['inter_plus'] += 1
            counts['inter'] += 1
        else:
            if int(v['count']) > 1:
                counts['non_inter_plus'] += 1
            counts['non_inter'] += 1

    return total_crashes, total_crash_locations, counts


def summary_concern_counts(crashes, concerns):
    """
    What percentage of intersections with concerns had crashes
    at varying counts of concerns?
    """

    matching = {}
    # Go through each concern location
    # Increment counts for crash/no crash intersection/no intersection
    # at this location
    inter_total = 0
    inter_loc = 0
    non_inter_total = 0
    non_inter_loc = 0

    total_concerns = 0
    for seg_id, d in concerns.items():
        total_concerns += d['count']
        if d['count'] not in list(matching.keys()):
            matching[d['count']] = {
                'inter': {'crash': 0, 'no_crash': 0},
                'non_inter': {'crash': 0, 'no_crash': 0}
            }
        if is_inter(seg_id):
            key = 'inter'
            inter_total += d['count']
            inter_loc += 1
        else:
            key = 'non_inter'
            non_inter_total += d['count']
            non_inter_loc += 1

        if seg_id in list(crashes.keys()):
            matching[d['count']][key]['crash'] += 1
        else:
            matching[d['count']][key]['no_crash'] += 1

    sorted_matching = sorted(matching.items())

    return [
        total_concerns,
        len(concerns),
        inter_total,
        inter_loc,
        non_inter_total,
        non_inter_loc,
        sorted_matching
    ]


def concern_percentages(concern_summary):

    results = []
    for key, value in concern_summary:
        # Do the 1+,2+ stats as well as 1, 2
        # Still need to break it out by int/non-int
        counts = {
            'total': value['inter']['crash'] + value['inter']['no_crash']
            + value['non_inter']['crash'] + value['non_inter']['no_crash'],
            'crashes': value['inter']['crash'] + value['non_inter']['crash'],
            'inters_total': value['inter']['crash'] + value['inter']['no_crash'],
            # Count of intersections with a concern
            'inters_crashes': value['inter']['crash'],
            'non_inters_total': value['non_inter']['crash']
            + value['non_inter']['no_crash'],
            'non_inters_crashes':  value['non_inter']['crash'],
        }
        # Add all the data for segments with more complaints
        # than the current complaint we're on
        for key2, value2 in concern_summary[key:len(concern_summary)]:

            if key2 > key:
                counts['total'] += value2['inter']['crash'] \
                    + value2['inter']['no_crash'] \
                    + value2['non_inter']['crash'] \
                    + value2['non_inter']['no_crash']
                counts['crashes'] += value2['inter']['crash'] \
                    + value2['non_inter']['crash']
                counts['inters_total'] += value2['inter']['crash'] \
                    + value2['inter']['no_crash']
                counts['inters_crashes'] += value2['inter']['crash']
                counts['non_inters_total'] += value2['non_inter']['crash'] \
                    + value2['non_inter']['no_crash']
                counts['non_inters_crashes'] += value2['non_inter']['crash']
        total_percent_v0 = round(100 * float(counts['crashes'])
                                 / float(counts['total']))
        inter_percent_v0 = round(100 * float(counts['inters_crashes'])
                                 / float(counts['inters_total'])) \
            if counts['inters_total'] else 0
        non_inter_percent_v0 = round((100 * float(
            counts['non_inters_crashes'])/float(
                counts['non_inters_total']))
            if counts['non_inters_total'] else 0)
        results.append([
            key,
            total_percent_v0,
            # total count
            counts['total'],
            inter_percent_v0,
            # total # of intersections with this many or more complaints
            counts['inters_total'],
            non_inter_percent_v0,
            # total # of non-intersections with this many or more complaints
            counts['non_inters_total'],
            round(100 * float(counts['inters_total'])/float(counts['total']))
        ])

    return results


def concern_counts_by_type(
        concern_data, crashes, category_field='REQUESTTYPE'):

    requests = {}
    locations = {}
    for concern in concern_data:

        if concern['near_id'] not in list(locations.keys()):
            locations[concern['near_id']] = {}

        request = concern[category_field]
        # Clean up badly formatted request types
        vals = request.split('nbsp;')
        if len(vals) > 1:
            request = vals[1]

        if request not in list(requests.keys()):
            requests[request] = {
                'crashes': 0,
                'total': 0,
                'inter_crashes': 0,
                'inter_total': 0,
                'non_inter_crashes': 0,
                'non_inter_total': 0,
            }

        # Only count this request if we haven't seen it in this location
        # before.  We might eventually want to count the number of certain
        # types of requests, but not doing that here
        if request not in list(locations[concern['near_id']].keys()):

            # count totals
            if str(concern['near_id']) in list(crashes.keys()):
                requests[request]['crashes'] += 1
            requests[request]['total'] += 1

            # count intersection totals
            if is_inter(concern['near_id']):
                if str(concern['near_id']) in list(crashes.keys()):
                    requests[request]['inter_crashes'] += 1
                requests[request]['inter_total'] += 1
            # count non-intersection totals
            else:
                if str(concern['near_id']) in list(crashes.keys()):
                    requests[request]['non_inter_crashes'] += 1
                requests[request]['non_inter_total'] += 1

        if request not in list(locations[concern['near_id']].keys()):
            locations[concern['near_id']][request] = 0
        locations[concern['near_id']][request] += 1

    return requests


def concern_percentages_by_type(
        requests, cutoff=100):

    results = []
    for k in requests:
        if requests[k]['total'] >= cutoff:
            total_percent = round(100 * float(
                requests[k]['crashes'])/float(requests[k]['total']))

            inter_percent = round(100 * float(
                requests[k]['inter_crashes'])/float(requests[k]['inter_total'])
                if requests[k]['inter_total'] else 0
            )
            non_inter_percent = round(100 * float(
                requests[k]['non_inter_crashes'])/float(
                requests[k]['non_inter_total'])
                if requests[k]['non_inter_total'] else 0
            )
            results.append([
                k,
                total_percent,
                requests[k]['crashes'],
                requests[k]['total'],
                inter_percent,
                requests[k]['inter_crashes'],
                requests[k]['inter_total'],
                non_inter_percent,
                requests[k]['non_inter_crashes'],
                requests[k]['non_inter_total'],
            ])

    return results


def get_analysis_for_city(
        crash_file, concern_file,
        category_field='REQUESTTYPE', years=None,
        cutoff=100):
    
    crash_info = util.group_json_by_location(
        crash_file, years=years, yearfield='CALENDAR_DATE')
    crashes = crash_info[1]

    concern_data, concerns = util.group_json_by_location(
        concern_file,
        otherfields=[category_field])

    total_crashes, crash_locations, results = summary_crash_rate(crashes)

    _, _, _, _, _, _, concern_summary = summary_concern_counts(
            crashes, concerns)

    concern_percent = concern_percentages(concern_summary)
    concerns_by_type = concern_counts_by_type(
        concern_data, crashes, category_field)
    concern_percent_by_type = concern_percentages_by_type(
        concerns_by_type, cutoff)
    return [
        total_crashes,
        crash_locations,
        results,
        concern_summary,
        concern_percent,
        concerns_by_type,
        concern_percent_by_type,
        crashes,
        concerns
    ]

if __name__ == '__main__':

    get_analysis_for_city(
        'tests/data/processed/maps',
        'tests/data/crash_test_dummy.json',
        'tests/data/concern_test_dummy.json')
#        '../../osm-data/processed/concern_joined.json')
