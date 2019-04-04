import argparse
from . import util
from shapely.ops import unary_union
from shapely.geometry import Point
import rtree
import os
from .segment import Segment

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

PROCESSED_DATA_FP = None
MAP_FP = None


def add_match_features(line, features):
    """
    Add the properties from the features dict to the line
    """
    feats_list = {}
    for m in line['matches']:
        for k, v in list(m[1].items()):
            if k in features:
                if k not in feats_list:
                    feats_list[k] = []
                if v:
                    feats_list[k].append(v)

    # Add new features to existing ones
    for feat, values in list(feats_list.items()):
        if values and len(set(values)) == 1:
            line['properties'][feat] = values[0]
        else:
            line['properties'][feat] = 0


def get_mapping(lines, features):
    """
    Attempts to map one or more segments of the second map to the first map
    Args:
        lines - a list of dicts containing the line from the first map,
            the properties, the candidate overlapping lines from the new map,
            and nearby segments on the original map because we may want to
            combine two for the purposes of mapping
    """
    print(len(lines))
    result_counts = [0, 0]
    buff = 5

    # keep track of which new segments matched at which size buffer
    buff_match = {}

    new_id = 0
    while buff <= 20:
        print("Looking at buffer " + str(buff))
        for i in range(len(lines)):
            util.track(i, 1000, len(lines))
            if 'matches' in list(lines[i].keys()):
                continue

            matched_candidates = []

            for j, candidate in enumerate(lines[i]['candidates']):
                if 'id' not in list(lines[i]['candidates'][j][1].keys()):
                    lines[i]['candidates'][j][1]['id'] = new_id
                    new_id += 1
                match = True

                for coord in candidate[0].coords:
                    if not Point(coord).within(lines[i]['line'].buffer(buff)):
                        match = False
                if match:
                    matched_candidates.append((candidate, buff))

                    if lines[i]['candidates'][j][1]['id'] \
                       not in list(buff_match.keys()):
                        buff_match[lines[i]['candidates'][j][1]['id']] = buff

            if matched_candidates:
                lines[i]['matches'] = matched_candidates

        buff *= 2
    
    # Now go through the lines that still aren't matched
    # this time, see if they are a subset of any of their candidates
    for i in range(len(lines)):
        matched_candidates = []
        if 'matches' in list(lines[i].keys()):
            continue
        for j, candidate in enumerate(lines[i]['candidates']):
            if 'id' not in list(lines[i]['candidates'][j][1].keys()):
                lines[i]['candidates'][j][1]['id'] = new_id
                new_id += 1

            match = True
            for coord in lines[i]['line'].coords:
                if not Point(coord).within(candidate[0].buffer(20)):
                    match = False
            if match:
                matched_candidates.append((candidate, 20))
                if lines[i]['candidates'][j][1]['id'] not in list(buff_match.keys()):
                    buff_match[lines[i]['candidates'][j][1]['id']] = buff
        if matched_candidates:
            lines[i]['matches'] = matched_candidates

    # Remove matches that matched better on a different segment
    # But only if there's a match for that segment already
    for i in range(len(lines)):
        if 'matches' in list(lines[i].keys()):
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
        if 'matches' in list(line.keys()) and line['matches']:
            result_counts[0] += 1
            
            orig.append((line['line'], line['properties']))

            # Every single match for this line
            add_match_features(line, features)

            # Add each matching line
            # Only used for debugging purposes, take out eventually
            for m in line['matches']:
                matched.append((m[0], m[1]))

        else:
            for f in features:
                line['properties'][f] = 0
            result_counts[1] += 1

    percent_matched = float(result_counts[0])/(
        float(result_counts[0]+result_counts[1])) * 100
    print('Found matches for ' + str(percent_matched) + '% of segments')


def get_int_mapping(lines, buffered, buffered_index):
    """
    Gets the mappings between intersections
    Args:
        lines - the set of lines in an intersection
        buffered - the buffered lines for the intersections in the other map
        buffered_index - the rtree index
    """
    print("Getting intersection mappings")

    line_results = []
    # Go through each line from the osm map
    for i, line in enumerate(lines):
        util.track(i, 1000, len(lines))
        line_buffer = line.geometry.buffer(10)

        best_match = {}
        best_overlap = 0
        for idx in buffered_index.intersection(line_buffer.bounds):
            buffer = buffered[idx][0]
            # If the new buffered intersection intersects the old one
            # figure out how much overlap, and take the best one
            if buffer.intersects(line.geometry):
                total_area = unary_union([line_buffer, buffer]).area
                overlap = max(
                    line_buffer.area/total_area, buffer.area/total_area)
                
                if overlap > best_overlap and overlap > .20:
                    best_overlap = overlap
                    best_match = buffered[idx][2]

        line_results.append([line.geometry, line.properties, best_match])

    total = len(line_results)
    percent_matched = 100 - 100 * float(
        len([x for x in line_results if not x[2]]))/float(total)
    print("Found matches for " + str(percent_matched) + "% of intersections")
    return line_results


def get_candidates(buffered, buffered_index, lines):
    """
    Gets candidate matches: lines that overlap the buffer of
    lines from the other map
    Args:
        buffered - a list of tuples containing the buffer,
            the linestring, and the properties for the lines for one map
        buffered_index - the rtree index
        lines - the lines for the other map
    Returns:
        a list of dicts containing a line, the properties,
        and the candidate overlapping lines
    """
    results = []

    print("Getting candidate overlapping lines")

    # Go through each line from the osm map
    for i, line in enumerate(lines):

        overlapping = []
        util.track(i, 1000, len(lines))

        # First, get candidates from new map that overlap the buffer
        # from the original map
        for idx in buffered_index.intersection(line.geometry.bounds):
            buffer = buffered[idx][0]

            # If the new line overlaps the old line
            # then check whether it is entirely within the old buffer
            if buffer.intersects(line.geometry):

                # Add the linestring and the features to the overlap list
                overlapping.append((buffered[idx][1], buffered[idx][2]))

        results.append({
            'line': line.geometry,
            'properties': line.properties,
            'candidates': overlapping,
        })

    return results


def add_int_features(inters, int_lines, featlist):
    """
    Adds the features to the intersections. Since intersection segments
    are made up of the lines coming into an intersection, intersection
    features are stored in a json file. Eventually the max value from all
    the lines coming into the intersection is chosen for the feature.
    Since we aren't mapping each individual line of the intersection,
    (sometimes impossible, since the maps are often a little different)
    we'll just take the max value here
    Args:
        inters - inter segments
        int_lines - contains the ids for the original intersection lines,
            and the new mapped intersection lines
        featlist - the features to add
    Returns:
        The updated inters list
    """

    indexed_inters = {str(x.properties['id']): x for x in inters}

    for line in int_lines:

        idx = str(line[1]['id'])
        if line[2]:
            for feat in featlist:
                if feat in line[2]:
                    indexed_inters[idx].properties[feat] = line[2][feat]

    return indexed_inters.values()


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

    non_inters_osm_file = os.path.join(
        MAP_FP, 'non_inters_segments.geojson')
    print("Reading original map from " + non_inters_osm_file)
    osm_map_non_inter = util.read_geojson(non_inters_osm_file)

    non_inters_new_file = os.path.join(
        MAP_FP, args.map2dir, 'non_inters_segments.geojson')
    print("Reading new map from " + non_inters_new_file)

    new_map_non_inter = util.read_geojson(non_inters_new_file)

    # Index for the new map
    new_buffered = []
    new_index = rtree.index.Index()

    # Buffer all the new lines
    for idx, new_line in enumerate(new_map_non_inter):
        b = new_line.geometry.buffer(20)
        new_buffered.append((b, new_line.geometry, new_line.properties))
        new_index.insert(idx, b.bounds)

    non_ints_with_candidates = get_candidates(
        new_buffered, new_index, osm_map_non_inter)

    print("Adding features: " + ','.join(feats))
    get_mapping(non_ints_with_candidates, feats)

    non_inters = [Segment(x['line'], x['properties'])
                  for x in non_ints_with_candidates]

    # Now do intersections
    osm_map_inter = util.read_geojson(
        os.path.join(MAP_FP, 'inters_segments.geojson'))
    new_map_inter = util.read_geojson(os.path.join(
        MAP_FP, args.map2dir, 'inters_segments.geojson'))

    orig_buffered_inter = []
    orig_index_inter = rtree.index.Index()

    new_buffered_inter = []
    new_index_inter = rtree.index.Index()
    for idx, new_line in enumerate(new_map_inter):
        b = new_line.geometry.buffer(10)
        new_buffered_inter.append((b, new_line.geometry, new_line.properties))
        new_index_inter.insert(idx, b.bounds)

    int_results = get_int_mapping(
        osm_map_inter, new_buffered_inter, new_index_inter)

    inters = add_int_features(
        osm_map_inter,
        int_results,
        feats
    )
    util.write_segments(non_inters, inters, MAP_FP)


    


