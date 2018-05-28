import fiona
import pyproj
import csv
import rtree
import geocoder
from time import sleep
from shapely.geometry import Point, shape, mapping, MultiLineString, LineString
import openpyxl
from matplotlib import pyplot
import os
from os.path import exists as path_exists
import json
from dateutil.parser import parse
from record import Crash, Concern, Record


PROJ = pyproj.Proj(init='epsg:3857')
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = BASE_DIR + '/data/processed/maps'
PROCESSED_DATA_FP = BASE_DIR + '/data/processed/'


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


def write_shp(schema, fp, data, shape_key, prop_key, crs={}):
    """ Write Shapefile
    Args:
        schema : schema dictionary
        fp : file (.shp file)
        data : a list of tuples
            one element of the tuple is a shapely shape,
            the other is a dict of properties
        shape_key : column name or tuple index of Shapely shape
        prop_key : column name or tuple index of properties
    """

    with fiona.open(fp, 'w', 'ESRI Shapefile', schema, crs=crs) as c:

        for i in data:

            # some mismatch in yearly crash data
            # need to force it to conform to schema
            for k in schema['properties']:
                if k not in i[prop_key]:
                    i[prop_key][k] = ''

            entry = {
                'geometry': mapping(i[shape_key]),
                # need to maintain key order because of fiona persnicketiness
                'properties': {k: i[prop_key][k]
                               for k in schema['properties']},
            }

            c.write(entry)


def records_to_shapefile(schema, fp, records, crs={}):

    with fiona.open(fp, 'w', 'ESRI Shapefile', schema, crs=crs) as c:

        for record in records:
            c.write({
                'geometry': mapping(record.point),
                'properties': {
                    k: str(v) for (k, v) in record.properties.items()}
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


def read_records(filename, record_type, startyear=None, endyear=None):
    """
    Reads appropriately formatted json file,
    pulls out currently relevant features,
    converts latitude and longitude to projection 4326, and turns into
    a Crash object
    Args:
        filename - json file
        start - optionally give start for date range of crashes
        end - optionally give end for date range of crashes
    Returns:
        A list of Crashes
    """

    records = []
    items = json.load(open(filename))
    if not items:
        return []

    for item in items:
        record = None
        if record_type == 'crash':
            record = Crash(item)
        elif record_type == 'concern':
            record = Concern(item)
        else:
            record = Record(item)
        records.append(record)

    if startyear:
        records = [x for x in records if x.timestamp >= parse(startyear)]
    if endyear:
        records = [x for x in records if x.timestamp < parse(endyear)]

    # Keep track of the earliest and latest crash date used
    start = min([x.timestamp for x in records])
    end = max([x.timestamp for x in records])
    print "Read in data from {} crashes from {} to {}".format(
        len(records), start.date(), end.date())
    return records


def find_nearest(records, segments, segments_index, tolerance,
                 type_record=False):
    """ Finds nearest segment to records
    tolerance : max units distance from record point to consider
    """

    print "Using tolerance {}".format(tolerance)

    for record in records:

        # We are in process of transition to using Record class
        # but haven't converted it everywhere, so until we do, need
        # to look at whether the records are of type record or not
        record_point = None
        if type_record:
            record_point = record.point
        else:
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
            if type_record:
                record.near_id = db_segment_id
            else:
                record['properties']['near_id'] = db_segment_id
        # If no segment matched, populate key = ''
        else:
            if type_record:
                record.near_id = ''
            else:
                record['properties']['near_id'] = ''


def read_segments(dirname=MAP_FP, get_inter=True, get_non_inter=True):
    """
    Reads in the intersection and non intersection segments, and
    makes a spatial index for lookup

    Args:
        Optional directory (defaults to MAP_FP)
        get_inter - if given, return inter segments; defaults to True
        get_non_inter - if given, return non inter segments; defaults to True
    Returns:
        The segments and spatial index
    """
    # Read in segments
    inter = []
    non_inter = []

    if get_inter:
        inter = read_shp(dirname + '/inters_segments.shp')
    if get_non_inter:
        non_inter = read_shp(dirname + '/non_inters_segments.shp')
    print "Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter))

    # Combine inter + non_inter
    combined_seg = inter + non_inter

    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element[0].bounds)
    return combined_seg, segments_index


def group_json_by_field(items, field):
    results = {}
    for item in items:
        if item[field] not in results.keys():
            results[item[field]] = []
        results[item[field]].append(item)
    return results


def group_json_by_location(
        items, years=None, yearfield=None, otherfields=[]):
    """
    Get both the json data from file as well as a dict where the keys
    are the segment id and the values are count, and a list of the values
    of any other fields you specify
    Args:
        jsonfile
        otherfields - optional list of keys of things you want to include
                      in the grouped by segment results
    """
    locations = {}

    for item in items:
        if not years or (
                years and yearfield and parse(item[yearfield]).year in years):
            if str(item['near_id']) not in locations.keys():
                d = {'count': 0}
                for field in otherfields:
                    d[field] = []
                locations[str(item['near_id'])] = d
            locations[str(item['near_id'])]['count'] += 1
            for field in otherfields:
                locations[str(item['near_id'])][field].append(item[field])

    return items, locations


def track(index, step, tot):
    """
    Prints progress at interval
    """
    if index % step == 0:
        print "finished {} of {}".format(index, tot)


def write_points(points, schema, filename):
    """
    Given a list of shapely points,
    de-dupe and write shape files

    Args:
        points: list of points indicating intersections
        schema: schema of the shapefile
        filename: filename for the shapefile
    """

    deduped_points = {}
    # remove duplicate points
    for pt, prop in points:
        if (pt.x, pt.y) not in deduped_points.keys():
            deduped_points[(pt.x, pt.y)] = pt, prop
    with fiona.open(filename, 'w', 'ESRI Shapefile', schema) as output:
        for i, (pt, prop) in enumerate(deduped_points.values()):
            track(i, 500, len(deduped_points))
            output.write({'geometry': mapping(pt), 'properties': prop})


def reproject_records(records, inproj='epsg:4326', outproj='epsg:3857'):
    """
    Reprojects a set of records from one projection to another
    Records can either be points, line strings, or multiline strings
    Args:
        records - list of records to reproject
        inproj - defaults to 4326
        outproj - defaults to 3857
    Returns:
        list of reprojected records
    """
    results = []
    inproj = pyproj.Proj(init=inproj)
    outproj = pyproj.Proj(init=outproj)
    for record in records:

        coords = record['geometry']['coordinates']
        if record['geometry']['type'] == 'Point':
            re_point = pyproj.transform(inproj, outproj, coords[0], coords[1])
            point = Point(re_point)
            results.append({'geometry': mapping(point),
                            'properties': record['properties']})
        elif record['geometry']['type'] == 'MultiLineString':
            new_coords = []
            print coords
            for segment in coords:
                print segment
                new_segment = [
                    pyproj.transform(
                        inproj, outproj, segment[0][0], segment[0][1]),
                    pyproj.transform(
                        inproj, outproj, segment[1][0], segment[1][1])
                ]
                new_coords.append(new_segment)

            results.append({'geometry': MultiLineString(new_coords),
                            'properties': record['properties']})
        elif record['geometry']['type'] == 'LineString':
            new_coords = []
            for coord in coords:
                new_coords.append(
                    pyproj.transform(inproj, outproj, coord[0], coord[1])
                )
            results.append({'geometry': LineString(new_coords),
                            'properties': record['properties']})
    return results


def make_schema(geometry, properties):
    """
    Utility for making schema with 'str' value for each key in properties
    """
    properties_dict = {k: 'str' for k, v in properties.items()}
    schema = {
        'geometry': geometry,
        'properties': properties_dict
    }
    return(schema)


def is_inter(id):
    if len(str(id)) > 1 and str(id)[0:2] == '00':
        return False
    return True
