import fiona
import pyproj
import csv
import rtree
import geocoder
from time import sleep
from shapely.geometry import Point, shape, mapping
import openpyxl
from matplotlib import pyplot
from os.path import exists as path_exists

PROJ = pyproj.Proj(init='epsg:3857')
MAP_FP = 'data/processed/maps'
PROCESSED_DATA_FP = 'data/processed/'


def read_geocode_cache(filename=PROCESSED_DATA_FP+'geocoded_addresses.csv'):
    """
    Read in a csv file with columns:
        Input address
        Output address
        Latitude
        Longitude
    Args:
        filename
    Results:
        dict of input address to list of output address, latitude, longitude
    """

    if not path_exists(filename):
        return {}
    cached = {}
    with open(filename) as f:
        csv_reader = csv.DictReader(f)
        for r in csv_reader:
            cached[r['Input Address']] = [
                r['Output Address'],
                r['Latitude'],
                r['Longitude']
            ]
    return cached


def write_geocode_cache(results,
                        filename=PROCESSED_DATA_FP + 'geocoded_addresses.csv'):
    """
    Write a csv file with columns:
        Input address
        Output address
        Latitude
        Longitude
    Args:
        results - dict of geocoded results
        filename - file to write to (defaults to geocoded_addresses.csv)
    """

    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Input Address',
            'Output Address',
            'Latitude',
            'Longitude'
        ])
        for key, value in results.iteritems():
            writer.writerow([key, value[0], value[1], value[2]])


def geocode_address(address, cached={}):
    """
    Check an optional cache to see if we already have the geocoded address
    Otherwise, use google's API to look up the address
    Due to rate limiting, try a few times with an increasing
    wait if no address is found

    Args:
        address
        cached (optional)
    Returns:
        address, latitude, longitude
    """
    if address in cached.keys():
        return cached[address]
    g = geocoder.google(address)
    attempts = 0
    while g.address is None and attempts < 3:
        attempts += 1
        sleep(attempts ** 2)
        g = geocoder.google(address)
    return g.address, g.lat, g.lng


def get_hourly_rates(files):
    """
    Function that reads ATRs and generates a sparkline plot
    of percentages of traffic over time
    
    Args:
        files - list of filenames to process
        outfile - where to write the resulting plot
    """
    all_counts = []
    for f in files:
        wb = openpyxl.load_workbook(f, data_only=True)
        sheet_names = wb.get_sheet_names()
        if 'Classification-Combined' in sheet_names:
            sheet = wb.get_sheet_by_name('Classification-Combined')
            # Right now the cell locations are hardcoded,
            # but if we expand to cover different formats, will need to change
            counts = []
            for row_index in range(9, 33):
                cell = "{}{}".format('O', row_index)
                val = sheet[cell].value
                counts.append(float(val))
            total = sheet['O34'].value
            for i in range(len(counts)):
                counts[i] = counts[i]/total
            all_counts.append(counts)
    return all_counts


def plot_hourly_rates(all_counts, outfile):
    """
    Generates a sparkline plot of percentages of traffic over time
    Eventually this should be moved to a visualization utils directory

    Args:
        all_counts - a list of lists of percentages
        outfile - where to write the resulting plot
    """

    bins = range(0, 24)
    for val in all_counts:
        pyplot.plot(bins, val)
    pyplot.legend(loc='upper right')
    pyplot.savefig(outfile)


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
            c.write({
                'geometry': mapping(i[shape_key]),
                'properties': i[prop_key],
            })


def record_to_csv(filename, records):
    """
    Write a csv file from records
    Args:
        filename
        records - list of records (a dict of dicts)
    """

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=records[0]['properties'].keys())
        writer.writeheader()
        for record in records:
            writer.writerow(record['properties'])


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


def raw_to_record_list(raw, orig, x='X', y='Y'):
    """
    Takes a list of dicts, and reprojects it into a list of records
    Args:
        raw - list of dicts
        orig - original projection
        x - name of key indicating longitude (default 'X')
        y - name of key indicating latitude (default 'Y')
    """
    result = []
    for r in raw:
        result.append(
            read_record(r, r[x], r[y],
                        orig=orig)
        )
    return result


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
    projecting x and y coordinates to projection 4326

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




