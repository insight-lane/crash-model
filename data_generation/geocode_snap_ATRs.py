import json
import time
import os
import csv

import pyproj
from ATR_util import *

PROJ = pyproj.Proj(init='epsg:3857')

ATR_FP = '../data/raw/AUTOMATED TRAFFICE RECORDING/'
PROCESSED_DATA_FP = '../data/processed/'
atrs = os.listdir(ATR_FP)

if not os.path.exists(PROCESSED_DATA_FP + 'geocoded_atrs.csv'):
    print "No geocoded_atrs.csv found, geocoding addresses"

    # geocode, parse result - address, lat long
    results = []
    for atr in atrs:
        atr = atr
        if is_readable_ATR(ATR_FP + atr):
            atr_address = clean_ATR_fname(ATR_FP + atr)
            print atr_address
            geocoded_add, lat, lng = geocode_ATR_data(atr_address)
            print str(geocoded_add) + ',' + str(lat) + ',' + str(lng)
            vol, speed, motos, light, heavy = read_ATR(ATR_FP + atr)
            r = [
                atr_address,
                geocoded_add,
                lat,
                lng,
                vol,
                speed,
                motos,
                light,
                heavy,
                atr
            ]
            results.append(r)
            print('Number geocoded: {}'.format(len(results)))
            time.sleep(1) # was running into rate limit issues

    with open(PROCESSED_DATA_FP + 'geocoded_atrs.csv', 'wb') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['orig','geocoded', 'lat', 'lng','volume', 'speed', 'motos', 'light', 'heavy','filename'])
        for r in results:
            writer.writerow(r)
else:
    print('geocoded_atrs.csv already exists, skipping geocoding')

# Read in segments
combined_seg, segments_index = read_segments()
print('Created spatial index')

# Read in atr lats
atrs = []
with open(PROCESSED_DATA_FP + 'geocoded_atrs.csv') as f:
    csv_reader = csv.DictReader(f)
    for r in csv_reader:
        # Some crash 0 / blank coordinates
        if r['lat']!='':
            atrs.append(
                read_record(r, r['lng'], r['lat'],
                           orig=pyproj.Proj(init='epsg:4326'))
            )
print "Read in data from {} atrs".format(len(atrs))

# Find nearest atr - 20 tolerance
print "Snapping atr to segments"
find_nearest(atrs, combined_seg, segments_index, 20)
print len(atrs)
print len(combined_seg)

with open(PROCESSED_DATA_FP + 'snapped_atrs.json', 'w') as f:
    json.dump([x['properties'] for x in atrs], f)
