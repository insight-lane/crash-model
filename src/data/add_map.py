import argparse
import util
from shapely.geometry import Point
import rtree
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = BASE_DIR + '/osm-data/processed/maps/'


def write_test(props, geometry, values, filename):
    keys = props.keys()
    properties = {k: 'str' for k in keys}
    schema = {
        'geometry': geometry,
        'properties': properties
    }
    print filename
    util.write_shp(
        schema,
        MAP_FP + filename,
        values, 0, 1)


# right now called with new_buffered, new_index, orig_map
def get_candidates(buffered, buffered_index, lines):

    results = []

    overlapping_buffers = []

    # Go through each line from the osm map
    for i, line in enumerate(lines):
        overlapping = []
        if i == 0:
            util.track(i, 1000, len(lines))
            for idx in buffered_index.intersection(line[0].bounds):
                buffer = buffered[idx][0]
#                import ipdb; ipdb.set_trace()

                # If the new line overlaps the old line
                # then check whether it is entirely within the old buffer
                if buffer.intersects(line[0]):
                    overlapping.append(buffered[idx][1])
                    overlapping_buffers.append([buffer, line[1]])
            # write original map's line for testing
            write_test(lines[0][1], 'LineString', [line], 'first')
            results.append({
                'line': line[0],
                'properties': line[1],
                'candidates': overlapping,
            })
#    write_test(lines[0][1], 'LineString', overlapping, 'testlines')
#    write_test(lines[0][1], 'Polygon', overlapping_buffers, 'testbuffer')
#    import ipdb; ipdb.set_trace()

    # just for testing purposes write out the first result
    output = [(x, lines[0][1]) for x in results[0]['candidates']]

    write_test(lines[0][1], 'LineString', output, 'testlines')
    return overlapping


def find_overlap(buffered, new_map, index):
    # for road in orig_map

    overlapping = []

#        for idx in int_buffers_index.intersection(road[0].bounds):
#            int_buffer = int_buffers[idx]

    for i, new_segment in enumerate(new_map):
        util.track(i, 1000, len(new_map))
        import ipdb; ipdb.set_trace()

        for idx in index.intersection(buffered[0]):
            new_match = index[idx]
            
            match = True
            for coord in new_segment[0].coords:
                if not Point(coord).within(buffered[0]):
                    match = False
            if match:
#            import ipdb; ipdb.set_trace()

                overlapping.append(new_segment)

    # write a points file for debugging
#    points = []
#    for over in overlapping:
#        for coord in over[0].coords:
#            points.append((Point(coord), {
#                'lat': str(coord[0]), 'long': str(coord[1])
#            }))
#    schema = {
#        'geometry': 'Point',
#        'properties': {
#            'lat': 'str',
#            'long': 'str',
#        }
#    }
#    util.write_shp(
#        schema,
#        '/home/jenny/boston-crash-modeling/osm-data/processed/maps/overlap_points.shp',
#        points, 0, 1)
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
#    new_lines = []
#    new_lines_buffered = []
    orig_lines = []
    orig_lines_buffered = []

    # Buffer all the original lines
    orig_map = [x for x in orig_map if x[1]['name'] == 'Columbia Road']
    buffers_index = rtree.index.Index()
    for idx, line in enumerate(orig_map):
        util.track(idx, 1000, len(orig_map))
        orig_lines.append(line)
        b = line[0].buffer(20)
        orig_lines_buffered.append((b, line[1]))
        buffers_index.insert(idx, b.bounds)

    # Index for the new map
    new_buffered = []
    new_index = rtree.index.Index()
#    print 'indexing.........'

    # Buffer all the new lines
    new_map = [x for x in new_map if x[1]['ST_NAME'] in (
        'Columbia', 'Devon', 'Stanwood')]

    for idx, new_line in enumerate(new_map):
        b = new_line[0].buffer(20)
        new_buffered.append((b, new_line[0], new_line[1]))
        new_index.insert(idx, new_line[0].buffer(20).bounds)

#    print 'done indexing.....'


#    final = get_candidates(orig_lines_buffered, buffers_index, new_map)
    final = get_candidates(new_buffered, new_index, orig_map)


    path = '/home/jenny/boston-crash-modeling/osm-data/processed/maps/'
#    util.write_shp(
#        schema,
#        path + 'gold.shp',
#        orig_lines, 0, 1)

#    other_schema = schema.copy()
#    other_schema['geometry'] = 'Polygon'
#    util.write_shp(
#        other_schema,
#        path + 'buffered.shp',
#        orig_lines_buffered, 0, 1)

#    print 'ready to enumerate....'
#    for i in range(len(new_lines_buffered)):
#    for i, line in enumerate(orig_lines_buffered):
#        print i
#        util.track(i, 1000, len(orig_lines_buffered))
#        results = find_overlap(line, new_map, index)
#        import ipdb; ipdb.set_trace()

#        for v in results:
#            final.append(v)
#        final.append(new_map[i])
    print len(final)
#    util.write_shp(
#        schema,
#        '/home/jenny/boston-crash-modeling/osm-data/processed/maps/overlap.shp',
#        final, 0, 1)



    


