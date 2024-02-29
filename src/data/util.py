from shapely.geometry import Point, shape, mapping, MultiLineString, LineString
import fiona
import pyproj
import rtree
from matplotlib import pyplot
import os
import json
from dateutil.parser import parse
import datetime
from .record import Crash, Record
import geojson
from collections import OrderedDict
from .segment import Segment
from .record import transformer_4326_to_3857, transformer_3857_to_4326


PROJ = pyproj.Proj(init='epsg:3857')
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = BASE_DIR + '/data/processed/maps'
PROCESSED_DATA_FP = BASE_DIR + '/data/processed/'



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

    with open(fp) as f:
        data = json.load(f)
    data = reproject_records([x for x in data['features']])

    return [Segment(x['geometry'], x['properties']) for x in data]


def get_reproject_point(lat, lon, transformer,
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

    lon, lat = transformer.transform(
        lon, lat
    )

    if coords:
        return float(lon), float(lat)
    else:
        return Point(float(lon), float(lat))


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
                segments[segment_id].properties['id'],
                segments[segment_id].geometry.distance(record_point)
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
        combined_seg = segments
    elif geojson:
        # Read in segments and turn them into shape, propery tuples
        combined_seg = [Segment(shape(x['geometry']), x['properties']) for x in
                        segments]
    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element.geometry.bounds)

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


def reproject(coords, transformer=None):
    """
    Reproject a set of coordinate points
    Args:
        coords: a list of coords
        transformer - a pyproj transformer object
            if not given, the default is to transform from
            4326 to 3857 projection
    Returns:
        new_coords = a list of reprojected json points
    """
    new_coords = []
    if not transformer:
        transformer = transformer_4326_to_3857

    for coord in coords:
        re_point = transformer.transform(coord[0], coord[1])
        point = Point(re_point)
        new_coords.append(mapping(point))
    return new_coords


def reproject_records(records, transformer=None):
    """
    Reprojects a set of records from one projection to another
    Records can either be points, line strings, or multiline strings
    Args:
        records - list of records to reproject
        optional: transformer object (if not given, defaults to 4326->3857)
    Returns:
        list of reprojected records
    """
    results = []

    if not transformer:
        transformer = transformer_4326_to_3857

    for record in records:
        coords = record['geometry']['coordinates']
        if record['geometry']['type'] == 'Point':
            re_point = transformer.transform(coords[0], coords[1])
            point = Point(re_point)
            results.append({'geometry': point,
                            'properties': record['properties']})
        elif record['geometry']['type'] == 'MultiLineString':
            new_coords = []
            for segment in coords:
                new_segment = []
                for coord in segment:
                    new_segment.append(transformer.transform(
                        coord[0], coord[1]))
                new_coords.append(new_segment)

            results.append({'geometry': MultiLineString(new_coords),
                            'properties': record['properties']})
        elif record['geometry']['type'] == 'LineString':
            new_coords = []
            for coord in coords:
                new_coords.append(
                    transformer.transform(coord[0], coord[1])
                )
            results.append({'geometry': LineString(new_coords),
                            'properties': record['properties']})

    return results


def write_records_to_geojson(records, outfilename):
    """
    Given a list of record objects, write them to geojson file
    Args:
        records - a list of objects that contain geometry and properties
        outfilename - geojson file to write to
    Returns:
        records as a geojson list
    """

    records = [{
        'geometry': mapping(record.geometry),
        'properties': OrderedDict(record.properties)
        } for record in records]

    records = prepare_geojson(records)
    with open(outfilename, 'w') as outfile:
        geojson.dump(records, outfile, allow_nan=True)
    return records


def prepare_geojson(elements):
    """
    Prepares a list of elements to be written as geojson, reprojecting
    from 3857 to 4326
    Args:
        elements - a list of dicts with geometry and properties
    Results:
        A geojson feature collection
    """

    elements = reproject_records(elements, transformer_3857_to_4326)
    results = [geojson.Feature(
        geometry=mapping(x['geometry']),
        id=x['properties']['id'] if 'id' in x['properties'] else '',
        # properties are usually Fiona.model.Feature - circular ref error
        properties=OrderedDict(x['properties'])) for x in elements]

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
        segment object - LineString or MultiLineString
    Returns:
        x, y tuple for the centerpoint
    """

    if segment.geometry.type == 'LineString':
        point = segment.geometry.interpolate(
            .5, normalized=True)
        return point.x, point.y
    elif segment.geometry.type == 'MultiLineString':
        lines = [x for x in [line for line in segment.geometry.geoms]]
        coords = []
        for line in lines:
            coords.extend([x for x in line.coords])

        minx = min([x[0] for x in coords])
        maxx = max([x[0] for x in coords])
        miny = min([x[1] for x in coords])
        maxy = max([x[1] for x in coords])
        point = LineString([[minx, miny], [maxx, maxy]]).interpolate(
            .5, normalized=True)
        point = segment.geometry.interpolate(segment.geometry.project(point))

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
                x[1], x[0], transformer_3857_to_4326, coords=True)
                                  for x in coords]]
        elif item.type == 'MultiLineString':
            lines = [x for x in item]
            reprojected_coords = []
            for line in lines:
                reprojected_coords.append([get_reproject_point(
                    x[1], x[0], transformer_3857_to_4326, coords=True)
                                  for x in line.coords])
        elif item.type == 'LineString':
            coords = [x for x in item.coords]
            reprojected_coords = [get_reproject_point(
                x[1], x[0], transformer_3857_to_4326, coords=True)
                                  for x in coords]
        elif item.type == 'Point':
            reprojected_coords = get_reproject_point(
                item.y, item.x, transformer_3857_to_4326,
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
        geojson.dump(geojson.FeatureCollection(output), outfile, allow_nan=True)


def write_segments(non_inters, inters, mapfp):
    """
    Writes non_inters, inters and combined inter_and_non_int.geojson
    Args:
        non_inters - list of non_inters segment objects
        inters - list of inters segment objects
        mapfp - maps directory to write to
    """
    # Store non-intersection segments

    non_inters = write_records_to_geojson(
        non_inters, os.path.join(
            mapfp, 'non_inters_segments.geojson'))

    # Store the individual intersections
    int_w_ids = write_records_to_geojson(
        inters, os.path.join(
            mapfp, 'inters_segments.geojson'))

    # Store the combined segments with all properties
    segments = non_inters['features'] + int_w_ids['features']

    with open(os.path.join(mapfp, 'inter_and_non_int.geojson'), 'w') as outfile:
        geojson.dump(geojson.FeatureCollection(segments), outfile, allow_nan=True)


