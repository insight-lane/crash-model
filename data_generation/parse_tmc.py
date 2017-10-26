import xlrd
import pandas as pd
from os import listdir, path
from os.path import exists as path_exists
import re
from dateutil.parser import parse
from ATR_util import geocode_address, read_shp, find_nearest
from ATR_util import csv_to_projected_records, get_hourly_rates
import rtree
import folium
from ATR_util import read_segments

RAW_DATA_FP = '../data/raw/'
PROCESSED_DATA_FP = '../data/processed/'
ATR_FP = '../data/raw/AUTOMATED TRAFFICE RECORDING/'


def file_dataframe(excel_sheet, data_location):
    column_time = data_location['columns'][0]
    column_east = column_time + 1
    column_south = column_time + 2
    column_west = column_time + 3
    column_north = column_time + 4
    
    start_r = data_location['rows'][0] + 3
    end_r = data_location['rows'][1]
    
    times = excel_sheet.col_values(column_time,start_r,end_r)
    times_strip = [x.strip() for x in times]
    east = excel_sheet.col_values(column_east,start_r,end_r)
    south = excel_sheet.col_values(column_south,start_r,end_r)
    west = excel_sheet.col_values(column_west,start_r,end_r)
    north = excel_sheet.col_values(column_north,start_r,end_r)

    columns = ['times', 'east', 'south', 'west', 'north']
    return(pd.DataFrame({'times':times_strip, 'east':east, 'south':south, 'west':west, 'north':north}, columns=columns))


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
    return pd.DataFrame.from_records([
        ('start', start_c, start_r),
        ('end', end_c, end_r)
    ], columns=['value', 'columns', 'rows'])


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
    return parse(segments[len(segments) - 1])


def find_address(filename):
    """
    Parses out filename to give an intersection
    Args:
        filename
    Returns:
        address, latitude, longitude
    """
    intersection = filename.split('_')[2]
    streets = intersection.split(',')
    streets = [re.sub('-', ' ', s) for s in streets]
    # Strip out space at beginning of street name if it's there
    streets = [s if s[0] != ' ' else s[1:len(s)] for s in streets]

    if len(streets) >= 2:
        intersection = streets[0] + ' and ' + streets[1] + ' Boston, MA'
        result = geocode_address(intersection)
        return result
    return None, None, None


def extract_data_sheet(sheet, sheet_data_location, counter):
    sheet_df = file_dataframe(sheet, sheet_data_location)
    sheet_df['data_id'] = counter
    return(sheet_df)


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

    data_sheet = extract_data_sheet(sheet, sheet_data_location, counter)
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
    return data_sheet, data_info


def process_format1(workbook, filename, address, date,
                    counter, motor_col, ped_col, bike_col, all_data,
                    data_info):

    if motor_col:
        counter += 1
        motor, data_info = extract_and_log_data_sheet(
            workbook, motor_col, counter, filename, address, date, data_info)
        all_data = all_data.append(motor)

    if ped_col:
        counter += 1
        pedestrian, data_info = extract_and_log_data_sheet(
            workbook, ped_col, counter, filename, address, date, data_info)
        all_data = all_data.append(pedestrian)
        
    if bike_col:
        counter += 1
        bike, data_info = extract_and_log_data_sheet(
            workbook, bike_col, counter, filename, address, date, data_info)
        all_data = all_data.append(bike)
    return all_data, counter, data_info, motor if motor else None


def get_geocoded():
    """
    Gets the geocoded turning movement count addresses

    If no existing geocoded tmc file exists, extracts the addresses
    and dates from the filenames, geocodes them, and writes results
    to file
    If there's an existing geocoded tmc file, read it in

    Args:
        None - file is hardcoded
    Results:
        addresses dataframe
    """
    addresses = pd.DataFrame()
    geocoded_file = PROCESSED_DATA_FP + 'geocoded_tmcs.csv'
    if not path_exists(geocoded_file):
        print 'No geocoded tmcs found, generating'
        data_directory = RAW_DATA_FP + 'TURNING MOVEMENT COUNT/'
        for filename in listdir(data_directory):
            if filename.endswith('.XLS'):
                address, latitude, longitude = find_address(filename)
                date = find_date(filename)

                address_record = pd.DataFrame([(
                    filename,
                    address,
                    latitude,
                    longitude,
                    date)],
                    columns=[
                        'File',
                        'Address',
                        'Latitude',
                        'Longitude',
                        'Date'
                    ])
                addresses = addresses.append(address_record)
        addresses.to_csv(
            path_or_buf=geocoded_file, index=False)
    else:
        print "reading from " + geocoded_file
        addresses = pd.read_csv(geocoded_file)

    address_records = csv_to_projected_records(geocoded_file,
                                               x='Longitude', y='Latitude')
    print "Read in data from {} records".format(len(address_records))

    inter = read_shp(PROCESSED_DATA_FP + 'maps/inters_segments.shp')
    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(inter):
        segments_index.insert(idx, element[0].bounds)
    print "Snapping tmcs to intersections"
    find_nearest(address_records, inter, segments_index, 20)

    # Find_nearest got the nearest intersection id, but we want to compare
    # against all segments too.  They don't always match, which may be
    # something we'd like to look into
    for address in address_records:
        address['properties']['near_intersection_id'] = \
                    address['properties']['near_id']
        address['properties']['near_id'] = ''

    combined_seg, segments_index = read_segments()
    find_nearest(address_records, combined_seg, segments_index, 20)

    return addresses, address_records


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
    atrs = csv_to_projected_records(PROCESSED_DATA_FP + 'geocoded_atrs.csv',
                                    x='lng', y='lat')
    for atr in atrs:
        properties = atr['properties']
        if properties['lat']:
            folium.CircleMarker(
                location=[float(properties['lat']), float(properties['lng'])],
                fill_color='green', fill=True, fill_opacity=.7, color='grey',
                radius=6).add_to(points)

    points.save('map.html')


def parse_tmcs(addresses):

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

    i = 0
    for row in addresses.iterrows():

        filename = row[1]['File']
#        print filename
        address = row[1]['Address']
        date = row[1]['Date']
        file_path = path.join(data_directory, filename)
        workbook = xlrd.open_workbook(file_path)
        sheet_names = [x.lower() for x in workbook.sheet_names()]
        motors = [col for col in sheet_names
                  if col.startswith('all motors')]
        peds = [col for col in sheet_names
                if col.startswith('all peds')]

        if motors or peds or 'bicycles hr.' in sheet_names:
            all_data, i, data_info, motor = process_format1(
                workbook, filename, address, date,
                i, motors[0] if motors else None,
                peds[0] if peds else None,
                'bicycles hr.' if 'bicycles hr.' in sheet_names else None,
                all_data, data_info)

    all_data.reset_index(drop=True, inplace=True)
    data_info.reset_index(drop=True, inplace=True)

    all_data = all_data.apply(pd.to_numeric, errors='ignore')
    data_info = data_info.apply(pd.to_numeric, errors='ignore')

    # All data and data_info are temporary files that when we're done with
    # cleanup will be obsolete
    # data_info gives description of the intersection/filename, what type of
    # vehicle/pedestrian is being counted, and an id indexing into all_data
    # all_data gives an hourly count in each direction
    all_data.to_csv(path_or_buf=data_directory + 'all_data.csv', index=False)
    data_info.to_csv(path_or_buf=data_directory + 'data_info.csv', index=False)

#    print data_directory
#    print data_info[10]
    print len(all_data)
    print data_info.filename.nunique()
    print all_data.keys()
    print data_info.keys()
    all_joined = pd.merge(left=all_data,right=data_info, left_on='data_id', right_on='id')
#    print all_joined.groupby(['data_type']).sum()
#    print addresses

#    print data_info.head()


def get_normalization_factor():
    """
    TMC counts are only over 11 hours
    Normalize using average rates of the 24 hour ATRs,
    since they're pretty consistent
    """
    # Read in atr lats
    atrs = csv_to_projected_records(PROCESSED_DATA_FP + 'geocoded_atrs.csv',
                                    x='lng', y='lat')

    files = [ATR_FP +
             atr['properties']['filename'] for atr in atrs]
    all_counts = get_hourly_rates(files)
    counts = [sum(i)/len(all_counts) for i in zip(*all_counts)]

    return sum(counts[7:18])

if __name__ == '__main__':

    addresses, address_records = get_geocoded()

    norm = get_normalization_factor()
    print addresses.keys()
#    print type(addresses)
    print address_records[0]
    # plot_tmcs(addresses)
    # parse_tmcs(addresses)
