# Designed to create a smaller map from a larger map
# Can be used for making test datasets, or for debugging
import argparse
from shapely.geometry import LineString, Point
import geojson
from data.util import read_geojson, get_reproject_point
from data.util import prepare_geojson


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
    args = parser.parse_args()
    
    overlapping = get_buffer(args.filename, args.latitude, args.longitude,
                             args.radius)

    if overlapping:
        with open(args.outputfile, 'w') as outfile:
            geojson.dump(overlapping, outfile)
        print("Copied {} features to {}".format(
            len(overlapping['features']), args.outputfile))
    else:
        print("No overlapping elements found")
