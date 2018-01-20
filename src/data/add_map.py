import argparse
import util
from shapely.geometry import Point


def find_overlap(buffered, orig_map):
    # for road in orig_map

    overlapping = []
    for old_segment in orig_map:
        match = True
        for coord in old_segment[0].coords:
            if not Point(coord).within(buffered[0]):
                match = False
        if match:
#            import ipdb; ipdb.set_trace()

            overlapping.append(old_segment)

    # write a points file for debugging
    points = []
    for over in overlapping:
        for coord in over[0].coords:
            points.append((Point(coord), {
                'lat': str(coord[0]), 'long': str(coord[1])
            }))
    schema = {
        'geometry': 'Point',
        'properties': {
            'lat': 'str',
            'long': 'str',
        }
    }
    util.write_shp(
        schema,
        '/home/jenny/boston-crash-modeling/osm-data/processed/maps/overlap_points.shp',
        points, 0, 1)
#    import ipdb; ipdb.set_trace()

    return overlapping

if __name__ == '__main__':
    # Read osm map file
    parser = argparse.ArgumentParser()

    # Both maps should be in 3857 projection
    parser.add_argument("map1", help="Map generated from open street map")
    parser.add_argument("map2", help="City specific map")

    args = parser.parse_args()
    
    orig_map = util.read_shp(args.map1)
    new_map = util.read_shp(args.map2)
    keys = orig_map[0][1].keys() + new_map[0][1].keys()
    properties = {k: 'str' for k in keys}
    schema = {
        'geometry': 'LineString',
        'properties': properties
    }

    final = []
    new_lines = []
    new_lines_buffered = []
    for line in new_map:
        if line[1]['ST_NAME'] == 'Gold':
            new_lines.append(line)
            b = line[0].buffer(20)
            new_lines_buffered.append((b, line[1]))

    path = '/home/jenny/boston-crash-modeling/osm-data/processed/maps/'
    util.write_shp(
        schema,
        path + 'gold.shp',
        new_lines, 0, 1)

    other_schema = schema.copy()
    other_schema['geometry'] = 'Polygon'
    util.write_shp(
        other_schema,
        path + 'buffered.shp',
        new_lines_buffered, 0, 1)

    for i in range(1):
        results = find_overlap(new_lines_buffered[i], orig_map)
#        import ipdb; ipdb.set_trace()

        for v in results:
            final.append(v)
#        final.append(new_map[i])
    print len(final)
    util.write_shp(
        schema,
        '/home/jenny/boston-crash-modeling/osm-data/processed/maps/overlap.shp',
        final, 0, 1)



    


