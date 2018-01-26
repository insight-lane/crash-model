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


def add_match_features(line):
    features = {}
    matching = True
    for m in line['matches']:
        for k, v in m[1].items():
            if k not in features.keys():
                features[k] = v
            elif features[k] != v:
                matching = False
    print matching


def get_mapping(lines):
    """
    Attempts to map one or more segments of the second map to the first map
    Args:
        lines - a list of dicts containing the line from the first map,
            the properties, the candidate overlapping lines from the new map,
            and nearby segments on the original map because we may want to
            combine two for the purposes of mapping
    """
    print len(lines)
    result_counts = [0, 0]
    buff = 5
    while buff <= 20:
        print "Looking at buffer " + str(buff)
        for i in range(len(lines)):
            util.track(i, 1000, len(lines))
            if 'matches' in lines[i].keys():
                continue

            matched_candidates = []

            for candidate in lines[i]['candidates']:
                match = True

                for coord in candidate[0].coords:
                    if not Point(coord).within(lines[i]['line'].buffer(buff)):
                        match = False
                if match:
                    matched_candidates.append(candidate)

            if matched_candidates:
                lines[i]['matches'] = matched_candidates

        buff *= 2
    
    # Now go through the lines that still aren't matched
    # this time, see if they are a subset of any of their candidates
    for i in range(len(lines)):
        matched_candidates = []
        if 'matches' in lines[i].keys():
            continue
        for candidate in lines[i]['candidates']:
            match = True
            for coord in lines[i]['line'].coords:
                if not Point(coord).within(candidate[0].buffer(20)):
                    match = False
            if match:
                matched_candidates.append(candidate)
        if matched_candidates:
            lines[i]['matches'] = matched_candidates

    orig = []
    matched = []
    for i, line in enumerate(lines):
        if 'matches' in line.keys():
            result_counts[0] += 1
            
            orig.append((line['line'], line['properties']))

            # Every single match for this line
            add_match_features(line)

            # Add each matching line
            # Only used for debugging purposes, take out eventually
            for m in line['matches']:
                matched.append((m[0], m[1]))

        else:
            result_counts[1] += 1

    write_test(
        lines[0]['properties'],
        'LineString',
        orig,
        'orig.shp'
    )
    write_test(
        lines[0]['matches'][0][1],
        'LineString',
        matched,
        'matches.shp'
    )
#        write_test(
#            line['properties'],
#            'Polygon',
#            [(line['line'].buffer(5), line['properties'])],
#            'buffered.shp'
#        )

    percent_matched = float(result_counts[0])/(
        float(result_counts[0]+result_counts[1])) * 100
    print 'Found matches for ' + str(percent_matched) + '% of segments'
    print result_counts


def get_candidates(buffered, buffered_index, lines):

    results = []

    print "Getting candidate overlapping lines"

    # Go through each line from the osm map
    for i, line in enumerate(lines):
        overlapping = []
        util.track(i, 1000, len(lines))

        # First, get candidates from new map that overlap the buffer
        # from the original map
        for idx in buffered_index.intersection(line[0].bounds):
            buffer = buffered[idx][0]

            # If the new line overlaps the old line
            # then check whether it is entirely within the old buffer
            if buffer.intersects(line[0]):

                # Add the linestring and the features to the overlap list
                overlapping.append((buffered[idx][1], buffered[idx][2]))

        results.append({
            'line': line[0],
            'properties': line[1],
            'candidates': overlapping,
        })

    return results


if __name__ == '__main__':
    # Read osm map file
    parser = argparse.ArgumentParser()

    # Both maps should be in 3857 projection
    parser.add_argument("map1", help="Map generated from open street map")
    parser.add_argument("map2", help="City specific map")

    args = parser.parse_args()
    
    orig_map = util.read_shp(args.map1)

    orig_map = [x for x in orig_map if x[1]['name'] == 'Columbia Road']
    new_map = util.read_shp(args.map2)

    # Index for the new map
    new_buffered = []
    new_index = rtree.index.Index()

    new_map = [x for x in new_map if x[1]['ST_NAME'] in (
        'Columbia', 'Devon', 'Stanwood')]

    # Buffer all the new lines
    for idx, new_line in enumerate(new_map):
        b = new_line[0].buffer(20)
        new_buffered.append((b, new_line[0], new_line[1]))
        new_index.insert(idx, new_line[0].buffer(20).bounds)

    lines_with_candidates = get_candidates(
        new_buffered, new_index, orig_map)
    get_mapping(lines_with_candidates)



    


