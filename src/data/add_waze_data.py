import argparse
from . import util
import os
import json
import geojson
from collections import defaultdict


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


def get_linestring(value):
    line = value['line']
    coords = [(x['x'], x['y']) for x in line]
    return geojson.Feature(
        geometry=geojson.LineString(coords),
        properties=value
    )


def map_segments(datadir, filename):

    items = json.load(open(filename))
    items = [get_linestring(x) for x in items]
    items = util.reproject_records(items)
    # Get the total number of snapshots in the waze data
    num_snapshots = max([x['properties']['snapshotId'] for x in items])

    road_segments, _ = util.get_roads_and_inters(os.path.join(
        datadir,
        'processed',
        'maps',
        'osm_elements.geojson'
    ))
    roads, roads_index = util.index_segments(
        road_segments, geojson=True, segment=True)
    road_buffers = []
    for road in roads:
        road_buffers.append(road[0].buffer(3))

    print("read in {} road segments".format(len(roads)))

    waze_info = defaultdict(list)
    count = 0
    for item in items:
        count += 1
        if item['properties']['eventType'] == 'jam':
            for idx in roads_index.intersection(item['geometry'].bounds):
                segment = roads[idx]
                buff = road_buffers[idx]
                overlap = buff.intersection(item['geometry'])

                if not overlap.length or \
                   (overlap.length < 20 and segment[0].length > 20):
                    # Skip segments with no overlap
                    # or very short overlaps
                    continue
                waze_info[segment[1]['segment_id']].append(item)

    # Add waze features
    # Also convert into format that util.prepare_geojson is expecting
    updated_roads = []
    for road in road_segments:
        properties = road.properties
        if properties['segment_id'] in waze_info:
            num_jams = len(waze_info[properties['segment_id']])
        else:
            num_jams = 0
        properties.update(jam_percent=num_jams/num_snapshots)
        updated_roads.append(
            {'geometry': road.geometry, 'properties': properties})

    # Look at alerts that are crashes, maybe ignore those jams?


def make_map(filename, datadir):

    items = json.load(open(filename))
    geojson_items = []
    for item in items:
        geojson_items.append(get_linestring(item))
    with open(os.path.join(datadir, 'waze.geojson'), 'w') as outfile:
        geojson.dump(geojson.FeatureCollection(geojson_items), outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--datadir", type=str,
                        help="data directory")

    args = parser.parse_args()

    infile = os.path.join(args.datadir, 'standardized', 'waze.json')
#    make_map(infile, os.path.join(args.datadir, 'processed', 'maps'))
    map_segments(args.datadir, infile)
