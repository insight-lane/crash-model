import argparse
import util
import osmnx as ox
import fiona
import shutil
import os
import re
import csv

MAP_FP = None


def simple_get_roads(city):
    """
    Use osmnx to get a simplified version of open street maps for the city
    Writes osm_nodes and osm_ways shapefiles to MAP_FP
    Args:
        city
    Returns:
        None
    """

    G1 = ox.graph_from_place(city, network_type='drive', simplify=False)
    G = ox.simplify_graph(G1)

    # Label endpoints
    streets_per_node = ox.count_streets_per_node(G)
    for node, count in streets_per_node.items():
        if count <= 1:
            G.nodes()[node]['dead_end'] = True

    # osmnx creates a directory for the nodes and edges
    # Store all nodes, since they can be other features
    ox.save_graph_shapefile(
        G, filename='all_nodes', folder=MAP_FP)

    # Store simplified network
    ox.save_graph_shapefile(
        G, filename='temp', folder=MAP_FP)

    # Copy and remove temp directory
    tempdir = os.path.join(MAP_FP, 'temp')
    for filename in os.listdir(os.path.join(tempdir, 'edges')):
        name, extension = filename.split('.')
        shutil.move(os.path.join(tempdir, 'edges', filename),
                    os.path.join(MAP_FP, 'osm_ways.' + extension))
    for filename in os.listdir(os.path.join(tempdir, 'nodes')):
        name, extension = filename.split('.')
        shutil.move(os.path.join(tempdir, 'nodes', filename),
                    os.path.join(MAP_FP, 'osm_nodes.' + extension))
    shutil.rmtree(tempdir)


def get_signals():
    nodes = util.read_shp(
        os.path.join(MAP_FP, 'all_nodes', 'nodes', 'nodes.shp'))
    signals = [
        node for node in nodes if node[1]['highway'] == 'traffic_signals'
    ]
    schema = {
        'geometry': 'Point',
        'properties': {
            'highway': 'str',
            'osmid': 'str',
            'ref': 'str'
        }
    }
    util.write_shp(
        schema,
        os.path.join(MAP_FP, 'osm_signals.shp'),
        signals, 0, 1, crs=fiona.crs.from_epsg(3857))


def reproject_and_clean_feats(orig_file, result_file, DOC_FP):
    """
    Reads in osm_ways file, cleans up the features, and reprojects
    results into 3857 projection
    Additionally writes a key which shows the correspondence between
    highway type as a string and the resulting int feature
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
        None, writes to file
    """

    way_results = fiona.open(orig_file)

    # Convert the map from above to 3857
    reprojected_way_lines = [
        tuple(
            x.values()
        ) for x in util.reproject_records(way_results)]

    highway_keys = {}
    for way_line in reprojected_way_lines:
        # All features need to be ints, so convert them here

        # Use speed limit if given in osm
        speed = way_line[1]['maxspeed']
        if speed:
            s = re.search('[0-9]+', speed)
            if s:
                speed = s.group(0)
        if not speed:
            speed = 0

        # round width
        width = 0
        if ['width'] in way_line[1].keys():
            width = way_line[1]['width']
            if not width or ';' in width or '[' in width:
                width = 0
            else:
                width = round(float(width))

        lanes = way_line[1]['lanes']
        if lanes:
            lanes = max([int(x) for x in re.findall('\d', lanes)])
        else:
            lanes = 0

        # Need to have an int highway field
        if way_line[1]['highway'] not in highway_keys.keys():
            highway_keys[way_line[1]['highway']] = len(highway_keys)

        # Use oneway
        oneway = 0
        if way_line[1]['oneway'] == 'True':
            oneway = 1

        way_line[1].update({
            'width': width,
            'lanes': int(lanes),
            'hwy_type': highway_keys[way_line[1]['highway']],
            'osm_speed': speed,
            'signal': 0,
            'oneway': oneway
        })
    schema = way_results.schema

    # Add values to schema if they don't exist, so new map won't break
    schema['properties'].update({
        # Add highway type key and osm_speed to the schema
        'width': 'int',
        'lanes': 'int',
        'hwy_type': 'int',
        'osm_speed': 'int',
        'signal': 'int',
        'oneway': 'int',
    })

    util.write_shp(
        schema,
        result_file,
        reprojected_way_lines, 0, 1, crs=fiona.crs.from_epsg(3857))

    # Write highway keys to docs if needed for reference
    if not os.path.exists(DOC_FP):
        os.makedirs(DOC_FP)
    with open(os.path.join(DOC_FP, 'highway_keys.csv'), 'wb') as f:
        w = csv.writer(f)
        w.writerow(['type', 'value'])
        for item in highway_keys.iteritems():
            w.writerow(item)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("city", help="e.g. 'Boston, Massachusetts, USA'")

    # Right now, you must also give data directory
    parser.add_argument("datadir", type=str,
                        help="data directory")

    # Can force update
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')

    args = parser.parse_args()
    city = args.city

    MAP_FP = os.path.join(args.datadir, 'processed/maps')
    DOC_FP = os.path.join(args.datadir, 'docs')

    # If maps do not exist, create
    if not os.path.exists(os.path.join(MAP_FP, 'osm_ways.shp')) \
       or args.forceupdate:
        print 'Generating map from open street map...'
        simple_get_roads(city)

    if not os.path.exists(os.path.join(MAP_FP, 'osm_signals.shp')):
        get_signals()

    if not os.path.exists(os.path.join(MAP_FP, 'osm_ways_3857.shp')) \
       or args.forceupdate:
        print "Reprojecting..."
        reproject_and_clean_feats(
            os.path.join(MAP_FP, 'osm_ways.shp'),
            os.path.join(MAP_FP, 'osm_ways_3857.shp'),
            DOC_FP
        )
