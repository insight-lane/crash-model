import argparse
import requests
import time
import json
import os
import csv


def convert_to_csv(filename):

    with open(filename + '.json', 'r') as f:
        tickets = json.load(f)

        print "Converting " + str(len(tickets)) + " tickets to csv"
        # Since this so far only looks at Boston, hard coding
        # fields we care about.  Will need to check against other cities
        fieldnames = ['X', 'Y', 'type', 'created', 'summary', 'description']
        with open(filename + '.csv', 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for t in tickets:

                writer.writerow({
                    'X': t['lng'],
                    'Y': t['lat'],
                    'type': t['request_type']['title']
                    if 'title' in t['request_type'].keys() else '',
                    'created': t['created_at'],
                    'summary': t['summary'].encode("utf-8"),
                    'description': t['description'].encode("utf-8")
                    if t['description'] else ''
                })


def get_tickets(place_url, outfile, statuses=[
        'open', 'acknowledged', 'closed', 'archived']):
    print outfile
    if not os.path.exists(outfile):
        status_str = ','.join(statuses)

        request_str = 'https://seeclickfix.com/api/v2/issues?place_url=' \
                      + place_url \
                      + '&status=' + status_str
        curr_page = requests.get(request_str)
        md = curr_page.json()['metadata']['pagination']
        print "Getting " + str(md['pages']) + " pages of see click fix data"

        next_page_url = md['next_page_url']
        all = curr_page.json()['issues']
        print "page:" + str(md['page'])
        while next_page_url:
            curr_page = requests.get(next_page_url)
            md = curr_page.json()['metadata']['pagination']
            print "page:" + str(md['page'])
            all += curr_page.json()['issues']
            next_page_url = md['next_page_url']
            time.sleep(.5)

        with open(outfile, 'w') as f:
            json.dump(all, f)
    else:
        print "See click fix file already exists, skipping query..."

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("outputfile", type=str,
                        help="output file prefix")
    parser.add_argument("-c", "--city", type=str, default='Boston')
    parser.add_argument("-s", "--status_list", nargs="+",
                        default=['open', 'acknowledged', 'closed', 'archived'])

    # Todo: add ability to grab other cities; boston was easy, but some
    # cities don't have obvious place_urls, and haven't yet looked into
    # how to best look that up
    args = parser.parse_args()

    filename = args.outputfile
    city = args.city

    get_tickets(city, filename + '.json', statuses=args.status_list)
    convert_to_csv(filename)
