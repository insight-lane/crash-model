import json
import os
import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


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
    return locations


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

    crashes = parse_json(DATA_FP + 'crash_joined.json')

    concerns = parse_json(DATA_FP + 'concern_joined.json')
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

    print len(crashes.keys())
    print len(concerns.keys())


