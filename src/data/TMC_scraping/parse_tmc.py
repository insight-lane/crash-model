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


def file_dataframe(excel_sheet, data_location):
    """
    Get the counts by hour in each direction from the excel spreadsheet
    Args:
        excel_sheet - the excel sheet of hourly counts
        data_location - a dataframe of the starting column and row
    Returns:
        A dataframe containing counts by hour in each direction
    """
    total_count = excel_sheet.cell_value(
        data_location['rows'][1]+1, data_location['columns'][1]+1)
    
    start_r = data_location['rows'][0] + 3
    end_r = data_location['rows'][1]

    column_time = data_location['columns'][0]
    column_east = column_time + 1
    column_south = column_time + 2
    column_west = column_time + 3
    column_north = column_time + 4
    
    times = excel_sheet.col_values(column_time, start_r, end_r)
    times_strip = [x.strip() for x in times]
    east = excel_sheet.col_values(column_east, start_r, end_r)
    south = excel_sheet.col_values(column_south, start_r, end_r)
    west = excel_sheet.col_values(column_west, start_r, end_r)
    north = excel_sheet.col_values(column_north, start_r, end_r)

    columns = ['times', 'east', 'south', 'west', 'north']
    return(pd.DataFrame({
        'times': times_strip,
        'east': east,
        'south': south,
        'west': west,
        'north': north,
    }, columns=columns)), total_count


def data_location(excel_sheet):
    """
    Look at current sheet to find the indices of the 'Time' field
    Use that as starting column and row
    Use number of columns/rows - 2 as ending column/row
    """
    sheet_c = excel_sheet.ncols
    sheet_r = excel_sheet.nrows

    start_c = 0
    start_r = 0
    
    end_c = sheet_c - 2
    end_r = sheet_r - 2
    for col in range(sheet_c):
        for row in range(sheet_r):
            cell_value = excel_sheet.cell_value(rowx=row, colx=col)
            if "time" in str(cell_value).lower():
                start_c = col
                start_r = row
            # Look for tot or total in the columns
            # That shows us where the bottom right is
            if 'tot' in str(cell_value).lower():
                if col == 0:
                    end_r = row - 1
                else:
                    end_c = col - 1

    return pd.DataFrame.from_records([
        ('start', start_c, start_r),
        ('end', end_c, end_r)
    ], columns=['value', 'columns', 'rows'])


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


def extract_data_sheet(sheet, sheet_data_location, counter):
    sheet_df, total_count = file_dataframe(sheet, sheet_data_location)
    sheet_df['data_id'] = counter
    return sheet_df, total_count


def log_data_sheet(sheet, sheet_name, sheet_data_location,
                   counter, filename, address, date):
    
    column_time = sheet_data_location['columns'][0]
    row_time = sheet_data_location['rows'][0]
    
    row_street = row_time + 1
    column_east = column_time + 1
    column_south = column_time + 2
    column_west = column_time + 3
    column_north = column_time + 4
    
    east = sheet.cell_value(row_street, column_east)
    south = sheet.cell_value(row_street, column_south)
    west = sheet.cell_value(row_street, column_west)
    north = sheet.cell_value(row_street, column_north)
    
    # Since column names can vary, clean up
    sheet_name = re.sub('all\s', '', sheet_name)
    sheet_name = re.sub('(\w+)\.?(\s.*)?', r'\1', sheet_name)

    record = pd.DataFrame([(
        counter,
        address,
        date,
        east,
        south,
        west,
        north,
        sheet_name,
        filename)],
        columns=[
            'id',
            'address',
            'date',
            'east',
            'south',
            'west',
            'north',
            'data_type',
            'filename'])
    return record


def extract_and_log_data_sheet(workbook, sheet_name, counter, filename,
                               address, date, data_info):

    sheet_names = [x.lower() for x in workbook.sheet_names()]
    sheet_index = sheet_names.index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)
    # This gives the location in the sheet where the counts start/end
    sheet_data_location = data_location(sheet)

    data_sheet, total_count = extract_data_sheet(
        sheet, sheet_data_location, counter)
    logged = log_data_sheet(
        sheet,
        sheet_name,
        sheet_data_location,
        counter,
        filename,
        address,
        date
    )

    data_info = data_info.append(logged)
    return data_sheet, data_info, total_count


def process_format1(workbook, filename, address, date,
                    counter, motor_col, ped_col, bike_col, all_data,
                    data_info):

    """
    Processes files in the format of the file starting with 6822_86_BERKELEY
    Updates dataframe for:
        -data_info, which gives description of the
        intersection/filename, what type of vehicle/pedestrian
        is being counted, and an id indexing into all_data
        -all_data gives an hourly count in each direction
    Args:
        workbook - the excel workbook
        filename
        address - the address for this TMC
        date
        counter - the index into all_data
        motor_col - the name of the sheet for the motors
        ped_col - the name of the sheet for the pedestrians
        bike_col - the name of the sheet for the bikes
        all_data - described above
        data_info - data_info

    Returns:
        
    """
    if motor_col:
        counter += 1
        motor, data_info, motor_count = extract_and_log_data_sheet(
            workbook, motor_col, counter, filename, address, date, data_info)
        all_data = all_data.append(motor)

    if ped_col:
        counter += 1
        pedestrian, data_info, ped_count = extract_and_log_data_sheet(
            workbook, ped_col, counter, filename, address, date, data_info)
        all_data = all_data.append(pedestrian)
        
    if bike_col:
        counter += 1
        bike, data_info, bike_count = extract_and_log_data_sheet(
            workbook, bike_col, counter, filename, address, date, data_info)
        all_data = all_data.append(bike)

    return all_data, counter, data_info, motor_count


def sum_format2_cols(sheet):
    """
    Sums the relevant rows from format2 files
    Args:
        workbook - the sheet
    Returns:
        total - total count from the sheet
    """
    start_r = 0
    for row in range(sheet.nrows):
        val = sheet.cell_value(rowx=row, colx=0)
        if val == 'Start Time':
            start_r = row + 1
        if val == '' and start_r:
            break
    end_r = row

    total = 0
    for col in range(1, sheet.ncols):
        if sheet.cell_value(start_r - 1, col) == '':
            break
        total += sum(sheet.col_values(col, start_r, end_r))
    return total


def process_format2(workbook, combined=False):
    """
    Processes files in the format of the file starting with 7538_1378_ARLINGTON
    For this format, we currently don't look for anything but total car count
    Args:
        workbook - the excel workbook
    Returns:
        total - total car and heavy vehicle count
    """

    # same format, different tabs
    # 6998 'Cars' 'Trucks' 'Bikes Peds'
    # 6988 - 'Cars Trucks' 'Bikes Peds'

    total = 0

    if combined:
        sheet = None
        for id in range(len(workbook.sheet_names())):
            sheet = workbook.sheet_by_index(id)
            if sheet.name.lower().startswith('car') \
               and sheet.name.lower().endswith('trucks'):
                break
        total = sum_format2_cols(sheet)
    else:
        sheet_index = workbook.sheet_names().index('Cars')
        sheet = workbook.sheet_by_index(sheet_index)
        total = sum_format2_cols(sheet)
        if 'Heavy Vehicles' in workbook.sheet_names():
            sheet_index = workbook.sheet_names().index('Heavy Vehicles')
        elif 'Trucks' in workbook.sheet_names():
            sheet_index = workbook.sheet_names().index('Trucks')
        sheet = workbook.sheet_by_index(sheet_index)
        total += sum_format2_cols(sheet)

    return total


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


def parse_tmcs():

    data_directory = RAW_DATA_FP + 'TURNING MOVEMENT COUNT/'

    all_data = pd.DataFrame()
    data_info = pd.DataFrame(columns=[
        'id',
        'address',
        'date',
        'east',
        'south',
        'west',
        'north',
        'data_type',
        'filename'
    ])

    # Stores the total count information
    summary = []

    print 'getting normalization factors'
    n_11, n_12 = get_normalization_factor()

    i = 0
    # Features we'll add to the processed tmc sheet

    missing = 0

    # Read geocoded cache
    geocoded_file = PROCESSED_DATA_FP + 'geocoded_addresses.csv'
    cached = {}
    if path_exists(geocoded_file):
        print 'reading geocoded cache file'
        cached = util.read_geocode_cache()

    data_directory = RAW_DATA_FP + 'TURNING MOVEMENT COUNT/'
    motor_count = 0
    for filename in listdir(data_directory):
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
                file_path = path.join(data_directory, filename)
                workbook = xlrd.open_workbook(file_path)
                sheet_names = [x.lower() for x in workbook.sheet_names()]

                motors = [col for col in sheet_names
                          if col.startswith('all motors')]
                peds = [col for col in sheet_names
                        if col.startswith('all peds')]
                
                if motors or peds or 'bicycles hr.' in sheet_names:
                    all_data, i, data_info, motor_count = process_format1(
                        workbook, filename, address, date,
                        i, motors[0] if motors else None,
                        peds[0] if peds else None,
                        'bicycles hr.' if 'bicycles hr.' in sheet_names else None,
                        all_data, data_info)
                elif 'cars' in sheet_names \
                     and (
                         'heavy vehicles' in sheet_names
                         or 'trucks' in sheet_names
                     ) and (
                         any(sheet.startswith('peds and ') for sheet in sheet_names)
                         or any(sheet.startswith('bikes') for sheet in sheet_names)
                     ):
                    motor_count = process_format2(workbook)
                elif any(sheet.startswith('cars') for sheet in sheet_names) \
                        and any(sheet.endswith('trucks') for sheet in sheet_names):

                    motor_count = process_format2(workbook, combined=True)
                else:
                    motor_count = None
                    missing += 1

                normalized = ''
                if motor_count:
                    if hours == 11:
                        normalized = int(round(motor_count/n_11))
                    else:
                        normalized = int(round(motor_count/n_12))
                value = {
                    'Filename': filename,
                    'Address': address,
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Date': date,
                    'Hours': hours,
                    'Total': int(motor_count) if motor_count else '',
                    'Normalized': normalized
                }
                summary.append(value)

        # Other formats are from 
        # 7499_279_BERKELEY

        # same format, different tabs
        # 6998 'Cars' 'Trucks' 'Bikes Peds'
        # 6988 - 'Cars Trucks' 'Bikes Peds'
        # 6973 - 'Cars & Trucks' 'Bikes & Peds'

    print 'missing:::::::::::::::::' + str(missing)
    # Write processed_tmc info


    # Write out the cached file
    util.write_geocode_cache(cached)

    # All data and data_info are temporary files that when we're done with
    # cleanup will be obsolete
    # data_info gives description of the intersection/filename, what type of
    # vehicle/pedestrian is being counted, and an id indexing into all_data
    # all_data gives an hourly count in each direction
    all_data.reset_index(drop=True, inplace=True)
    data_info.reset_index(drop=True, inplace=True)

    all_data = all_data.apply(pd.to_numeric, errors='ignore')
    data_info = data_info.apply(pd.to_numeric, errors='ignore')

    all_data.to_csv(path_or_buf=data_directory + 'all_data.csv', index=False)
    data_info.to_csv(path_or_buf=data_directory + 'data_info.csv', index=False)

#    print len(all_data)
#    print data_info.filename.nunique()
#    print all_data.keys()
#    print data_info.keys()
    all_joined = pd.merge(left=all_data,right=data_info, left_on='data_id', right_on='id')
#    print all_joined.groupby(['data_type']).sum()
#    print addresses

#    print data_info.head()
    return summary


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


def get_conflict_count(dir_locations, sheet, row):

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
                conflict_count2 = sheet.cell_value(
                    index,
                    dir_locations[
                        conflict['from2']]['to'][conflict['to2']])

                rowlabel = sheet.cell_value(index, 0)
                if 'tot' not in str(rowlabel).lower() and \
                   type(conflict_count1) == float and \
                   type(conflict_count2) == float:

                    conflicts += abs(conflict_count1 - conflict_count2)
    return conflicts


def parse_15_min_format1(workbook, sheet_name):

    sheet_index = workbook.sheet_names().index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)

    row = 8
    col = 1
    dir_locations = {}
    current = ''
    curr_count = 0

    while col < sheet.ncols:
        if 'north' in sheet.cell_value(row, col).lower():
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
        elif 'south' in sheet.cell_value(row, col).lower():
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
        elif 'east' in sheet.cell_value(row, col).lower():
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
        elif 'west' in sheet.cell_value(row, col).lower():
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

    dir_locations[current]['indices'][1] = dir_locations[
        current]['indices'][0] + curr_count

    row += 1
    total = 0
    left = 0
    right = 0
    for direction in dir_locations.keys():
        indices = dir_locations[direction]['indices']
        dir_locations[direction]['to'] = {}
        for col in range(indices[0], indices[1]):
            if 'thru' in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['thru'] = col
            elif 'right' in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['right'] = col
            elif 'left' in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['left'] = col
            elif 'u-tr' in sheet.cell_value(row, col).lower():
                dir_locations[direction]['to']['u-tr'] = col

        for dir, col_index in dir_locations[direction]['to'].iteritems():
            col_sum = sum(sheet.col_values(col_index, row + 1, sheet.nrows))
            total += col_sum

            # counts of left turns and counts of right turns
            # from each direction
            if dir == 'right':
                right += col_sum
            elif dir == 'left':
                left += col_sum
    conflicts = get_conflict_count(dir_locations, sheet, row)
    print str(total) + ',' + str(left) + ',' + str(right) + ',' + str(conflicts)


def parse_15_min_format(workbook, sheet_name, format):

    sheet_index = workbook.sheet_names().index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)

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
            end = indices[1] - 1
        else:
            end = indices[1]
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
            
            for r in range(row_start, sheet.nrows):
                rowlabel = sheet.cell_value(r, 0)
                if 'tot' not in str(rowlabel).lower() and \
                   type(sheet.cell_value(r, col_index)) == float:
                    col_sum += sheet.cell_value(r, col_index)
            total_count += col_sum

            # counts of left turns and counts of right turns
            # from each direction
            if dir == 'right':
                right_count += col_sum
            elif dir == 'left':
                left_count += col_sum

    conflicts = get_conflict_count(dir_locations, sheet, row)
    print str(total_count) + ',' + str(left_count) + ',' + str(right_count) + ',' + str(conflicts)


def parse_conflicts(address_records):
    for address in address_records:
        filename = address['Filename']
        file_path = path.join(TMC_FP, filename)
        workbook = xlrd.open_workbook(file_path)
        sheet_names = workbook.sheet_names()
        # If it's not near an intersection, either the
        # address couldn't be looked up or it's at a crosswalk which
        # we don't look at yet
        if address['near_intersection_id']:
            if 'Cars & Trucks' in sheet_names:
                parse_15_min_format(workbook, 'Cars & Trucks', 1)

    # files that don't adhere to n/s/e/w
    # 6909_629_ADAMS-ST,-EAST-ST,-WINTER-ST_NA_NA_DORCHESTER_11HR_NA_05-14-2013.XLS
    # 7283_268_BOWDOIN-ST,-QUINCY-ST_NA_NA_DORCHESTER_11-HOURS_NA_06-04-2013.XLS
    # 6986_2346_MALCOLM-X-BLVD,-ROXBURY-ST,-SHAWMUT-AVE_NA_NA_ROXBURY_11-HOURS_NA_06-19-2013.XLS

        elif '15\' all Motors' in sheet_names:
            print filename
            parse_15_min_format(workbook, '15\' all Motors', 2)

if __name__ == '__main__':

    address_records = []

    summary_file = PROCESSED_DATA_FP + 'tmc_summary.json'
    if not path_exists(summary_file):
        print 'No tmc_summary.json, parsing tmcs files now...'

        summary = parse_tmcs()
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
#            json.dump([x['properties'] for x in address_records], f)
            json.dump(address_records, f)
    else:
        address_records = json.load(open(summary_file))

    print len(address_records)
    parse_conflicts(address_records)

#    compare_crashes()

#    import ipdb; ipdb.set_trace()

#    print address_records[0]
#    compare_atrs(address_records)
#    norm = get_normalization_factor()
#    print addresses.keys()
#    print type(addresses)
#    print address_records[0]
#    plot_tmcs(addresses)





