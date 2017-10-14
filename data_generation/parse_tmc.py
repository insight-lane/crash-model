import xlrd
import pandas as pd
from os import listdir, path
import re
from dateutil.parser import parse
from ATR_util import geocode_address


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


def find_date(excel_sheet):
    """
    Parse out the date
    Args:
        excel_sheet
    Returns: datetime date object
    """
    sheet_c = excel_sheet.ncols
    sheet_r = excel_sheet.nrows
    date = ''
    row = 0
    while row < sheet_r and not date:
        col = 0
        while col < sheet_c and not date:
            cell_value = excel_sheet.cell_value(rowx=row, colx=col)
            if "date" in str(cell_value).lower():
                date = cell_value
            col += 1
        row += 1

    date = date.lower()
    # Dates can be in the form 'Date - <date>'
    stripped_date = re.sub('date(\s+\-)?(\s+)?', '', date)
    if stripped_date:
        return parse(stripped_date).date()

    # If we didn't already figure out a date,
    # look at the column to the right of the date field
    # This is not very robust, e.g. it will
    # break if whatever is to the right of the
    # column containing 'date' is not a date
    if col < sheet_c:
        new_date = excel_sheet.cell_value(rowx=row-1, colx=col)
        if new_date:
            date = parse(new_date).date()

    return date


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
    global data_info
    
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
    data_info = data_info.append(record)


def extract_and_log_data_sheet(workbook, sheet_name, counter, filename,
                               address, date):
    sheet_index = sheet_names.index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)
    sheet_data_location = data_location(sheet)
    
    data_sheet = extract_data_sheet(sheet, sheet_data_location, counter)
    log_data_sheet(sheet, sheet_name, sheet_data_location, counter, filename,
                   address, date)
    
    return(data_sheet)


def process_format1(workbook, filename,
                    counter, motor_col, ped_col, bike_col, all_data):

    # dates are same across these sheets
    sheet_name = ''
    if motors:
        sheet_name = motors[0]
    elif peds:
        sheet_name = peds[0]
    else:
        sheet_name = 'bicycles hr.'
    sheet_index = sheet_names.index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)
    address, latitude, longitude = find_address(filename)
    date = find_date(sheet)

    if motor_col:
        counter += 1
        motor = extract_and_log_data_sheet(
            workbook, motor_col, counter, filename, address, date)
        all_data = all_data.append(motor)

    if ped_col:
        counter += 1
        pedestrian = extract_and_log_data_sheet(
            workbook, ped_col, counter, filename, address, date)
        all_data = all_data.append(pedestrian)
        
    if bike_col:
        counter += 1
        bike = extract_and_log_data_sheet(
            workbook, bike_col, counter, filename, address, date)
        all_data = all_data.append(bike)
    return all_data, counter

if __name__ == '__main__':

    data_directory = '../data/raw/TURNING MOVEMENT COUNT/'
    data_file_names = listdir(data_directory)

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

    for file_name in data_file_names:
        if file_name.endswith('.XLS'):
            file_path = path.join(data_directory, file_name)
            workbook = xlrd.open_workbook(file_path)
            sheet_names = [x.lower() for x in workbook.sheet_names()]

            motors = [col for col in sheet_names
                      if col.startswith('all motors')]
            peds = [col for col in sheet_names
                    if col.startswith('all peds')]

            if motors or peds or 'bicycles hr.' in sheet_names:
                all_data, i = process_format1(
                    workbook, file_name, i, motors[0] if motors else None,
                    peds[0] if peds else None,
                    'bicycles hr.' if 'bicycles hr.' in sheet_names else None,
                    all_data)

    all_data.reset_index(drop=True, inplace=True)    
    data_info.reset_index(drop=True, inplace=True)

    all_data = all_data.apply(pd.to_numeric, errors='ignore')
    data_info = data_info.apply(pd.to_numeric, errors='ignore')

    all_data.to_csv(path_or_buf=data_directory + 'all_data.csv', index=False)
    data_info.to_csv(path_or_buf=data_directory + 'data_info.csv', index=False)

#    print data_directory
#    print data_info[10]
#    print all_data
    print data_info.filename.nunique()

    all_joined = pd.merge(left=all_data,right=data_info, left_on='data_id', right_on='id')
    print all_joined.groupby(['data_type']).sum()

#    print data_info.head()
    

