import fiona
import pyproj
import csv
import rtree
import geocoder
from time import sleep
from shapely.geometry import Point, shape, mapping

PROJ = pyproj.Proj(init='epsg:3857')
MAP_FP = 'data/processed/maps'


def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)


def write_shp(schema, fp, data, shape_key, prop_key):
    """ Write Shapefile
    schema : schema dictionary
    shape_key : column name or tuple index of Shapely shape
    prop_key : column name or tuple index of properties
    """

    with fiona.open(fp, 'w', 'ESRI Shapefile', schema) as c:
        for i in data:
            # some mismatch in yearly crash data
            # need to force it to conform to schema
            for k in schema['properties']:
                if k not in i[prop_key]:
                    i[prop_key][k] = ''
            c.write({
                'geometry': mapping(i[shape_key]),
                # need to maintain key order because of fiona persnicketiness
                'properties': {
                    k: i[prop_key][k] for k in schema['properties']},
            })


def read_record(record, x, y, orig=None, new=PROJ):
    """
    Reads record, outputs dictionary with point and properties
    Specify orig if reprojecting
    """
    if (orig is not None):
        x, y = pyproj.transform(orig, new, x, y)
    r_dict = {
        'point': Point(float(x), float(y)),
        'properties': record
    }
    return(r_dict)


# Temporarily commented out; not sure we actually use this anymore
# now that we have csv_to_projected_records
# def read_csv(file):
#    # Read in CAD crash data
#    crash = []
#    with open(file) as f:
#        csv_reader = csv.DictReader(f)
#        for r in csv_reader:
#            # Some crash 0 / blank coordinates
#            if r['X'] != '':
#                crash.append(
#                    read_record(r, r['X'], r['Y'],
#                                orig=pyproj.Proj(init='epsg:4326'))
#                )
#    return crash


def csv_to_projected_records(filename, x='X', y='Y'):
    """
    Reads a csv file in and creates a list of records,
    reprojecting x and y coordinates from projection 4326
    to projection 3857

    Args:
        filename (csv file)
        optional:
            x coordinate name (defaults to 'X')
            y coordinate name (defaults to 'Y')
    """
    records = []
    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            # Can possibly have 0 / blank coordinates
            if r[x] != '':
                records.append(
                    read_record(r, r[x], r[y],
                                orig=pyproj.Proj(init='epsg:4326'))
                )
    return records


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


def read_segments():
    # Read in segments
    inter = read_shp(MAP_FP + '/inters_segments.shp')
    non_inter = read_shp(MAP_FP + '/non_inters_segments.shp')
    print "Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter))

    # Combine inter + non_inter
    combined_seg = inter + non_inter

    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element[0].bounds)
    return combined_seg, segments_index


def geocode_address(address):
    """
    Use google's API to look up the address
    Due to rate limiting, try a few times with an increasing
    wait if no address is found

    Args:
        address
    Returns:
        address, latitude, longitude
    """
    g = geocoder.google(address)
    attempts = 0
    while g.address is None and attempts < 3:
        attempts += 1
        sleep(attempts ** 2)
        g = geocoder.google(address)
    return g.address, g.lat, g.lng
