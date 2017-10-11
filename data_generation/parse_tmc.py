import xlrd
import pandas as pd
from os import listdir, path


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

# finding date
def find_date(excel_sheet):
    sheet_c = excel_sheet.ncols
    sheet_r = excel_sheet.nrows
    date = ''
    for col in range(sheet_c):
        for row in range(sheet_r):
            cell_value = excel_sheet.cell_value(rowx=row, colx=col)
            if "date" in str(cell_value).lower():
                date = cell_value
    return date

def data_location(excel_sheet):
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

def find_address(excel_sheet):
    return excel_sheet.cell_value(rowx=0, colx=0)


def extract_data_sheet(sheet, sheet_name, sheet_data_location, counter):
    sheet_df = file_dataframe(sheet, sheet_data_location)
    sheet_df['data_id'] = counter
    return(sheet_df)

def log_data_sheet(sheet, sheet_name, sheet_data_location, counter, file_name):
    global data_info
    address = find_address(sheet)
    date = find_date(sheet)
    
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
    
    record = pd.DataFrame([(counter, address, date, east, south, west, north, sheet_name, file_name)], 
                          columns=['id','address','date','east','south','west','north','data_type','filename'])
    data_info = data_info.append(record)

def extract_and_log_data_sheet(workbook, sheet_name, counter, file_name):
    sheet_index = sheet_names.index(sheet_name)
    sheet = workbook.sheet_by_index(sheet_index)
    sheet_data_location = data_location(sheet)
    
    data_sheet = extract_data_sheet(sheet, sheet_name, sheet_data_location, counter)
    if file_name.startswith('7435_891_SOUTHAMPTON-ST'):
        print sheet_data_location
    log_data_sheet(sheet, sheet_name, sheet_data_location, counter, file_name)
    
    return(data_sheet)


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
            if motors:
                motor = extract_and_log_data_sheet(
                    workbook, motors[0], i, file_name)
                all_data = all_data.append(motor)

            peds = [col for col in sheet_names
                    if col.startswith('all peds')]
            if peds:
                pedestrian = extract_and_log_data_sheet(
                    workbook, peds[0], i, file_name)
                all_data = all_data.append(pedestrian)
        
            if 'bicycles hr.' in sheet_names:
                pedestrian = extract_and_log_data_sheet(workbook, 'bicycles hr.', i, file_name)
                all_data = all_data.append(pedestrian)

    all_data.reset_index(drop=True, inplace=True)    
    data_info.reset_index(drop=True, inplace=True)

    all_data = all_data.apply(pd.to_numeric, errors='ignore')
    data_info = data_info.apply(pd.to_numeric, errors='ignore')

    all_data.to_csv(path_or_buf=data_directory + 'all_data.csv', index=False)
    data_info.to_csv(path_or_buf=data_directory + 'data_info.csv', index=False)

    print data_info
    print all_data
    print data_info.filename.nunique()

    all_joined = pd.merge(left=all_data,right=data_info, left_on='data_id', right_on='id')
    all_joined.groupby(['data_type']).sum()

    print data_info.head()
    
print i
