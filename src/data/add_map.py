import argparse
import util
from shapely.ops import unary_union
from shapely.geometry import Point
import rtree
import os
import json

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

PROCESSED_DATA_FP = None
MAP_FP = None


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


def add_match_features(line, features):

    features = {}
    unmatching_feats = []
    feats_list = {}
    for m in line['matches']:
        for k, v in m[1].items():
            if k in features:

                if k not in feats_list:
                    feats_list[k] = []
                if v:
                    feats_list[k].append(v)
                    if k not in features.keys():
                        features[k] = v
                    elif features[k] != v:
                        if k not in unmatching_feats:
                            unmatching_feats.append(k)

#    if not matching:
#        orig = [(line['line'], line['properties'])]
#        write_test(
#            line['properties'],
#            'LineString',
#            orig,
#            'orig.shp'
#        )
#        write_test(
#            line['matches'][0][1],
#            'LineString',
#            line['matches'],
#            'matches.shp'
#        )

    # Add new features to existing ones
    for feat, values in feats_list.items():
        if values and len(set(values)) == 1:
            line['properties'][feat] = values[0]

def get_mapping(lines, features):
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

    # keep track of which new segments matched at which size buffer
    buff_match = {}

    new_id = 0
    while buff <= 20:
        print "Looking at buffer " + str(buff)
        for i in range(len(lines)):
            util.track(i, 1000, len(lines))
            if 'matches' in lines[i].keys():
                continue

            matched_candidates = []

            for j, candidate in enumerate(lines[i]['candidates']):
                if 'id' not in lines[i]['candidates'][j][1].keys():
                    lines[i]['candidates'][j][1]['id'] = new_id
                    new_id += 1
                match = True

                for coord in candidate[0].coords:
                    if not Point(coord).within(lines[i]['line'].buffer(buff)):
                        match = False
                if match:
                    matched_candidates.append((candidate, buff))

                    if lines[i]['candidates'][j][1]['id'] \
                       not in buff_match.keys():
                        buff_match[lines[i]['candidates'][j][1]['id']] = buff

            if matched_candidates:
                lines[i]['matches'] = matched_candidates

        buff *= 2
    
    # Now go through the lines that still aren't matched
    # this time, see if they are a subset of any of their candidates
    for i in range(len(lines)):
        matched_candidates = []
        if 'matches' in lines[i].keys():
            continue
        for j, candidate in enumerate(lines[i]['candidates']):
            if 'id' not in lines[i]['candidates'][j][1].keys():
                lines[i]['candidates'][j][1]['id'] = new_id
                new_id += 1

            match = True
            for coord in lines[i]['line'].coords:
                if not Point(coord).within(candidate[0].buffer(20)):
                    match = False
            if match:
                matched_candidates.append((candidate, 20))
                if lines[i]['candidates'][j][1]['id'] not in buff_match.keys():
                    buff_match[lines[i]['candidates'][j][1]['id']] = buff
        if matched_candidates:
            lines[i]['matches'] = matched_candidates

    # Remove matches that matched better on a different segment
    # But only if there's a match for that segment already
    for i in range(len(lines)):
        if 'matches' in lines[i].keys():
            matches = lines[i]['matches']
            new_matches = []
            for (m, buff) in matches:
                if buff_match[m[1]['id']] == buff:
                    new_matches.append(m)
            if new_matches:
                lines[i]['matches'] = new_matches
            else:
                # Remove buffer info
                lines[i]['matches'] = [m[0] for m in lines[i]['matches']]

    orig = []
    matched = []
    for i, line in enumerate(lines):
        if 'matches' in line.keys() and line['matches']:
            result_counts[0] += 1
            
            orig.append((line['line'], line['properties']))

            # Every single match for this line
            add_match_features(line, features)

            # Add each matching line
            # Only used for debugging purposes, take out eventually
            for m in line['matches']:
                matched.append((m[0], m[1]))

        else:
            result_counts[1] += 1

#        write_test(
#            line['properties'],
#            'LineString',
#            [(line['line'], line['properties'])],
#            'orig.shp'
#        )

    percent_matched = float(result_counts[0])/(
        float(result_counts[0]+result_counts[1])) * 100
    print 'Found matches for ' + str(percent_matched) + '% of segments'

    print result_counts


def get_int_mapping(lines, buffered, buffered_index):

    print "Getting intersection mappings"

    line_results = []
    # Go through each line from the osm map
    for i, line in enumerate(lines):
        util.track(i, 1000, len(lines))
        line_buffer = line[0].buffer(10)

        best_match = {}
        best_overlap = 0
        for idx in buffered_index.intersection(line_buffer.bounds):
            buffer = buffered[idx][0]
            # If the new buffered intersection intersects the old one
            # figure out how much overlap, and take the best one
            if buffer.intersects(line[0]):
                total_area = unary_union([line_buffer, buffer]).area
                overlap = max(
                    line_buffer.area/total_area, buffer.area/total_area)
                
                if overlap > best_overlap and overlap > .20:
                    best_overlap = overlap
                    best_match = buffered[idx][2]

        line_results.append([line[0], line[1], best_match])

    total = len(line_results)
    percent_matched = 100 - 100 * float(
        len([x for x in line_results if not x[2]]))/float(total)
    print "Found matches for " + str(percent_matched) + "% of intersections"
    return line_results


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


def add_int_features(int_lines, dir1, dir2, featlist):

    with open(os.path.join(dir2, 'inters_data.json'), 'r') as f:
        inters_new = json.load(f)
    
    inters_data_fp = os.path.join(dir1, 'inters_data.json')
    with open(inters_data_fp, 'r') as f:
        inters_orig = json.load(f)

    for line in int_lines:
        orig_feats = inters_orig[str(line[1]['id'])]
        if line[2]:
            new_feats = inters_new[str(line[2]['id'])]

            # Since at the moment, the canonical dataset is created by only
            # looking at the max value of each feature, we can just append
            # the max value of the new features to the first segment of the
            # original feature list
            for feat in featlist:
                orig_feats[0][feat] = max([x[feat] for x in new_feats])

    with open(inters_data_fp, 'w') as f:
        json.dump(inters_orig, f)


if __name__ == '__main__':
    # Read osm map file
    parser = argparse.ArgumentParser()

    # Both maps should be in 3857 projection
    parser.add_argument(
        "datadir", help="base data directory containing maps generated from"
        + "open street map")
    parser.add_argument(
        "map2dir", help="directory containing maps generated from"
        + "city specific data")
    parser.add_argument("-features", "--features", nargs="+", default=[
        'AADT', 'SPEEDLIMIT', 'Struct_Cnd', 'Surface_Tp', 'F_F_Class'],
        help="List of segment features to include")

    args = parser.parse_args()
    
    feats = args.features

    PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
    MAP_FP = os.path.join(PROCESSED_DATA_FP, 'maps')

    non_inters_orig_file = os.path.join(
        MAP_FP, 'non_inters_segments.shp')
    print "Reading original map from " + non_inters_orig_file
    orig_map_non_inter = util.read_shp(non_inters_orig_file)

#    orig_map_non_inter = [
#        x for x in orig_map_non_inter if x[1]['name'] == 'Columbia Road']

    non_inters_new_file = os.path.join(
        MAP_FP, args.map2dir, 'non_inters_segments.shp')
    print "Reading new map from " + non_inters_new_file
    new_map_non_inter = util.read_shp(non_inters_new_file)
#    new_map_non_inter = [x for x in new_map_non_inter if x[1]['ST_NAME'] in (
#        'Columbia', 'Devon', 'Stanwood')]

    # Index for the new map
    new_buffered = []
    new_index = rtree.index.Index()

    # Buffer all the new lines
    for idx, new_line in enumerate(new_map_non_inter):
        b = new_line[0].buffer(20)
        new_buffered.append((b, new_line[0], new_line[1]))
        new_index.insert(idx, b.bounds)

    non_ints_with_candidates = get_candidates(
        new_buffered, new_index, orig_map_non_inter)

    print "Adding features: " + ','.join(feats)
    get_mapping(non_ints_with_candidates, feats)

    # Write the non-intersections segments back out with the new features
    schema = {
        'geometry': 'LineString',
        'properties': {k: 'str' for k in orig_map_non_inter[0][1].keys()}
    }
    util.write_shp(
        schema,
        MAP_FP + 'non_inters_segments.shp',
        orig_map_non_inter, 0, 1)

    # Now do intersections
    orig_map_inter = util.read_shp(
        os.path.join(MAP_FP, 'inters_segments.shp'))

    new_map_inter = util.read_shp(
        os.path.join(MAP_FP, args.map2dir, 'inters_segments.shp'))

    orig_buffered_inter = []
    orig_index_inter = rtree.index.Index()

    new_buffered_inter = []
    new_index_inter = rtree.index.Index()
    for idx, new_line in enumerate(new_map_inter):
        b = new_line[0].buffer(10)
        new_buffered_inter.append((b, new_line[0], new_line[1]))
        new_index_inter.insert(idx, b.bounds)

    int_results = get_int_mapping(
        orig_map_inter, new_buffered_inter, new_index_inter)

    add_int_features(
        int_results,
        PROCESSED_DATA_FP,
        os.path.join(MAP_FP, args.map2dir), feats)
#    write_test(
#        new_buffered_inter[0][2],
#        'Polygon',
#        [(x[0], x[2]) for x in new_buffered_inter],
#        'buffered.shp'
#    )

#    write_test(
#        new_buffered_inter[0][2],
#        'Polygon',
#        [(x[0], x[2]) for x in orig_buffered_inter],
#        'orig_buffered.shp'
#    )



#    non_ints_with_candidates = get_candidates(
#        new_buffered, new_index, orig_map_non_inter)
#    get_mapping(non_ints_with_candidates)

#    lines_with_candidates = get_candidates(
#        new_buffered, new_index, orig_map)
#    get_mapping(lines_with_candidates)



    


