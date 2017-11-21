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


def find_address(filename, cached):
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
        if intersection in cached.keys():
            print intersection + ' is cached'
            result = cached[intersection]
        else:
            print 'geocoding ' + intersection
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
                    address['properties']['near_id']
        address['properties']['near_id'] = ''

    combined_seg, segments_index = util.read_segments()
    util.find_nearest(address_records, combined_seg, segments_index, 30)
    print "................................."
    print len(combined_seg)
    print combined_seg[0]
    import ipdb; ipdb.set_trace()

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
            orig_address, address, latitude, longitude = find_address(
                filename, cached)
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
#            print "......................."
#            print row['near_id']
#            print row
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


if __name__ == '__main__':

    address_records = []
    if not path_exists(PROCESSED_DATA_FP + 'tmc_summary.json'):
        print 'No tmc_summary.json, parsing tmcs files now...'
        summary = parse_tmcs()
        address_records = snap_inter_and_non_inter(summary)
        print address_records[0]
        with open(PROCESSED_DATA_FP + 'tmc_summary.json', 'w') as f:
            json.dump([x['properties'] for x in address_records], f)

#    print len(address_records)
    compare_crashes()


#    print address_records[0]
#    compare_atrs(address_records)
#    norm = get_normalization_factor()
#    print addresses.keys()
#    print type(addresses)
#    print address_records[0]
#    plot_tmcs(addresses)





