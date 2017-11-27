import json
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))


DATA_FP = BASE_DIR + '/data/processed/'


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


def concern_volume(matching):
    # Question 1:
    # What percentage of intersections with concerns had crashes
    # at varying counts of concerns?
    for key, value in sorted(matching.items()):
        print str(key) + ':' + str(float(
            value[0])/float(value[0] + value[1])) + '\t' + str(
                value[0] + value[1])


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

    concern_volume(matching)
    concern_types(concerns, concern_data)

    # Question 3
    # We are just looking at segments above.  What about intersections
    # What percentage of intersections had crashes?
    # What percentage of segments had crashes?
    


    # other questions

    # Pedestrian crashes vs. not

    # percentages of crashes at intersections without vision zero data

    # how many intersections had a crash at all?

    # number of vision zero complaints may correlate with volume, so maybe less useful as a metric; vs type of complaint

    # also parsing the extra field's text

    # compare vision zero counts with ATR/TMC volume counts
