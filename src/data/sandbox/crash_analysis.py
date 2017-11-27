import json
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))


DATA_FP = BASE_DIR + '/data/processed/'
MAP_FP = DATA_FP + 'maps/'


def parse_json(jsonfile, otherfields=[]):
    items = json.load(open(jsonfile))
    locations = {}
    for item in items:
        if str(item['near_id']) not in locations.keys():
            d = {'count': 0}
            for field in otherfields:
                d[field] = []
            locations[str(item['near_id'])] = d
        locations[str(item['near_id'])]['count'] += 1
        for field in otherfields:
            locations[str(item['near_id'])][field].append(item[field])
    return items, locations


def hist(labels, counts, ylabel, title):
 
    y_pos = np.arange(len(labels))
 
    plt.bar(y_pos, counts, align='center', alpha=0.5)
    plt.xticks(y_pos, labels)
    plt.ylabel(ylabel)
    plt.title(title)
 
    plt.show()


def is_inter(id):
    if len(str(id)) > 1 and str(id)[0:2] == '00':
        return False
    return True


def int_vs_non_int(crashes):
    """
    Info about intersections vs non intersections and their crash rate
    """

    # Hard code counts in since they don't change (at least not for Boston)
    # and it's much faster
    inter_count = 8574
    non_inter_count = 17388

    counts = {
        'inter': 0,
        'non_inter': 0,
        'no_match': 0,
        'inter_plus': 0,
        'non_inter_plus': 0,
    }
    for k, v in crashes.iteritems():
        if str(k) == '':
            counts['no_match'] += 1
        elif is_inter(k):
            if int(v['count']) > 1:
                counts['inter_plus'] += 1
            counts['inter'] += 1
        else:
            if int(v['count']) > 1:
                counts['non_inter_plus'] += 1
            counts['non_inter'] += 1

    print "========================================================="
    print "Number of intersections:" + str(inter_count)
    print "Number of non-intersections:" + str(non_inter_count)

    print "Number of intersection segments with 1/more than 1 crash:" \
        + str(counts['inter']) + '/' + str(counts['inter_plus'])
    print "Number of non-intersection segments with 1/more than 1 crash:" \
        + str(counts['non_inter']) + '/' + str(counts['non_inter_plus'])

    print "percent of all segments with crash:" + str(
        float(counts['inter'] + counts['non_inter']) /
        float(inter_count + non_inter_count))

    # Percentage of intersections/non-intersections
    # that have at least one crash
    print "percent of intersections with crash:" + str(
        float(counts['inter'])/float(inter_count))

    print "percent of non-intersections with crash:" + str(
        float(counts['non_inter'])/float(non_inter_count))

    print "percent of intersections with more than 1 crash:" + str(
        float(counts['inter_plus'])/float(inter_count))

    print "percent of non-intersections with more than 1 crash:" + str(
        float(counts['non_inter_plus'])/float(non_inter_count))


def concern_volume(crashes, concerns):
    """
    What percentage of intersections with concerns had crashes
    at varying counts of concerns?
    """

    matching = {}
    for id, d in concerns.iteritems():
        if d['count'] not in matching.keys():
            matching[d['count']] = {
                'inter': [0, 0],
                'non_inter': [0, 0]
            }
        if is_inter(id):
            key = 'inter'
        else:
            key = 'non_inter'

        if id in crashes.keys():
            matching[d['count']][key][0] += 1
        else:
            matching[d['count']][key][1] += 1

    print "========================================================="
    print "concerns\t %\t total\t int %\t int tot\t non-int %\t non-int tot"
    sorted_matching = sorted(matching.items())
    print sorted_matching
    for key, value in sorted(matching.items()):

        # Do the 1+,2+ stats as well as 1, 2
        total_inters = value['inter'][0] + value['inter'][1]
        total_non_inters = value['non_inter'][0] + value['non_inter'][1]

        inter_value = value['inter'][0]
        non_inter_value = value['non_inter'][0]

        total_percent = float(inter_value + non_inter_value) / \
            float(total_inters + total_non_inters)
        inters_percent = 0
        if total_inters > 0:
            inters_percent = float(inter_value) / float(total_inters)
        non_inters_percent = 0
        if total_non_inters > 0:
            non_inters_percent = float(non_inter_value) / \
                float(total_non_inters)
        print str(key) + '\t' + \
            str(total_percent) + \
            '\t' + str(total_inters + total_non_inters) + \
            '\t' + str(inters_percent) + \
            '\t' + str(total_inters) + \
            '\t' + str(non_inters_percent) + \
            '\t' + str(total_non_inters)


def concern_types(concerns, concern_data):
    # Question 2:
    # For intersections with a specific complaint type:
    #    what percentage had a crash?
    requests = {}
    for data in concern_data:
        if data['REQUESTTYPE'] not in requests.keys():
            requests[data['REQUESTTYPE']] = 1

    requests = {}
    all_unique = []

    for k, v in concerns.iteritems():
        unique_requests = {}
        for request in v['REQUESTTYPE']:
            # Clean up badly formatted request types
            vals = request.split('nbsp;')
            if len(vals) > 1:
                request = vals[1]

            if request not in unique_requests.keys():
                unique_requests[request] = 0
            unique_requests[request] += 1

            if request not in requests.keys():
                requests[request] = {'crash': 0, 'no': 0, 'count': 0}
            if str(k) in crashes.keys():
                requests[request]['crash'] += 1
            else:
                requests[request]['no'] += 1
            requests[request]['count'] += 1

        for key, value in unique_requests.iteritems():
            if value > 1:
                all_unique.append([key, value])

    by_type = {}
    for k, v in all_unique:
        if k not in by_type.keys():
            by_type[k] = 0
        by_type[k] += 1

    print "========================================================="
    for k, v in requests.iteritems():
        print k
        print 'Number of requests of this type that appear more than once at an intersection\t' + str(by_type[k])
        print '\t' + str(float(requests[k]['crash'])/(
            float(requests[k]['crash'] + requests[k]['no'])))
        print '\t' + str(requests[k]['crash']) + ',' + str(requests[k]['no'])




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--files", nargs='+',
                        help="Give list of csv files to correlate against" +
                        "crash information.")

    args = parser.parse_args()

    crash_data, crashes = parse_json(DATA_FP + 'crash_joined.json')

    concern_data, concerns = parse_json(DATA_FP + 'concern_joined.json',
                                        otherfields=['REQUESTTYPE'])

    int_vs_non_int(crashes)
    concern_volume(crashes, concerns)
#    concern_types(concerns, concern_data)

    # other questions

    # Pedestrian crashes vs. not

    # number of vision zero complaints may correlate with volume, so maybe less useful as a metric; vs type of complaint

    # also parsing the extra field's text

    # compare vision zero counts with ATR/TMC volume counts
