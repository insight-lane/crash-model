#!/usr/bin/python

import requests
import argparse
import datetime
import json
import gzip
import os
import yaml


if __name__ == '__main__':
    """
    Given a link to a waze feed, and a directory to write to, zip and write
    the resulting json file to the directory
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', "--file", type=str, required=True,
                        help="yml file containing city and waze feed urls")
    parser.add_argument('-d', "--dirname", type=str, required=True,
                        help="directory to write results to")
    
    args = parser.parse_args()

    if not os.path.exists(args.dirname):
        os.makedirs(args.dirname)

    with open(args.file) as f:
        feeds = yaml.safe_load(f)

    for city in feeds:
        response = requests.get(feeds[city])
        dirname = os.path.join(args.dirname, city)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        # Filename is the current minute, in utc time
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
        json_str = json.dumps(response.json())
        json_bytes = json_str.encode('utf-8')

        outfile = os.path.join(dirname,
                               timestamp + '.json.gz')

        with gzip.open(outfile, 'wb') as f:
            f.write(json_bytes)


