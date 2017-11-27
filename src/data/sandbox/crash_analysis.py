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


def parse_json(jsonfile, otherfields=[]):
    crashes = json.load(open(jsonfile))
    locations = {}
    for crash in crashes:
        if str(crash['near_id']) not in locations.keys():
            d = {'count': 0}
            for field in otherfields:
                d[field] = []
            locations[str(crash['near_id'])] = d
        locations[str(crash['near_id'])]['count'] += 1
        for field in otherfields:
            locations[str(crash['near_id'])][field].append(crash[field])
    return crashes, locations


def hist(labels, counts, ylabel, title):
 
    y_pos = np.arange(len(labels))
 
    plt.bar(y_pos, counts, align='center', alpha=0.5)
    plt.xticks(y_pos, labels)
    plt.ylabel(ylabel)
    plt.title(title)
 
    plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--files", nargs='+',
                        help="Give list of csv files to correlate against" +
                        "crash information.")

    args = parser.parse_args()

    crash_data, crashes = parse_json(DATA_FP + 'crash_joined.json')

    concern_data, concerns = parse_json(DATA_FP + 'concern_joined.json',
                                        otherfields=['REQUESTTYPE'])
    concern_hist = {}
    matching = {}
    for id, d in concerns.iteritems():
        if d['count'] not in concern_hist.keys():
            concern_hist[d['count']] = 0
        concern_hist[d['count']] += 1
        if d['count'] not in matching.keys():
            matching[d['count']] = [0, 0]
        if id in crashes.keys():
            matching[d['count']][0] += 1
        else:
            matching[d['count']][1] += 1

    # Question 1:
    # What percentage of intersections with concerns had crashes
    # at varying counts of concerns?
    for key, value in sorted(matching.items()):
        print str(key) + ':' + str(float(
            value[0])/float(value[0] + value[1])) + '\t' + str(
                value[0] + value[1])

    # Question 2:
    # For intersections with a specific complaint type:
    #    what percentage had a crash?
    requests = {}
    for data in concern_data:
        if data['REQUESTTYPE'] not in requests.keys():
            requests[data['REQUESTTYPE']] = 1

    requests = {}
    for k, v in concerns.iteritems():
        for request in v['REQUESTTYPE']:
            if request not in requests.keys():
                requests[request] = {'crash': 0, 'no': 0}
            if str(k) in crashes.keys():
                requests[request]['crash'] += 1
            else:
                requests[request]['no'] += 1

    for k, v in requests.iteritems():
        print k
        print '\t' + str(float(requests[k]['crash'])/(
            float(requests[k]['crash'] + requests[k]['no'])))
        print '\t' + str(requests[k]['crash']) + ',' + str(requests[k]['no'])

    # other questions

    # Accurate counts of type of request vs. just whether or not that type happened
    # Pedestrian crashes vs. not

    # percentages of crashes at intersections without vision zero data

    # how many intersections had a crash at all?

    # number of vision zero complaints may correlate with volume, so maybe less useful as a metric; vs type of complaint

    # also parsing the extra field's text

