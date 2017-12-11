import xlrd
import pandas as pd
from os import listdir, path
from os.path import exists as path_exists
import re
from dateutil.parser import parse
from .. import util
import rtree
import folium
import json
import pyproj
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

RAW_DATA_FP = BASE_DIR + '/data/raw/'
PROCESSED_DATA_FP = BASE_DIR + '/data/processed/'
ATR_FP = BASE_DIR + '/data/raw/AUTOMATED TRAFFICE RECORDING/'
TMC_FP = RAW_DATA_FP + '/TURNING MOVEMENT COUNT/'


def num_hours(filename):
    """
    Parses out filename to give the number of hours of the sample
    Args:
        filename
    Returns:
        number
    """
    prefix = re.sub('\.XLS', '', filename)
    segments = prefix.split('_')
    return segments[len(segments)-3].split('-')[0]


def find_date(filename):
    """
    Parses out filename to give the date
    Args:
        filename
    Returns:
        date
    """
    prefix = re.sub('\.XLS', '', filename)
    segments = prefix.split('_')
    return parse(segments[len(segments) - 1]).date()


def lookup_address(intersection, cached):
    """
    Look up an intersection first in the cache, and if it
    doesn't exist, geocode it

    Args:
        intersection: string
        cached: dict
    Returns:
        tuple of original address, geocoded address, latitude, longitude
    """
    if intersection in cached.keys():
        print intersection + ' is cached'
        return cached[intersection]
    else:
        print 'geocoding ' + intersection
        return list(util.geocode_address(intersection))


def find_address_from_filename(filename, cached):
    """
    Parses out filename to give an intersection
    Args:
        filename
    Returns:
        tuple of original address, geocoded address, latitude, longitude
    """
    intersection = filename.split('_')[2]
    streets = intersection.split(',')
    streets = [re.sub('-', ' ', s) for s in streets]
    # Strip out space at beginning of street name if it's there
    streets = [s if s[0] != ' ' else s[1:len(s)] for s in streets]

    if len(streets) >= 2:
        intersection = streets[0] + ' and ' + streets[1] + ' Boston, MA'
        result = lookup_address(intersection, cached)

        # It's possible that google can't look up the address by the
        # first two street names for an intersection containing three
        # or more street names.  Try the first and second
        if (result is None
                or 'Boston' not in str(result[0])) and len(streets) > 2:
            intersection = streets[0] + ' and ' + streets[2] + ' Boston, MA'
            print 'trying again, this time geocoding ' + intersection
            result = list(util.geocode_address(intersection))
        result.insert(0, intersection)
        return result
    return None, None, None, None


def snap_inter_and_non_inter(summary):
    inter = util.read_shp(PROCESSED_DATA_FP + 'maps/inters_segments.shp')

    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(inter):
        segments_index.insert(idx, element[0].bounds)
    print "Snapping tmcs to intersections"

    address_records = util.raw_to_record_list(
        summary, pyproj.Proj(init='epsg:4326'), x='Longitude', y='Latitude')
    util.find_nearest(address_records, inter, segments_index, 30)

    # Find_nearest got the nearest intersection id, but we want to compare
    # against all segments too.  They don't always match, which may be
    # something we'd like to look into
    for address in address_records:
        address['properties']['near_intersection_id'] = \
            str(address['properties']['near_id'])
        address['properties']['near_id'] = ''

    combined_seg, segments_index = util.read_segments()
    util.find_nearest(address_records, combined_seg, segments_index, 30)
    return address_records


def plot_tmcs(addresses):

    # First create basemap
    points = folium.Map(
        [42.3601, -71.0589],
        tiles='Cartodb Positron',
        zoom_start=12
    )

    # plot tmcs
    for address in addresses.iterrows():
        if not pd.isnull(address[1]['Latitude']):
            folium.CircleMarker(
                location=[address[1]['Latitude'], address[1]['Longitude']],
                fill_color='yellow', fill=True, fill_opacity=.7, color='yellow',
                radius=6).add_to(points)

    # Plot atrs
    atrs = util.csv_to_projected_records(
        PROCESSED_DATA_FP + 'geocoded_atrs.csv', x='lng', y='lat')
    for atr in atrs:
        properties = atr['properties']
        if properties['lat']:
            folium.CircleMarker(
                location=[float(properties['lat']), float(properties['lng'])],
                fill_color='green', fill=True, fill_opacity=.7, color='grey',
                radius=6).add_to(points)

    points.save('map.html')


def get_normalization_factor():
    """
    TMC counts are only over 11 or 12 hours, always starting at 7
    Normalize using average rates of the 24 hour ATRs,
    since they're pretty consistent
    Args:
        None
    Returns:
        Tuple of 11 hour normalization, 12 hour normalization
    """
    # Read in atr lats
    atrs = util.csv_to_projected_records(
        PROCESSED_DATA_FP + 'geocoded_atrs.csv', x='lng', y='lat')

    files = [ATR_FP +
             atr['properties']['filename'] for atr in atrs]
    all_counts = util.get_hourly_rates(files)
    counts = [sum(i)/len(all_counts) for i in zip(*all_counts)]

    return sum(counts[7:18]), sum(counts[7:19])


def compare_atrs(tmcs):
    atrs = {}
    count = 0
    with open(PROCESSED_DATA_FP + 'snapped_atrs.json') as f:
        data = json.load(f)
        print data[0]
        for row in data:
            if row['near_id']:
                atrs[row['near_id']] = row
    for tmc in tmcs:
        if tmc['properties']['near_id'] in atrs.keys():
            print "------------------------------------------"
            print tmc['properties']
            print atrs[tmc['properties']['near_id']]
            print ".........................................."
            count += 1
    print count


def compare_crashes():

    count = 0
    print 'comparing.........'
    inters = {}
    with open(PROCESSED_DATA_FP + 'inters_data.json') as f:
        print 'yay'
        data = json.load(f)
        for key, value in data.iteritems():
            inters[str(key)] = value[0]

    print inters.values()[0]

    crashes_by_seg = {}
    with open(PROCESSED_DATA_FP + 'crash_joined.json') as f:
        data = json.load(f)
        for row in data:
            if str(row['near_id']) == '':
                next
            if str(row['near_id']) not in crashes_by_seg.keys():
                crashes_by_seg[str(row['near_id'])] = {
                    'total': 0, 'type': [], 'values': []}
            crashes_by_seg[str(row['near_id'])]['total'] += 1
            crashes_by_seg[str(row['near_id'])]['type'].append(
                row['FIRST_EVENT_SUBTYPE'])
            crashes_by_seg[str(row['near_id'])]['values'].append(row)
            
#    print len(crashes_by_seg.keys())
    count = 0
    max = 0
    max_intersection = None
    high_crashes = []
    single_crash = []
    no_crashes = []
    crash_tuples = []

    results = []

    crash_count = []
    crash_volume = []
    crash_speed = []
    crash_speed_bins = []
    with open(PROCESSED_DATA_FP + 'tmc_summary.json') as f:
        data = json.load(f)
        for row in data:
            if str(row['near_intersection_id']) in crashes_by_seg.keys() \
               and row['near_intersection_id'] != '':
                crashes = crashes_by_seg[str(row['near_intersection_id'])]
                row['Crashes'] = crashes['total']
                row['Types'] = crashes['type']
                row['Speed'] = inters[str(row['near_intersection_id'])]['SPEEDLIMIT']
                results.append(row)

                crash_tuples.append((
                    crashes['total'], str(row['near_intersection_id']), row['Normalized']))
                if row['Normalized']:
                    crash_count.append(float(crashes['total']))
#                    print row['Normalized']
                    crash_volume.append(float(row['Normalized']))
                    crash_speed.append(float(row['Speed']))
                    if row['Speed'] < 20:
                        crash_speed_bins.append(float(1))
                    elif row['Speed'] < 30:
                        crash_speed_bins.append(float(2))
                    else:
                        crash_speed_bins.append(float(3))
                if crashes['total'] > max:
                    max = crashes['total']
                    max_intersection = row
#                    print "......................."
#                    print row
                if crashes['total'] > 1:
                    if row['Normalized']:
                        high_crashes.append(row['Normalized'])
                else:
                    if row['Normalized']:
                        single_crash.append(row['Normalized'])
            else:
                if row['Normalized']:
                    no_crashes.append(row['Normalized'])
                count += 1

#    print '8028' in crashes_by_seg.keys()
    high_crashes.sort()
    single_crash.sort()
    no_crashes.sort()
#    print high_crashes
#    print sum(high_crashes)/len(high_crashes)

#    print sum(single_crash)/len(single_crash)
#    print no_crashes
#    print sum(no_crashes)/len(no_crashes)
#    print max
#    print max_intersection

    for i in range(2):
        print results[i]

    import numpy
    print numpy.corrcoef([crash_count, crash_speed_bins])
#    print crash_tuples

    sorted_results = sorted(results, key=lambda k: k['Normalized'])
    print sorted_results[0]
    print sorted_results[len(results)-1]
    print len(sorted_results)
    # count = 0
    print single_crash
    print high_crashes
    #     if tmc['properties']['near_id'] in crashes_by_seg.keys():
    #         print tmc['properties']
    #     count += 1
    # print "count::::::::::::::::::::" + str(count)
    # print len(crashes_by_seg)


def add_direction(direction_locations, direction, col, previous, count):
    direction_locations[direction] = {'indices': [col, 0]}
    if previous:
        direction_locations[previous]['indices'][1] = direction_locations[
            previous]['indices'][0] + count
    return direction_locations


def get_conflict_count(dir_locations, sheet, row, sheet2):

    # Conflicts (count each conflict over 15 minutes)
    conflicts = 0
    conflict_sets = [{
        # Left turn from south conflicts with straight from north
        'from1': 'south',
        'to1': 'left',
        'from2': 'north',
        'to2': 'thru'
    }, {
        # Right turn from south conflicts with straight from west
        'from1': 'south',
        'to1': 'right',
        'from2': 'west',
        'to2': 'thru'
    }, {
        # Left turn from west conflicts with straight from east
        'from1': 'west',
        'to1': 'left',
        'from2': 'east',
        'to2': 'thru'
    }, {
        # Right turn from west conflicts with straight from north
        'from1': 'west',
        'to1': 'right',
        'from2': 'north',
        'to2': 'thru'
    }, {
        # Left turn from north conflicts with straight from south
        'from1': 'north',
        'to1': 'left',
        'from2': 'south',
        'to2': 'thru'
    }, {
        # Right turn from north conflicts with straight from east
        'from1': 'north',
        'to1': 'right',
        'from2': 'east',
        'to2': 'thru'
    }, {
        # Left turn from east conflicts with straight from west
        'from1': 'east',
        'to1': 'left',
        'from2': 'west',
        'to2': 'thru'
    }, {
        # Right turn from east conflicts with straight from south
        'from1': 'east',
        'to1': 'right',
        'from2': 'south',
        'to2': 'thru'
    }]

    for conflict in conflict_sets:
        if conflict['from1'] in dir_locations.keys() \
           and conflict['to1'] in dir_locations[
               conflict['from1']]['to'].keys() \
           and conflict['from2'] in dir_locations.keys() \
           and conflict['to2'] in dir_locations[
               conflict['from2']]['to'].keys():
            for index in range(row+1, sheet.nrows):
                conflict_count1 = sheet.cell_value(
                    index,
                    dir_locations[
                        conflict['from1']]['to'][conflict['to1']])
                if sheet2:
                    conflict_count1 += sheet2.cell_value(
                        index,
                        dir_locations[
                            conflict['from1']]['to'][conflict['to1']])
                conflict_count2 = sheet.cell_value(
                    index,
                    dir_locations[
                        conflict['from2']]['to'][conflict['to2']])
                if sheet2:
                    conflict_count2 += sheet2.cell_value(
                        index,
                        dir_locations[
                            conflict['from2']]['to'][conflict['to2']])
                rowlabel = sheet.cell_value(index, 0)
                if 'tot' not in str(rowlabel).lower() and \
                   type(conflict_count1) == float and \
                   type(conflict_count2) == float:

                    conflicts += min(conflict_count1, conflict_count2)
    return conflicts


def parse_15_min_format(workbook, sheet_name, format, sheet_name2=None):

    sheet_index = workbook.sheet_names().index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)
    sheet2 = None
    if sheet_name2:
        sheet_index2 = workbook.sheet_names().index(sheet_name2)
        sheet2 = workbook.sheet_by_index(sheet_index2)

    if format == 1:
        row = 8
        north = 'north'
        south = 'south'
        east = 'east'
        west = 'west'
        thru = 'thru'
        left = 'left'
        right = 'right'
    elif format == 2:
        row = 6
        north = 's.b.'
        south = 'n.b.'
        east = 'w.b.'
        west = 'e.b.'
        thru = 't'
        left = 'l'
        right = 'r'

    col = 1
    dir_locations = {}
    current = ''
    curr_count = 0

    # Can't be a full 11-12 hour count if it's this small
    if sheet.nrows < 25:
        return
    while col < sheet.ncols:
        if north in sheet.cell_value(row, col).lower():
            if 'north' in dir_locations.keys():
                return
            dir_locations = add_direction(
                dir_locations,
                'north',
                col,
                current,
                curr_count
            )
            current = 'north'
            curr_count = 0
        elif south in sheet.cell_value(row, col).lower():
            if 'south' in dir_locations.keys():
                return
            dir_locations = add_direction(
                dir_locations,
                'south',
                col,
                current,
                curr_count
            )
            current = 'south'
            curr_count = 0
        elif east in sheet.cell_value(row, col).lower():
            if 'east' in dir_locations.keys():
                return
            dir_locations = add_direction(
                dir_locations,
                'east',
                col,
                current,
                curr_count
            )
            current = 'east'
            curr_count = 0
        elif west in sheet.cell_value(row, col).lower():
            if 'west' in dir_locations.keys():
                return
            dir_locations = add_direction(
                dir_locations,
                'west',
                col,
                current,
                curr_count
            )
            current = 'west'
            curr_count = 0
        col += 1
        curr_count += 1

    # Labels might be messed up, don't look at these either
    if not current:
        return

    dir_locations[current]['indices'][1] = dir_locations[
        current]['indices'][0] + curr_count

    if format == 1:
        row += 1
    elif format == 2:
        row += 3
    total_count = 0
    left_count = 0
    right_count = 0
    for direction in dir_locations.keys():
        indices = dir_locations[direction]['indices']
        dir_locations[direction]['to'] = {}

        # hack because at least one of the tmcs has a bad header for the total
        if format == 2:
            end = min(indices[1] - 1, sheet.ncols)
        else:
            end = min(indices[1], sheet.ncols)
        for col in range(indices[0], end):
            if thru in sheet.cell_value(row, col).lower() \
               and 'tot' not in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['thru'] = col
            elif right in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['right'] = col
            elif left in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['left'] = col
            elif 'u-tr' in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['u-tr'] = col

        for dir, col_index in dir_locations[direction]['to'].iteritems():
            col_sum = 0
            row_start = row + 1

            quarter_hours = 0
            for r in range(row_start, sheet.nrows):
                rowlabel = sheet.cell_value(r, 0)
                # Only look at the first 11 hours for normalization
                # And ignore totals
                if quarter_hours < 44 \
                   and 'tot' not in str(rowlabel).lower() and \
                   type(sheet.cell_value(r, col_index)) == float:
                    quarter_hours += 1
                    col_sum += sheet.cell_value(r, col_index)
                    if sheet2:
                        col_sum += sheet2.cell_value(r, col_index)
                        
            total_count += col_sum

            # counts of left turns and counts of right turns
            # from each direction
            if dir == 'right':
                right_count += col_sum
            elif dir == 'left':
                left_count += col_sum

    conflicts = get_conflict_count(dir_locations, sheet, row, sheet2)

    return [total_count, left_count, right_count, conflicts, quarter_hours]


def parse_conflicts():
    count = 0

    print 'getting normalization factors'
    n_11, n_12 = get_normalization_factor()

    # Read geocoded cache
    geocoded_file = PROCESSED_DATA_FP + 'geocoded_addresses.csv'
    cached = {}
    if path_exists(geocoded_file):
        print 'reading geocoded cache file'
        cached = util.read_geocode_cache()

    summary = []
    for filename in listdir(TMC_FP):
        if filename.endswith('.XLS'):

            # Pull out what we can from the filename itself
            orig_address, address, latitude, longitude = \
                find_address_from_filename(filename, cached)
            # If you can't geocode the address then there's not much point
            # in parsing it because you won't be able to snap it to a segment
            if latitude:

                if orig_address:
                    cached[orig_address] = [address, latitude, longitude]
                date = str(find_date(filename))
                hours = num_hours(filename)
                file_path = path.join(TMC_FP, filename)
                workbook = xlrd.open_workbook(file_path)
                sheet_names = workbook.sheet_names()

                # total, left, right, conflicts
                counts = [0, 0, 0, 0]
                result = None
                
                if [x for x in sheet_names if re.match('Cars.*Trucks', x)]:
                    sheet_name = [x for x in sheet_names
                                  if re.match('Cars.*Trucks', x)][0]
                    result = parse_15_min_format(workbook, sheet_name, 1)
                elif [x for x in sheet_names if re.match('15.*Motors A', x)]:
                    # skip this one
                    pass
                elif [x for x in sheet_names if re.match('15.*ll Motors', x)]:
                    sheet_name = [x for x in sheet_names
                                  if re.match('15.*ll Motors', x)][0]
                    result = parse_15_min_format(workbook, sheet_name, 2)
                elif 'Cars' in sheet_names and (
                        'Heavy Vehicles' in sheet_names
                        or 'Trucks' in sheet_names):
                    hv = 'Heavy Vehicles'
                    if 'Trucks' in sheet_names:
                        hv = 'Trucks'
                    result = parse_15_min_format(workbook, 'Cars', 1,
                                                 sheet_name2=hv)
                elif '15-min. Cars' in sheet_names \
                     and [x for x in sheet_names if re.match(
                         '15-min*Heavy Vehicle', x)]:
                    hv = [x for x in sheet_names if re.match(
                        '15-min*Heavy Vehicle', x)][0]
                    result = parse_15_min_format(workbook, '15-min. Cars', 1,
                                                 sheet_name2=hv)
                elif 'Cars & Peds' in sheet_names \
                     and 'Trucks & Bikes' in sheet_names:
                    result = parse_15_min_format(workbook, 'Cars & Peds', 1,
                                                 sheet_name2='Trucks & Bikes')

                if result:
                    count += 1
                    counts = result
                    print filename
                    print hours
                    print counts

                    normalized = ''
                    total = result[0]
                    if hours == 11:
                        normalized = int(round(total/n_11))
                    else:
                        normalized = int(round(total/n_12))
                    value = {
                        'Filename': filename,
                        'Address': address,
                        'Latitude': latitude,
                        'Longitude': longitude,
                        'Date': date,
                        'Hours': hours,
                        'Total': int(total),
                        'Normalized': normalized,
                        'Left': int(result[1]),
                        'Right': int(result[2]),
                        'Conflict': int(result[3])
                    }
                    summary.append(value)

    # Write out the cached file
    util.write_geocode_cache(cached)

    print "parsed " + str(count) + " TMC files"
    return summary

if __name__ == '__main__':

    address_records = []

    summary_file = PROCESSED_DATA_FP + 'tmc_summary.json'
    if not path_exists(summary_file):
        print 'No tmc_summary.json, parsing tmcs files now...'

        summary = parse_conflicts()
        address_records = snap_inter_and_non_inter(summary)

        all_crashes, crashes_by_location = util.group_json_by_location(
            PROCESSED_DATA_FP + 'crash_joined.json')

        for record in address_records:
            if record['properties']['near_id'] \
               and str(record['properties']['near_id']) \
               in crashes_by_location.keys():
                record['properties']['crash_count'] = crashes_by_location[
                    str(record['properties']['near_id'])]['count']

        with open(summary_file, 'w') as f:
            address_records = [x['properties'] for x in address_records]
            json.dump(address_records, f)
    else:
        address_records = json.load(open(summary_file))

    print len(address_records)

    # to do
    # move compare crashes to notebook
    # want to do anything with compare_atrs?
    # tests?
    # add any features to model?  what do we add from atrs?
    # plot_tmcs?  keep or get rid of
    
#    compare_crashes()





