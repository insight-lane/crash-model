import json
import time
import os
import re
import csv

import fiona
import geocoder
import rtree
import folium
from shapely.geometry import Point, MultiPoint, shape, mapping
import pyproj

from ATR_util import *

PROJ = pyproj.Proj(init='epsg:3857')

os.chdir('../data/raw/AUTOMATED TRAFFICE RECORDING/')
atrs = os.listdir(os.getcwd())

if not os.path.exists('../../processed/geocoded_atrs.csv'):
    print "No geocoded_atrs.csv found, geocoding addresses"

    # geocode, parse result - address, lat long
    results = []
    for atr in atrs:
        if is_readable_ATR(atr):
            atr_address = clean_ATR_fname(atr)
            geocoded_add, lat, lng = geocode_address(atr_address)
            vol, speed, motos, light, heavy = read_ATR(atr)
            r = [atr_address, geocoded_add, lat, lng, vol, speed, motos, light, heavy, atr]
            results.append(r)
            print('Number geocoded: {}'.format(len(results)))

    
    with open('../../processed/geocoded_atrs.csv', 'wb') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['orig','geocoded', 'lat', 'lng','volume', 'speed', 'motos', 'light', 'heavy','filename'])
        for r in results:
            writer.writerow(r)
else:
    print('geocoded_atrs.csv already exists, skipping geocoding')

#Read in segments
inter = read_shp('../../processed/maps/inters_segments.shp')
non_inter = read_shp('../../processed/maps/non_inters_segments.shp')
print "Read in {} intersection, {} non-intersection segments".format(len(inter), len(non_inter))

# Combine inter + non_inter
combined_seg = inter + non_inter

# # Create spatial index for quick lookup
segments_index = rtree.index.Index()
for idx, element in enumerate(combined_seg):
    segments_index.insert(idx, element[0].bounds)

print('Created spatial index')

# Read in atr lats
atrs = []
with open('../../processed/geocoded_atrs.csv') as f:
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

with open('../../processed/snapped_atrs.json', 'w') as f:
    json.dump([x['properties'] for x in atrs], f)
