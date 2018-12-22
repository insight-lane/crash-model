import fiona
import pyproj
import csv
import rtree
import geocoder
from time import sleep
from shapely.geometry import Point, shape, mapping, MultiLineString, LineString
from matplotlib import pyplot
import os
from os.path import exists as path_exists
import json
from dateutil.parser import parse
import datetime
from .record import Crash, Concern, Record
import geojson
from .segment import Segment


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
        Status (whether the geocoding was successful 'S', or the address
            could not be found 'F', or there was an intermittent error such as
            a time out, '')
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
                r['Longitude'],
                r['Status'],
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

    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Input Address',
            'Output Address',
            'Latitude',
            'Longitude',
            'Status',
        ])
        for key, value in results.items():
            writer.writerow([key, value[0], value[1], value[2], value[3]])


def lookup_address(intersection, cached, mapboxtoken=None):
    """
    Look up an intersection first in the cache, and if it
    doesn't exist, geocode it

    Args:
        intersection: string
        cached: dict
    Returns:
        tuple of original address, geocoded address, latitude, longitude
    """

    # If we've cached this either successfully or were unable to find
    # the address previously
    if intersection in list(cached.keys()) and cached[intersection][3]:
        print(intersection + ' is cached')
        return cached[intersection]
    else:
        print('geocoding ' + intersection)
        return list(geocode_address(intersection, {}, mapboxtoken))


def geocode_address(address, cached={}, mapboxtoken=None):
    """
    Check an optional cache to see if we already have the geocoded address
    Otherwise, use google's API to look up the address
    Due to rate limiting, try a few times with an increasing
    wait if no address is found

    Args:
        address
        cached (optional)
    Returns:
        address, latitude, longitude, status
    """
    if address in list(cached.keys()):
        return cached[address]
    if mapboxtoken:
        g = geocoder.mapbox(address, key=mapboxtoken)
    else:
        g = geocoder.google(address)
    attempts = 0
    while g.address is None and attempts < 3:
        attempts += 1
        sleep(attempts ** 2)
        g = geocoder.google(address)

    status = ''

    if g.status == 'OK':
        status = 'S'
    elif g.status == 'ZERO_RESULTS':
        status = 'F'
    return g.address, g.lat, g.lng, status


def get_hourly_rates(volume_file):
    """
    Give the average percentage of traffic that occurs each hour
    Args:
        volume_file - path to standarized volume file
    Returns:
        counts - the average percentage of traffic that occurs each hour
    """
    all_counts = []
    with open(volume_file) as data_file:
        volumes = json.load(data_file)
    
        for v in volumes:
            counts = v['volume']['hourlyVolume']
            total = sum(counts)
            counts = [x/total for x in counts]
            if counts:
                all_counts.append(counts)

    counts = [sum(i)/len(all_counts) for i in zip(*all_counts)]

    return counts


def plot_hourly_rates(all_counts, outfile):
    """
    Generates a sparkline plot of percentages of traffic over time
    Eventually this should be moved to a visualization utils directory

    Args:
        all_counts - a list of lists of percentages
        outfile - where to write the resulting plot
    """

    bins = list(range(0, 24))
    for val in all_counts:
        pyplot.plot(bins, val)
    pyplot.legend(loc='upper right')
    pyplot.savefig(outfile)


def read_geojson(fp):
    """ Read geojson file, reproject to 3857, and
    output tuple geometry + property """

    data = fiona.open(fp)
    data = reproject_records([x for x in data])
    return [(x['geometry'], x['properties']) for x in data]


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


def get_reproject_point(lat, lon, inproj='epsg:4326',
                        outproj='epsg:3857',
                        coords=False):
    """
    Turn a point in one projection into another
    Default is to convert from 4326 to 3857
    Args:
        lat
        long
    Returns:
        A point in the specified projection
    """
    lon, lat = pyproj.transform(
        pyproj.Proj(init=inproj), pyproj.Proj(init=outproj),
        lon, lat
    )
    if coords:
        return float(lon), float(lat)
    else:
        return Point(float(lon), float(lat))


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


def read_records_from_geojson(filename):
    """
    Reads appropriately formatted geojson file,
    converts latitude and longitude to projection 4326, and turns into
    a Record object
    Args:
        filename - geojson file
    Returns:
        A list of Records
    """

    records = []
    with open(filename) as f:
        items = geojson.load(f)
        for item in items['features']:
            properties = item['properties']
            properties['location'] = {
                'latitude': item['geometry']['coordinates'][1],
                'longitude': item['geometry']['coordinates'][0]
            }
            record = Record(properties)
            records.append(record)
    return records


def read_records(filename, record_type,
                 startdate=None, enddate=None):
    """
    Reads appropriately formatted json file,
    pulls out currently relevant features,
    converts latitude and longitude to projection 4326, and turns into
    a Crash object
    Args:
        filename - json file
        start - optionally give start for date range of crashes
        end - optionally give end date after which to exclude crashes
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

    if startdate:
        records = [x for x in records if x.timestamp >= parse(startdate)]
    if enddate:
        records = [x for x in records
                   if x.timestamp < parse(enddate) + datetime.timedelta(1)]

    # Keep track of the earliest and latest crash date used
    start = min([x.timestamp for x in records])
    end = max([x.timestamp for x in records])
    if start and end:
        print("Read in data from {} crashes from {} to {}".format(
            len(records), start.date(), end.date()))
    print("Read in data from {} records".format(len(records)))

    return records


def find_nearest(records, segments, segments_index, tolerance,
                 type_record=False):
    """ Finds nearest segment to records
    tolerance : max units distance from record point to consider
    """

    print("Using tolerance {}".format(tolerance))

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

    inter = []
    non_inter = []

    if get_inter:
        inter = fiona.open(dirname + '/inters_segments.geojson')
        inter = reproject_records([x for x in inter])
        inter = [{
            'geometry': mapping(x['geometry']),
            'properties': x['properties']} for x in inter]

    if get_non_inter:
        non_inter = fiona.open(
            dirname + '/non_inters_segments.geojson')
        non_inter = reproject_records([x for x in non_inter])
        non_inter = [{
            'geometry': mapping(x['geometry']),
            'properties': x['properties']} for x in non_inter]

    print("Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter)))

    return index_segments(list(inter) + list(non_inter))


def index_segments(segments, geojson=True, segment=False):
    """
    Reads a list of segments in geojson format, and makes
    a spatial index for lookup
    Args:
        list of segments
        geojson - whether or not the list of tuples are in geojson format
            (the other option is shapely shapes) defaults to True
    Returns:
        segments (in shapely format), and segments_index
    """

    combined_seg = segments
    if segment:
        combined_seg = [(x.geometry, x.properties) for x in segments]
    elif geojson:
        # Read in segments and turn them into shape, propery tuples
        combined_seg = [(shape(x['geometry']), x['properties']) for x in
                        segments]
    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element[0].bounds)

    return combined_seg, segments_index


def group_json_by_field(items, field):
    results = {}
    for item in items:
        if item[field] not in list(results.keys()):
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
            if str(item['near_id']) not in list(locations.keys()):
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
        print("finished {} of {}".format(index, tot))


def reproject(coords, inproj='epsg:4326', outproj='epsg:3857'):
    new_coords = []
    inproj = pyproj.Proj(init=inproj)
    outproj = pyproj.Proj(init=outproj)

    for coord in coords:
        re_point = pyproj.transform(inproj, outproj, coord[0], coord[1])
        point = Point(re_point)
        new_coords.append(mapping(point))
    return new_coords


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
            results.append({'geometry': point,
                            'properties': record['properties']})
        elif record['geometry']['type'] == 'MultiLineString':
            new_coords = []
            for segment in coords:
                new_segment = []
                for coord in segment:
                    new_segment.append(pyproj.transform(
                        inproj, outproj, coord[0], coord[1]))
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


def prepare_geojson(records):
    """
    Prepares a set of records to be written as geojson, reprojecting
    from 3857 to 4326
    Args:
        records - a list of dicts with geometry and properties
    Results:
        A geojson feature collection
    """

    records = reproject_records(records, inproj='epsg:3857',
                                outproj='epsg:4326')
    results = [geojson.Feature(
        geometry=mapping(x['geometry']),
        id=x['properties']['id'] if 'id' in x['properties'] else '',
        properties=x['properties']) for x in records]

    return geojson.FeatureCollection(results)


def make_schema(geometry, properties):
    """
    Utility for making schema with 'str' value for each key in properties
    """
    properties_dict = {k: 'str' for k, v in list(properties.items())}
    schema = {
        'geometry': geometry,
        'properties': properties_dict
    }
    return(schema)


def is_inter(seg_id):
    if len(str(seg_id)) > 1 and str(seg_id)[0:2] == '00':
        return False
    return True


def get_center_point(segment):
    """
    Get the centerpoint for a linestring or multiline string
    Args:
        segment - Geojson LineString or MultiLineString
    Returns:
        Geojson point
    """

    if segment['geometry']['type'] == 'LineString':
        point = LineString(
            segment['geometry']['coordinates']).interpolate(
            .5, normalized=True)
        return point.x, point.y
    elif segment['geometry']['type'] == 'MultiLineString':
        # Make a rectangle around the multiline
        coords = [item for coords in segment[
            'geometry']['coordinates'] for item in coords]

        minx = min([x[0] for x in coords])
        maxx = max([x[0] for x in coords])
        miny = min([x[1] for x in coords])
        maxy = max([x[1] for x in coords])

        point = LineString([[minx, miny], [maxx, maxy]]).interpolate(
            .5, normalized=True)
        mlstring = MultiLineString(segment['geometry']['coordinates'])
        point = mlstring.interpolate(mlstring.project(point))

        return point.x, point.y

    return None, None


def get_roads_and_inters(filename):
    """
    Pull the roads and the intersections from a geojson file
    Typically this will read from the standardized osm_elements.geojson.
    Since that file includes dead ends, these will also be stripped.
    Everything will also be reprojected into 3857 projection
    Args:
        filename - geojson file of linestrings and points
    Returns:
        roads, intersections
    """
    data = fiona.open(filename)
    data = reproject_records([x for x in data])

    # All the line strings are roads
    roads = [Segment(x['geometry'], x['properties']) for x in data
             if x['geometry'].type == 'LineString']

    # Get the intersection list by excluding anything that's not labeled
    # as an intersection
    inters = [x for x in data if x['geometry'].type == 'Point'
              and 'intersection' in list(x['properties'].keys())
              and x['properties']['intersection']]

    return roads, inters


def output_from_shapes(items, filename):
    """
    Write a list of polygons in 3857 projection to file in 4326 projection
    Used for debugging purposes
    At the moment, since this has only output intersection buffers,
    the resulting output won't contain any properties

    Args:
        polys - list of polygon objects
        filename - output file
    Returns:
        nothing, writes to file
    """
    output = []
    for item, properties in items:
        if item.type == 'Polygon':
            coords = [x for x in item.exterior.coords]
            reprojected_coords = [[get_reproject_point(
                x[1], x[0], inproj='epsg:3857', outproj='epsg:4326', coords=True)
                                  for x in coords]]
        elif item.type == 'MultiLineString':
            lines = [x for x in item]
            reprojected_coords = []
            for line in lines:
                reprojected_coords.append([get_reproject_point(
                x[1], x[0], inproj='epsg:3857', outproj='epsg:4326', coords=True)
                                  for x in line.coords])
        elif item.type == 'LineString':
            coords = [x for x in item.coords]
            reprojected_coords = [get_reproject_point(
                x[1], x[0], inproj='epsg:3857', outproj='epsg:4326', coords=True)
                                  for x in coords]
        elif item.type == 'Point':
            reprojected_coords = get_reproject_point(
                item.y, item.x, inproj='epsg:3857', outproj='epsg:4326',
                coords=True
            )
        else:
            print("{} not supported, skipping".format(item.type))
            continue
        output.append({
            'type': 'Feature',
            'geometry': {
                'type': item.type,
                'coordinates': reprojected_coords
            },
            'properties': properties
        })

    with open(filename, 'w') as outfile:
        geojson.dump(geojson.FeatureCollection(output), outfile)


def get_feature_list(config):
    """
    Make the list of features, and write it to the city's data folder
    That way, we can avoid hardcoding the feature list in multiple places.
    If you add extra features, the only place you should need to add them
    is here
    Args:
        Config - the city's config file
    """

    # Features drawn from open street maps
    feat_types = {'f_cat': [], 'f_cont': []}

    # Run through the possible feature types
    for feat_type in ['openstreetmap_features',
                      'waze_features', 'additional_map_features']:
        if feat_type in config:
            if 'categorical' in config[feat_type]:
                feat_types['f_cat'] += [x for x in config[
                    feat_type]['categorical'].keys()]
                feat_types['f_cont'] += [x for x in config[
                    feat_type]['continuous'].keys()]

    # Add point-based features, still in a slightly different format
    if 'data_source' in config and config['data_source']:
        for additional in config['data_source']:
            feat_types[additional['feat']].append(additional['name'])

    return feat_types
