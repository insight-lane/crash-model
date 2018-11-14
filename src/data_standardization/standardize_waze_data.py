import argparse
import os
from dateutil.parser import parse
import gzip
import json
import yaml
import datetime
import pytz


CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))


def get_datetime(date, timezone):
    """
    Takes a date string in form 2018-10-15 20:13:00:000
    (the date string is in UTC but is timezone naive)
    and turns it into a datetime object in the given timezone
    Args:
        date - a date string in form 2018-10-15 20:13:00:000
        timezone - a pytz object
    Returns:
        a datetime object
    """
    date = parse(':'.join(date.split(':')[0:-1]))
    utc_date = date.replace(tzinfo=datetime.timezone.utc)
    date = utc_date.astimezone(timezone)
    return date


def convert_from_millis(millis, timezone):
    """
    Given a millisecond, convert into a human-readable
    date string in city's timezone
    Args:
        millis
        timezone - a pytz object
    Returns:
        datetime string
    """
    return datetime.datetime.fromtimestamp(
        millis/1000,
        tz=timezone
    ).strftime('%Y-%m-%d %H:%M:%S')


def read_snapshots(dirname, config, startdate=None, enddate=None):
    """
    Read in files, either .json.gz or .json from a directory
    Create a dictionary of lists of jams, alerts, and irregularities
    To do: handle time zone
    Args:
        dirname - directory the waze data lives in
        config - configuration dict for city
        startdate - drop days before this date
        enddate - drop days after this date
    returns
        a list of all jams, alerts and irregularities for this city
    """
    files = os.listdir(dirname)
    city = config['city'].split(',')[0]

    all_data = []
    min_start = None
    max_end = None

    timezone = pytz.timezone(config['timezone'])
    count = 0
    if startdate:
        startdate = timezone.localize(parse(startdate))
    if enddate:
        enddate = timezone.localize(parse(enddate))

    files.sort()
    for jsonfilename in files:
        _, ext = os.path.splitext(jsonfilename)

        if ext == '.gz':
            with gzip.GzipFile(os.path.join(dirname, jsonfilename), 'r') as f:
                json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                data = json.loads(json_str)
        elif ext == '.json':
            with open(os.path.join(dirname, jsonfilename)) as f:
                data = json.load(f)
        else:
            continue

        end = get_datetime(data['endTime'], timezone)
        if max_end is None or max_end < end:
            max_end = end

        start = get_datetime(data['startTime'], timezone)
        if min_start is None or min_start > start:
            min_start = start

        if (startdate and start < startdate) \
           or (enddate and end > enddate + datetime.timedelta(1)):
            continue
        count += 1

        # We care about jams, alerts, and irregularities
        if 'jams' in data:
            all_data += [
                dict(x, eventType='jam',
                     pubTimeStamp=convert_from_millis(
                         x['pubMillis'],
                         timezone
                     ),
                     snapshotId=count
                )
                for x in data['jams']
                if 'city' in x and city in x['city']
            ]
        if 'alerts' in data:
            all_data += [
                dict(x, eventType='alert',
                     pubTimeStamp=convert_from_millis(
                         x['pubMillis'],
                         timezone
                     ),
                     snapshotId=count
                )
                for x in data['alerts']
                if 'city' in x and city in x['city']]
        if 'irregularities' in data:
            all_data += [
                dict(x, eventType='irregularity',
                     snapshotId=count) for x in data['irregularities']
                if 'city' in x and city in x['city']]

    print("Reading waze data from {} snapshots between {} and {}".format(
        count, min_start, max_end))

    return all_data


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="config file for city")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="path to destination's data folder," +
                        "e.g. ../data/boston")
    parser.add_argument("-s", "--startdate",
                        help="If given, start date in format YYYY-MM-DD")
    parser.add_argument("-e", "--enddate",
                        help="If given, last day included in format YYYY-MM-DD")
    args = parser.parse_args()

    # load config for this city
    config_file = args.config
    with open(config_file) as f:
        config = yaml.safe_load(f)

    snapshots = read_snapshots(
        os.path.join(args.datadir, 'raw', 'waze'),
        config,
        startdate=args.startdate,
        enddate=args.enddate
    )

    jsonfile = os.path.join(
        args.datadir, 'standardized', 'waze.json')
    print("output {} records to {}".format(len(snapshots), jsonfile))
    with open(jsonfile, 'w') as f:
        json.dump(snapshots, f)
