import argparse
import osmnx as ox
import fiona
import shutil
import os
import re
import csv
import geojson
import json
import requests
import geopandas
from collections import OrderedDict
from . import util
from shapely.geometry import Polygon, LineString, LinearRing
import data.config
from .record import transformer_3857_to_4326


MAP_FP = None
STANDARDIZED_FP = None
RAW_FP = None


def find_osm_polygon(city):
    """Interrogate the OSM nominatim API for a city polygon.

    Nominatim may not always return city matches in the most intuitive order,
    so results need to be searched for a compatible polygon. The index of the
    polygon is required for proper use of osmnx.graph_from_place(). Some cities
    do not have a polygon at all, in which case they defer to using
    graph_from_point() with city lat & lng.

    Args:
        city (str): city to search for
    Returns:
        int: index of polygon+1 (becomes the correct 'which_result' value)
        None: if no polygon found
    """

    search_params = {'format': 'json', 'limit': 5,
                     'dedupe': 0, 'polygon_geojson': 1, 'q': city}
    url = 'https://nominatim.openstreetmap.org/search'

    response = requests.get(url, params=search_params)
    for index, match in enumerate(response.json()):
        # a match that can be used by graph_from_place needs to be a Polygon
        # or MultiPolygon
        if (match['geojson']['type'] in ['Polygon', 'MultiPolygon']):
            return index+1, match['geojson']

    return None, None


def expand_polygon(polygon, points_file, max_percent=.1):
    """
    Read the crash data, determine what proportion of crashes fall outside
    the city polygon
    Args:
        polygon - city polygon
        points_file - json points file
        Optional: max_percent (in case you want to override the maximum
            percent that can be outside the original polygon to buffer)
    Returns:
        Updated polygon if it was a polygon to start with, None otherwise
    """

    # Right now, only support this for polygons
    if polygon['type'] != 'Polygon':
        return None

    polygon_coords = util.reproject([x for x in polygon['coordinates'][0]])
    polygon_coords = [x['coordinates'] for x in polygon_coords]

    poly_shape = Polygon(polygon_coords)

    records = util.read_records(points_file, 'crash')

    outside = []
    for record in records:
        if not poly_shape.contains(record.point):
            outside.append(record.point)
    outside_rate = len(outside)/len(records)

    if outside_rate > .01 and outside_rate < max_percent:
        print("{}% of crashes fell outside the city polygon".format(
            int(round(outside_rate, 2)*100)
        ))
        poly_shape = buffer_polygon(poly_shape, outside)

        # Convert back to 4326 projection
        coords = util.reproject(poly_shape.exterior.coords, transformer_3857_to_4326)
        coords = [x['coordinates'] for x in coords]

        poly_shape = Polygon(coords)

        return poly_shape

    # If almost no points fall outside the polygon, no need to buffer,
    # and if a large proportion of points fall outside the polygon,
    # the crash data might be for a larger area than just the city
    return None


def buffer_polygon(polygon, points):
    """
    Given a set of points outside a polygon, expand the polygon
    to include points within 250 meters
    Args:
        polygon - shapely polygon
        points - list of shapely points
    Returns:
        new polygon with buffered points added
    """
    not_close = []
    add_buffers = []

    poly_ext = LinearRing(polygon.exterior.coords)
    for point in points:
        # Find the distance between the point and the city polygon
        dist = polygon.distance(point)
        if dist > 250:
            not_close.append(point)
        else:
            # Create a line between the polygon and the point,
            # and buffer it
            point2 = poly_ext.interpolate(poly_ext.project(point))
            line = LineString([(point.x, point.y), (point2.x, point2.y)])
            buff = line.buffer(50)
            add_buffers.append(buff)
    for buff in add_buffers:
        polygon = polygon.union(buff)
    if not_close:
        print("{} crashes fell outside the buffered city polygon".format(
            len(not_close)
        ))
    else:
        print("Expanded city polygon to include all crash locations")
    return polygon


def get_graph(config):
    """
    Use osmnx to get a graph for a city according to shape type
    specified in config object
    Args:
        config object
    Returns:
        osmnx graph object
    """

    if config.map_geography == 'shapefile':
        print("Reading from shape file")
        # Read in boundary shapefile and convert it to 4326 projection
        polygons = geopandas.read_file(os.path.join(
            RAW_FP, 'maps', config.boundary_shapefile))
        polygons = polygons.to_crs({'init': 'epsg:4326'})
        # Add an arbitrary column to group by
        polygons['groupby'] = 0
        combined_polys = polygons.dissolve(by='groupby')
        poly = combined_polys.geometry[0]
        print("graphing from polygon")
        G1 = ox.graph_from_polygon(poly, network_type='drive',
                                   simplify=False)
        print("finished graphing from polygon")
        return G1
        
    # confirm if a polygon is available for this city, which determines which
    # graph function is appropriate
    print("searching nominatim for " + str(config.city) + " polygon")
    polygon_pos, polygon = find_osm_polygon(config.city)

    if polygon_pos is not None and config.map_geography != 'radius':
        # Check to see if polygon needs to be expanded to include other points
        polygon = expand_polygon(polygon, os.path.join(
            STANDARDIZED_FP, 'crashes.json'))

        if not polygon:
            print("city polygon found in OpenStreetMaps at position " +
                  str(polygon_pos) + ", building graph of roads within " +
                  "specified bounds")
            G1 = ox.graph_from_place(config.city, network_type='drive',
                                     simplify=False, which_result=polygon_pos)
        else:
            print("using buffered city polygon")
            G1 = ox.graph_from_polygon(polygon, network_type='drive',
                                       simplify=False)
    else:
        print_string = ""
        if config.map_geography != 'radius':
            print_string = "No city polygon found in OpenStreetMaps, building "
        else:
            print_string = "Building "
        print_string += "graph of roads within {} km of city ({}/{})".format(
              str(config.city_radius),
              str(config.city_latitude),
              str(config.city_longitude))

        G1 = ox.graph_from_point((config.city_latitude,
                                  config.city_longitude),
                                 distance=config.city_radius * 1000,
                                 network_type='drive', simplify=False)
    return G1
    

def simple_get_roads(config, mapfp):
    """
    Use osmnx to get a simplified version of open street maps for the city
    Writes osm_nodes and osm_ways shapefiles to mapfp
    Args:
        config object
    Returns:
        None
        This function creates the following files
           features.geojson - traffic signals, crosswalks and intersections
           osm.gpkg - the simplified road network
           osm_nodes.shp - the intersections and dead ends
    """

    ox.settings.useful_tags_way.append('cycleway')
    G1 = get_graph(config)
    G = ox.simplify_graph(G1)

    # Label endpoints
    streets_per_node = ox.stats.count_streets_per_node(G)
    for node, count in list(streets_per_node.items()):
        if count <= 1:
            G.nodes()[node]['dead_end'] = True
            G1.nodes()[node]['dead_end'] = True

    # osmnx creates a directory for the nodes and edges
    # Store all nodes, since they can be other features

    # Get relevant node features out of the unsimplified graph
    nodes, data = zip(*G1.nodes(data=True))
    gdf_nodes = geopandas.GeoDataFrame(list(data), index=nodes)
    node_feats = gdf_nodes[gdf_nodes['highway'].isin(
        ['crossing', 'traffic_signals'])]
    intersections = gdf_nodes[gdf_nodes['dead_end'] == True]

    names = {'traffic_signals': 'signal', 'crossing': 'crosswalk'}
    features = []
    for _, row in node_feats.iterrows():
        features.append(geojson.Feature(
            geometry=geojson.Point((row['x'], row['y'])),
            id=row.name,
            properties={'feature': names[row['highway']]},
        ))
    for _, row in intersections.iterrows():
        features.append(geojson.Feature(
            geometry=geojson.Point((row['x'], row['y'])),
            id=row.name,
            properties={'feature': 'intersection'},
        ))

    features = geojson.FeatureCollection(features)

    with open(os.path.join(mapfp, 'features.geojson'), "w") as f:
        json.dump(features, f)

    # Store simplified network
    # seems to be an error with inserting osmid that hasn't been fixed yet
    for node, data in G.nodes(data=True):
        if 'osmid' in data:
            data['osmid_original'] = data.pop('osmid')
    # TODO: apparently you can't specify overwrite to this function
    gpkg_path = os.path.join(mapfp, 'osm.gpkg')
    if os.path.exists(gpkg_path):
        os.remove(gpkg_path)
    ox.save_graph_geopackage(
        G, filepath=os.path.join(mapfp, 'osm.gpkg'))


def clean_and_write(osm_graph_file,
                    result_file, DOC_FP):
    """
    Takes several shape files in 4326 projection, created from osmnx,
    reprojects them, and calls write_geojson
    Args:
        osm_graph_file - osm gpkg with node and edge layers
        result_file - file to write to
        DOC_FP - file to write highway keys to
    Returns:
        None, writes a geojson file
    """
    cleaned_ways = clean_ways(osm_graph_file, DOC_FP)

    nodes = fiona.open(osm_graph_file, layer='nodes')
    nodes, cleaned_ways = get_connections(cleaned_ways, nodes)

    write_geojson(cleaned_ways, nodes,
                  result_file)


def get_connections(ways, nodes):
    """
    Populate the cross streets for each node,
    and add unique ids to the ways
    Args:
        ways - a list of geojson linestrings
        nodes - a list of geojson points
    Returns:
        nodes - a dict containing the roads connected to each node
        ways - the ways, with a unique osmid-fromnode-to-node string
    """
    node_info = {}
    for way in ways:
        # There are some collector roads and others that don't
        # have names. Skip these
        if way['properties']['name']:

            # While we are still merging segments with different names,
            # just use both roads. This should be revisited
            if '[' in way['properties']['name']:
                way['properties']['name'] = re.sub(
                    r'[^\s\w,]|_', '', way['properties']['name'])
                way['properties']['name'] = "/".join(
                    way['properties']['name'].split(', '))

            if way['properties']['from'] not in node_info.keys():
                node_info[way['properties']['from']] = []
            node_info[way['properties']['from']].append(
                way['properties']['name'])

            if way['properties']['to'] not in node_info.keys():
                node_info[way['properties']['to']] = []
            node_info[way['properties']['to']].append(
                way['properties']['name'])

        ident = str(way['properties']['osmid']) + '-' \
            + str(way['properties']['from']) + '-' \
            + str(way['properties']['to'])
        way['properties']['segment_id'] = ident

    nodes_with_streets = []
    for node in nodes:
        if node['properties']['osmid'] in node_info:
            node['properties']['streets'] = ', '.join(
                set(node_info[node['properties']['osmid']]))
        else:
            node['properties']['streets'] = ''
        nodes_with_streets.append(node)
    return nodes_with_streets, ways


def write_keys(DOC_FP, name, keys):
    """
    Since we're creating numeric keys, we'd like to know what
    the numbers correspond to, so write to file the mapping from key
    to open street map features that are strings
    Args:
        DOC_FP - the directory to write the file
        keys - a dict associating key with string type
    """
    # Write highway keys to docs if needed for reference
    if not os.path.exists(DOC_FP):
        os.makedirs(DOC_FP)
    with open(os.path.join(DOC_FP, name + '_keys.csv'), 'w') as f:
        w = csv.writer(f)
        w.writerow(['type', 'value'])
        for item in keys.items():
            w.writerow(item)


def get_width(width):
    """
    Parse the width from the openstreetmap width property field
    Args:
        width - a string
    Returns:
        width - an int
    """

    # This indicates two segments combined together.
    # For now, we just skip combined segments with different widths
    if not width or ';' in width or '[' in width:
        width = 0
    else:
        # Sometimes there's bad (non-numeric) width
        # so remove anything that isn't a number or .
        # Skip those that don't have some number in them
        width = re.sub(r'[^0-9\.]+', '', width)
        if width:
            width = round(float(width))
        else:
            width = 0
    return width


def get_speed(speed):
    """
    Parse the speed from the openstreetmap maxspeed property field
    If there's more than one speed (from merged ways), use the highest speed
    Args:
        speed - a string
    Returns:
        speed - an int
    """
    if speed:
        speeds = [int(x) for x in re.findall(r'\d+', speed)]
        if speeds:
            return max(speeds)
    return 0


def clean_ways(orig_file, DOC_FP):
    """
    Reads in osm gpkg file, cleans up the features, and reprojects
    results into 3857 projection
    Additionally writes a key which shows the correspondence between
    highway type/cycleway type as a string and the resulting int feature
    This can be used to map the int values back to the features, output as csvs
    Features:
        width
        lanes
        hwy_type
        osm_speed
        signal
    Args:
        orig_file: Filename for original file
        result_file: Filename for resulting file in 3857 projection
        DOC_FP: directory to write highway keys file to
    Returns:
        a list of reprojected way lines
    """

    way_lines = fiona.open(orig_file, layer='edges')

    highway_keys = {None: 0}
    cycleway_keys = {}
    results = []

    for way_line in way_lines:

        speed = get_speed(way_line['properties']['maxspeed']) \
            if 'maxspeed' in list(way_line['properties']) else 0
        width = get_width(way_line['properties']['width']) \
            if 'width' in list(way_line['properties']) else 0

        lanes = way_line['properties']['lanes']
        if lanes:
            lanes = max([int(x) for x in re.findall(r'\d', lanes)])
        else:
            lanes = 0

        # All fields need to be int
        # Make dicts for the fields that aren't to track the value
        # Write these to file for lookup
        if way_line['properties']['highway'] not in list(highway_keys.keys()):
            highway_keys[way_line['properties']['highway']] = len(highway_keys)
        if 'cycleway' in way_line['properties'] and \
           way_line['properties']['cycleway'] and \
           way_line['properties']['cycleway'] not in list(cycleway_keys.keys()):
            cycleway_keys[way_line['properties']['cycleway']] = len(cycleway_keys)

        # Width per lane
        width_per_lane = 0
        if lanes and width:
            width_per_lane = round(width/lanes)

        # Use oneway
        oneway = 0
        if way_line['properties']['oneway'] == 'True':
            oneway = 1

        way_line['properties'].update({
            'width': width,
            'lanes': int(lanes),
            'hwy_type': highway_keys[way_line['properties']['highway']],
            'cycleway_type': cycleway_keys[way_line['properties']['cycleway']]
                if 'cycleway' in way_line['properties'] and \
                    way_line['properties']['cycleway']
                else 0,
            'osm_speed': speed,
            'signal': 0,
            'oneway': oneway,
            'width_per_lane': width_per_lane
        })
        results.append(way_line)

    write_keys(DOC_FP, 'highway', highway_keys)
    write_keys(DOC_FP, 'cycleway', cycleway_keys)
    return results


def write_geojson(way_results, node_results, outfp):
    """
    Given a list of ways, intersection nodes, and all nodes, write them
    out to a geojson file.
    """
    feats = way_results

    for node in node_results:
        if not node['properties']['dead_end']:
            node['properties']['intersection'] = 1
        if node['properties']['highway'] == 'traffic_signals':
            node['properties']['signal'] = 1
        feats.append(geojson.Feature(
            geometry=geojson.Point(node['geometry']['coordinates']),
            properties=OrderedDict(node['properties']))
        )

    feat_collection = geojson.FeatureCollection(feats)
    with open(outfp, 'w') as outfile:
        geojson.dump(feat_collection, outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Config file")
    parser.add_argument("-d", "--datadir", type=str, required=True,
                        help="Data directory")
    # Can force update
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()

    config = data.config.Configuration(args.config)
    MAP_FP = os.path.join(args.datadir, 'processed/maps')
    DOC_FP = os.path.join(args.datadir, 'docs')
    STANDARDIZED_FP = os.path.join(args.datadir, 'standardized')
    RAW_FP = os.path.join(args.datadir, 'raw')

    # If maps do not exist, create
    if not os.path.exists(os.path.join(MAP_FP, 'osm.gpkg')) \
       or args.forceupdate:
        print('Generating map from open street map...')
        simple_get_roads(config, MAP_FP)

    if not os.path.exists(os.path.join(MAP_FP, 'osm_elements.geojson')) \
       or args.forceupdate:
        print("Cleaning and writing to {}...".format('osm_elements.geojson'))

        clean_and_write(
            os.path.join(MAP_FP, 'osm.gpkg'),
            os.path.join(MAP_FP, 'osm_elements.geojson'),
            DOC_FP
        )

