# Designed to create a smaller map from a larger map
# Can be used for making test datasets, or for debugging
import argparse
import json
from shapely.geometry import LineString, Point
import geojson
from data.util import read_geojson, get_reproject_point
from data.util import prepare_geojson, reproject_records
from data.add_waze_data import get_linestring


def get_buffer(filename, lat, lon, radius):
    """
    Given a geojson file, latitude and longitude in 4326 projection,
    and a radius, write to file (as geojson) all the LineStrings and
    Points that overlap a circular buffer around the coordinates.
    Args:
        filename
        lat
        lon
        radius
    Returns:
        A list of overlapping geojson features 4326 projection
    """

    segments = read_geojson(filename)

    # Calculate the bounding circle
    overlapping = []
    point = get_reproject_point(lat, lon)
    buffered_poly = point.buffer(radius)
    for segment in segments:
        if segment[0].intersects(buffered_poly):
            
            if type(segment[0]) == LineString:
                coords = [x for x in segment[0].coords]
                overlapping.append({
                    'geometry': {'coordinates': coords, 'type': 'LineString'},
                    'type': 'Feature',
                    'properties': segment[1]
                })
            elif type(segment[0]) == Point:
                overlapping.append({
                    'geometry': {
                        'coordinates': [segment[0].x, segment[0].y],
                        'type': 'Point'
                    },
                    'properties': segment[1]
                })
            elif type(segment[0]) == 'MultiLineString':
                print("MultiLineString not implented yet, skipping...")

    if overlapping:
        overlapping = prepare_geojson(overlapping)
    return overlapping


def get_waze_buffer(filename, outfile, lat, lon, radius):
    """
    Get waze elements that fall within a certain area
    Write them back out to a json file
    """
    items = json.load(open(filename))

    items = [get_linestring(x) for x in items]
    items = reproject_records(items)

    point = get_reproject_point(lat, lon)
    buffered_poly = point.buffer(radius)
    count = 0
    results = []
    for item in items:
        if item['geometry'].intersects(buffered_poly):
            count += 1
            results.append(item['properties'])
    print("{} results found".format(count))

    with open(outfile, 'w') as f:
        json.dump(results, f)

    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", type=str,
                        help="Geojson file used",
                        required=True)
    parser.add_argument("-lat", "--latitude", type=str,
                        help="Latitude of center point",
                        required=True)
    parser.add_argument("-lon", "--longitude", type=str,
                        help="Longitude of center point",
                        required=True)
    parser.add_argument("-r", "--radius", type=int,
                        help="Radius of buffer around coordinates, in meters",
                        required=True)
    parser.add_argument("-o", "--outputfile", type=str,
                        help="Output filename",
                        required=True)
    parser.add_argument("--waze", action='store_true',
                        help="If waze flag is set, read in waze data format")

    args = parser.parse_args()

    if args.waze:
        get_waze_buffer(args.filename, args.outputfile, args.latitude,
                        args.longitude, args.radius)
    else:
        overlapping = get_buffer(args.filename, args.latitude, args.longitude,
                                 args.radius)

        if overlapping:
            with open(args.outputfile, 'w') as outfile:
                geojson.dump(overlapping, outfile)
            print("Copied {} features to {}".format(
                len(overlapping['features']), args.outputfile))
        else:
            print("No overlapping elements found")
