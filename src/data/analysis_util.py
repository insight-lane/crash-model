# Util file solely for analysis.  If you find yourself using any of these
# during the data generation process, you should probably move that
# function to util.py instead
from util import is_inter
import util
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
    for k, v in crashes.iteritems():
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
    for id, d in concerns.iteritems():
        total_concerns += d['count']
        if d['count'] not in matching.keys():
            matching[d['count']] = {
                'inter': {'crash': 0, 'no_crash': 0},
                'non_inter': {'crash': 0, 'no_crash': 0}
            }
        if is_inter(id):
            key = 'inter'
            inter_total += d['count']
            inter_loc += 1
        else:
            key = 'non_inter'
            non_inter_total += d['count']
            non_inter_loc += 1

        if id in crashes.keys():
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


def concern_percentages(sorted_matching):

    results = []
    for key, value in sorted_matching:
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
        for key2, value2 in sorted_matching[key:len(sorted_matching)]:

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

