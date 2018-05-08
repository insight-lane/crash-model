import argparse
import util
import osmnx as ox
import fiona
import shutil
import os
import re
import csv
import geojson


MAP_FP = None


def simple_get_roads(city):
    """
    Use osmnx to get a simplified version of open street maps for the city
    Writes osm_nodes and osm_ways shapefiles to MAP_FP
    Args:
        city
    Returns:
        None, but creates the following shape files:
           osm_ways.shp - the simplified road network
           osm_nodes.shp - the intersections and dead ends
        And creates the following directory:
           all_nodes - containing edges and nodes directories
               for the unsimplified road network
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
        G1, filename='all_nodes', folder=MAP_FP)

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


def reproject_and_write(ways_file, nodes_file, all_nodes_file,
                        result_file, DOC_FP):
    """
    Takes several shape files in 4326 projection, created from osmnx,
    reprojects them, and calls write_geojson
    Args:
        ways_file - shp file for the ways
        nodes_file - shp file for the intersection and end nodes
        all_nodes_file - shp file for ALL nodes in the road network
        result_file - file to write to
        DOC_FP - file to write highway keys to
    Returns:
        None, writes a geojson file
    """
    reprojected_ways = clean_and_reproject_ways(ways_file, DOC_FP)
    f = fiona.open(nodes_file)
    reprojected_nodes = util.reproject_records(f)
    f = fiona.open(all_nodes_file)
    reprojected_all_nodes = util.reproject_records(f)
    write_geojson(reprojected_ways, reprojected_nodes,
                  reprojected_all_nodes, result_file)


def write_highway_keys(DOC_FP, highway_keys):
    """
    Since we're creating a numeric highway key, we'd like to know what
    the numbers correspond to, so write to file the mapping from key
    to open street map highway type
    Args:
        DOC_FP - the directory to write the file
        highway_keys - a dict associating key with string type
    """
    # Write highway keys to docs if needed for reference
    if not os.path.exists(DOC_FP):
        os.makedirs(DOC_FP)
    with open(os.path.join(DOC_FP, 'highway_keys.csv'), 'wb') as f:
        w = csv.writer(f)
        w.writerow(['type', 'value'])
        for item in highway_keys.iteritems():
            w.writerow(item)


def clean_and_reproject_ways(orig_file, DOC_FP):
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
        a list of reprojected way lines
    """

    f = fiona.open(orig_file)
    reprojected_way_lines = util.reproject_records(f)
    highway_keys = {}
    for way_line in reprojected_way_lines:
        # All features need to be ints, so convert them here

        # Use speed limit if given in osm
        speed = way_line['properties']['maxspeed']
        if speed:
            s = re.search('[0-9]+', speed)
            if s:
                speed = s.group(0)
        if not speed:
            speed = 0

        # round width
        width = 0
        if ['width'] in way_line['properties'].keys():
            width = way_line['properties']['width']
            if not width or ';' in width or '[' in width:
                width = 0
            else:
                width = round(float(width))

        lanes = way_line['properties']['lanes']
        if lanes:
            lanes = max([int(x) for x in re.findall('\d', lanes)])
        else:
            lanes = 0

        # Need to have an int highway field
        if way_line['properties']['highway'] not in highway_keys.keys():
            highway_keys[way_line['properties']['highway']] = len(highway_keys)

        # Use oneway
        oneway = 0
        if way_line['properties']['oneway'] == 'True':
            oneway = 1

        way_line['properties'].update({
            'width': width,
            'lanes': int(lanes),
            'hwy_type': highway_keys[way_line['properties']['highway']],
            'osm_speed': speed,
            'signal': 0,
            'oneway': oneway
        })

    write_highway_keys(DOC_FP, highway_keys)
    return reprojected_way_lines


def write_geojson(way_results, node_results, all_node_results, outfp):
    """
    Given a list of 
    """
    feats = []

    # Add the ways
    for way_result in way_results:
        feats.append({
            'type': 'Feature',
            'geometry': {
                'type': way_result['geometry'].type,
                'coordinates': [x for x in way_result['geometry'].coords]
            },
            'properties': way_result['properties']
        })

    # Add the nodes, in a dict, ordered by id
    node_dict = {}
    for node in node_results:
        if not node['properties']['dead_end']:
            node['properties']['intersection'] = 1
        if node['properties']['highway'] == 'traffic_signals':
            node['properties']['signal'] = 1

        node_dict[node['properties']['osmid']] = {
            'type': 'Feature',
            'geometry': {
                'type': node['geometry']['type'],
                'coordinates': node['geometry']['coordinates']
            },
            'properties': node['properties']
        }

    non_int_nodes = [x for x in all_node_results
                     if x['properties']['osmid'] not in node_dict.keys()]

    # Go through the rest of the nodes, and add any of them that have
    # (hardcoded) open street map features that we care about
    # For the moment, all_nodes only contains street nodes, so we'll
    # only look at crosswalks
    for node in non_int_nodes:
        add_node = False
        if node['properties']['highway'] == 'crossing':
            node['properties']['crossing'] = 1
            add_node = True
        elif node['properties']['highway'] == 'traffic_signals':
            node['properties']['traffic_signals'] = 1
            add_node = True
        if add_node:
            node_dict[node['properties']['osmid']] = {
                'type': 'Feature',
                'geometry': {
                    'type': node['geometry']['type'],
                    'coordinates': node['geometry']['coordinates']
                },
                'properties': node['properties']
            }

    # Add node features to the way features
    feats = feats + node_dict.values()
    with open(outfp, 'w') as outfile:
        geojson.dump({
            'type': 'FeatureCollection',
            'features': feats
        }, outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("city", help="e.g. 'Boston, Massachusetts, USA'")

    # Directory where the city's data is stored
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

    if not os.path.exists(os.path.join(MAP_FP, 'osm_elements.geojson')) \
       or args.forceupdate:
        print "Reprojecting and writing to {}...".format('osm_elements.geojson')

        reproject_and_write(
            os.path.join(MAP_FP, 'osm_ways.shp'),
            os.path.join(MAP_FP, 'osm_nodes.shp'),
            os.path.join(MAP_FP, 'all_nodes', 'nodes', 'nodes.shp'),
            os.path.join(MAP_FP, 'osm_ways.geojson'),
            DOC_FP
        )

