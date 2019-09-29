import xlrd
from os import listdir, path
from os.path import exists as path_exists
import re
from dateutil.parser import parse
from .. import util
import rtree
import json
import pyproj
import os
import argparse
import sys
from ..record import Record


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

RAW_DATA_FP = os.path.join(BASE_DIR, 'data/raw')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')
ATR_FP = os.path.join(RAW_DATA_FP, 'volume', 'ATRs')
TMC_FP = os.path.join(RAW_DATA_FP, 'volume', 'TMCs')
STANDARDIZED_DATA_FP = os.path.join(BASE_DIR, 'data', 'standardized')


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
    if intersection in list(cached.keys()):
        print(intersection + ' is cached')
        return cached[intersection]
    else:
        print('geocoding ' + intersection)
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
            print('trying again, this time geocoding ' + intersection)
            result = list(util.geocode_address(intersection))
        result.insert(0, intersection)

        return result
    
    return None, None, None, None, 'F'


def snap_inter_and_non_inter(summary):
    inter = util.read_geojson(
        os.path.join(PROCESSED_DATA_FP, 'maps/inters_segments.geojson'))

    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(inter):
        segments_index.insert(idx, element.geometry.bounds)
    print("Snapping tmcs to intersections")

    # Turn the summary into the format that works for reprojection
    address_records = []
    for properties in summary:
        properties['location'] = {
            'latitude': properties['Latitude'],
            'longitude': properties['Longitude']
        }
        address_records.append(Record(properties))

    util.find_nearest(address_records, inter, segments_index, 30, type_record=True)

    # Find_nearest got the nearest intersection id, but we want to compare
    # against all segments too.  They don't always match, which may be
    # something we'd like to look into
    for address in address_records:
        address.properties['near_intersection_id'] = \
            str(address.properties['near_id'])
        address.properties['near_id'] = ''

    combined_seg, segments_index = util.read_segments(os.path.join(PROCESSED_DATA_FP, 'maps'))
    util.find_nearest(address_records, combined_seg, segments_index, 30, type_record=True)

    return address_records


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
    counts = util.get_hourly_rates(os.path.join(
        STANDARDIZED_DATA_FP, 'volume.json'))

    return sum(counts[7:18]), sum(counts[7:19])


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
        if conflict['from1'] in list(dir_locations.keys()) \
           and conflict['to1'] in list(dir_locations[
               conflict['from1']]['to'].keys()) \
           and conflict['from2'] in list(dir_locations.keys()) \
           and conflict['to2'] in list(dir_locations[
               conflict['from2']]['to'].keys()):
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
            if 'north' in list(dir_locations.keys()):
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
            if 'south' in list(dir_locations.keys()):
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
            if 'east' in list(dir_locations.keys()):
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
            if 'west' in list(dir_locations.keys()):
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
    for direction in list(dir_locations.keys()):
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

        for dir, col_index in dir_locations[direction]['to'].items():
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

    print('getting normalization factors')
    n_11, n_12 = get_normalization_factor()

    # Read geocoded cache
    geocoded_file = os.path.join(PROCESSED_DATA_FP, 'geocoded_addresses.csv')
    cached = {}
    if path_exists(geocoded_file):
        print('reading geocoded cache file')
        cached = util.read_geocode_cache(filename=geocoded_file)

    summary = []
    for filename in listdir(TMC_FP):
        if filename.endswith('.XLS'):

            # Pull out what we can from the filename itself
            orig_address, address, latitude, longitude, status = \
                find_address_from_filename(filename, cached)
            # If you can't geocode the address then there's not much point
            # in parsing it because you won't be able to snap it to a segment
            if latitude:

                if orig_address:
                    cached[orig_address] = [
                        address, latitude, longitude, status]
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
                    print(filename)
                    print(hours)
                    print(counts)

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
    util.write_geocode_cache(cached, filename=geocoded_file)

    print("parsed " + str(count) + " TMC files")
    return summary

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")

    # Can force update
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether force update the maps')

    args = parser.parse_args()
    if args.datadir:
        RAW_DATA_FP = os.path.join(args.datadir, 'raw')
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        STANDARDIZED_DATA_FP = os.path.join(args.datadir, 'standardized')
        ATR_FP = os.path.join(RAW_DATA_FP, 'volume', 'ATRs')
        TMC_FP = os.path.join(RAW_DATA_FP, 'volume', 'TMCs')

    if not os.path.exists(TMC_FP):
        print("No TMC directory, skipping...")
        sys.exit()
    if not os.path.exists(os.path.join(STANDARDIZED_DATA_FP, 'volume.json')):
        # At the moment this is true, but it probably can be skipped if
        # not available
        print("TMC parsing needs volume data for normalization, skipping...")
        sys.exit

    address_records = []

    print('Parsing turning movement counts...')
    summary_file = os.path.join(PROCESSED_DATA_FP, 'tmc_summary.json')
    if not path_exists(summary_file) or args.forceupdate:
        print('Parsing tmc files...')

        summary = parse_conflicts()
        address_records = snap_inter_and_non_inter(summary)

        items = json.load(
            open(os.path.join(PROCESSED_DATA_FP, 'crash_joined.json')))

        all_crashes, crashes_by_location = util.group_json_by_location(items)

        for record in address_records:
            if record.properties['near_id'] \
               and str(record.properties['near_id']) \
               in list(crashes_by_location.keys()):
                record.properties['crash_count'] = crashes_by_location[
                    str(record.properties['near_id'])]['count']

        with open(summary_file, 'w') as f:
            address_records = [x.properties for x in address_records]
            json.dump(address_records, f)
    else:
        address_records = json.load(open(summary_file))
        print("Read in " + str(len(address_records)) + " records")






