import json
import fiona
import os
import re
import geocoder
import csv
import rtree
import folium
from shapely.geometry import Point, MultiPoint, shape, mapping
import pyproj

DATA_PATH = '../data'
PROJ = pyproj.Proj(init='epsg:3857')

# parse out clean addresses
atrs = os.listdir(DATA_PATH + r'/raw/AUTOMATED TRAFFICE RECORDING/')
atr_split = [x.split('_') for x in atrs]
atr_address = [' '.join(x[3:5]) for x in atr_split]
atr_address = [re.sub('-', ' ', x) for x in atr_address]
# just get the unique addresses
atr_address = set(atr_address)

# GEOCODE
# check if there's already a geocoded file, if not, geocode
# this uses Google, which may not play nice all the time
# definitely check your data.zip, it should have a geocoded file
if not os.path.exists(DATA_PATH+'/processed/geocoded_atrs.csv'):
    print "No geocoded_atrs.csv found, geocoding addresses"
    g = geocoder.google(atr_address[0] + ' Boston, MA')

    # geocode, parse result - address, lat long
    results = []
    for add in atr_address:
        print "{}% done".format(1.*atr_address.index(add)/len(atr_address))
        g = geocoder.google(add + ' Boston, MA')
        r = [add, g.address, g.lat, g.lng]
        results.append(r)


    with open(DATA_PATH+'/processed/geocoded_atrs.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['orig','geocoded', 'lat', 'lng'])
        for r in results:
            writer.writerow(r)

def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)
def read_record(record, x, y, orig=None, new=PROJ):
    """
    Reads record, outputs dictionary with point and properties
    Specify orig if reprojecting
    """
    if (orig is not None):
        x, y = pyproj.transform(orig, new, x, y)
    r_dict = {
        'point': Point(float(x), float(y)),
        'properties': r
    }
    return(r_dict)
def find_nearest(records, segments, segments_index, tolerance):
    """ Finds nearest segment to records
    tolerance : max units distance from record point to consider
    """

    print "Using tolerance {}".format(tolerance)

    for record in records:
        record_point = record['point']
        record_buffer_bounds = record_point.buffer(tolerance).bounds
        nearby_segments = segments_index.intersection(record_buffer_bounds)
        segment_id_with_distance = [
            # Get db index and distance to point
            (
                segments[segment_id][1]['id'],
                segments[segment_id][0].distance(record_point)
            )
            for segment_id in nearby_segments
        ]
        # Find nearest segment
        if len(segment_id_with_distance):
            nearest = min(segment_id_with_distance, key=lambda tup: tup[1])
            db_segment_id = nearest[0]
            # Add db_segment_id to record
            record['properties']['near_id'] = db_segment_id
        # If no segment matched, populate key = ''
        else:
            record['properties']['near_id'] = ''

#Read in segments
inter = read_shp(DATA_PATH+'/processed/maps/inters_segments.shp')
non_inter = read_shp(DATA_PATH+'/processed/maps/non_inters_segments.shp')
print "Read in {} intersection, {} non-intersection segments".format(len(inter), len(non_inter))

# Combine inter + non_inter
combined_seg = inter + non_inter

# Create spatial index for quick lookup
segments_index = rtree.index.Index()
for idx, element in enumerate(combined_seg):
    segments_index.insert(idx, element[0].bounds)

# Read in atr lats
atrs = []
with open(DATA_PATH+'/processed/geocoded_atrs.csv') as f:
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
print "snapping atr to segments"
find_nearest(atrs, combined_seg, segments_index, 20)

with open(DATA_PATH+'/processed/snapped_atrs.json', 'w') as f:
    json.dump([x['properties'] for x in atrs], f)

# plot results
# skipping this for now
#map = folium.Map(location=[42.3601, -71.0589], zoom_start=12, tiles='Stamen Toner')
#for atr in atrs:
#    note = atr['properties']['orig']
#    lat = atr['properties']['lat']
#    lng = atr['properties']['lng']
#    folium.Marker([lat, lng], popup=note).add_to(map)
#map




