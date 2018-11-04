import os
from data.util import read_geocode_cache, lookup_address
import re
import openpyxl
from collections import OrderedDict
import csv
from dateutil.parser import parse


class BostonVolumeParser:
    """
    Read ATRs and TMCs into standardized volume format
    """

    def __init__(self, datadir):
        self.BASE_FP = datadir
        self.PROCESSED_DATA_FP = os.path.join(self.BASE_FP, 'processed')
        self.RAW_FP = os.path.join(self.BASE_FP, "raw", "volume")
        self.ATR_FP = os.path.join(self.RAW_FP, "ATRs")
        self.CURR_FP = os.path.dirname(os.path.abspath(__file__))

    def get_volume(self):
        """
        return volume counts for Boston
        """
        atr_volume = self.get_ATRs()

        return atr_volume

    def get_ATRs(self):

        print("Standardizing volume data for Boston")

        if not os.path.exists(self.ATR_FP):
            print("NO ATR directory found, skipping...")
            return []
        atrs = os.listdir(self.ATR_FP)

        if not os.path.exists(os.path.join(self.PROCESSED_DATA_FP,
                                           'geocoded_addresses.csv')):
            print("No geocoded_addresses.csv found, geocoding addresses")

        cached = read_geocode_cache(filename=os.path.join(
            self.PROCESSED_DATA_FP, 'geocoded_addresses.csv'))

        results = []
        geocoded_count = [0, 0, 0]
        for atr in atrs:
            if self.is_readable_ATR(os.path.join(self.ATR_FP, atr)):
                atr_address = self.clean_ATR_fname(
                    os.path.join(self.ATR_FP, atr))
                print(atr_address)
                geocoded_add, lat, lng, status = lookup_address(
                    atr_address, cached)

                cached[atr_address] = [geocoded_add, lat, lng, status]

                print(str(geocoded_add) + ',' + str(lat) + ',' + str(lng))
                vol, speed, motos, light, heavy, date, counts = self.read_ATR(
                    os.path.join(self.ATR_FP, atr))
                if status == 'S':
                    geocoded_count[0] += 1
                elif status == 'F':
                    geocoded_count[1] += 1
                else:
                    geocoded_count[2] += 1

                r = OrderedDict([
                    ("startDateTime", date),
                    ("location", OrderedDict([
                        ("latitude", float(lat) if lat else ''),
                        ("longitude", float(lng) if lng else ''),
                        ("address", geocoded_add if geocoded_add else '')
                    ])),
                    ("volume", OrderedDict([
                        ("totalVolume", vol),
                        ("totalLightVehicles", light),
                        ("totalHeavyVehicles", heavy),
                        ("bikes", motos),
                        ("hourlyVolume", counts)
                    ])),
                    ("speed", OrderedDict([
                        ("averageSpeed", speed)
                    ]))
                ])
                results.append(r)

        print('Number successfully geocoded: {}'.format(geocoded_count[0]))
        print('Unable to geocode: {}'.format(geocoded_count[1]))
        print('Timed out on {} addresses'.format(geocoded_count[2]))

        # Write out the cache
        with open(os.path.join(self.PROCESSED_DATA_FP,
                               'geocoded_addresses.csv'), 'w') as csvfile:

            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([
                'Input Address',
                'Output Address',
                'Latitude',
                'Longitude',
                'Status'
            ])

            for name, value in cached.items():
                writer.writerow([name] + value)
        return results

    def is_readable_ATR(self, fname):
        """
        Function to check if ATR is of type we want to read
        checking for 3 conditions

         1) of 'XXX' type (contains speed, volume, and classification data)
         2) of 24-HOURS type
         3) .XLSX file type
        """

        # split file name so we can check relevant info
        meta_info = fname.split('_')
        file_type = meta_info[8].split('.')[1]

        # only look at files that are .xlsx, are 24 hours, and are of type XXX
        if (meta_info[7] == 'XXX') and (
                meta_info[6] == '24-HOURS') and (file_type == 'XLSX'):
            return True
        else:
            return False

    def clean_ATR_fname(self, fname):
        """
        Clean filename to prepare for geocoding
        EX:
        7362_NA_NA_147_TRAIN-ST_DORCHESTER_24-HOURS_XXX_03-19-2014.XLSX
        to
        147 TRAIN ST Boston, MA
        """

        # split address on underscore character
        atr_address = fname.split('_')
        # combine elements that make up the address
        atr_address = ' '.join(atr_address[3:5])
        # replace '-' with spaces
        atr_address = re.sub('-', ' ', atr_address)
        atr_address += ' Boston, MA'
        return atr_address

    def read_ATR(self, fname):
        """
        Function to read ATR data
        data to collect:
        mean speed, volume, motos (# of motorcycles), light(# of cars/trucks),
        and heavy(# of heavy duty vehicles)
        """

        # data_only=True so as to not read formulas
        wb = openpyxl.load_workbook(fname, data_only=True)
        sheet_names = wb.sheetnames

        # get total volume cell F106
        if 'Volume' in sheet_names:
            sheet = wb['Volume']
            vol = sheet['F106'].value
        else:
            vol = 0

        # get mean speed data
        if 'Speed Combined' in sheet_names:
            sheet = wb['Speed Combined']
            speed = sheet['E42'].value
        elif 'Speed-1' in sheet_names:
            sheet = wb['Speed-1']
            speed = sheet['E42'].value
        else:
            speed = 0

        # get classification data
        counts = []
        if 'Classification-Combined' in sheet_names:
            sheet = wb['Classification-Combined']
            motos = sheet['D38'].value
            light = sheet['D39'].value
            heavy = sheet['D40'].value

            for row_index in range(9, 33):
                cell = "{}{}".format('O', row_index)
                val = sheet[cell].value
                counts.append(val)

        elif 'Classification-1' in sheet_names:
            sheet = wb['Classification-1']
            motos = sheet['D38'].value
            light = sheet['D39'].value
            heavy = sheet['D40'].value

            for row_index in range(9, 33):
                cell = "{}{}".format('O', row_index)
                val = sheet[cell].value
                counts.append(val)
        else:
            motos = 0
            light = 0
            heavy = 0

        date = parse(fname.split('.')[-2].split('_')[-1]).strftime("%Y-%m-%d")

        return vol, speed, motos, light, heavy, date, counts

