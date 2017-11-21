# -*- coding: utf-8 -*-
import os
import subprocess


if __name__ == '__main__':

    path = os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))) + '/data/raw/'
    filename = path + 'Boston_Segments.shp'

    subprocess.check_call([
        'python',
        '-m',
        'data.extract_intersections',
        filename])

    subprocess.check_call([
        'python',
        '-m',
        'data.create_segments',
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.join_segments_crash_concern',
    ])

    subprocess.check_call([
        'python',
        '-m',
        'data.ATR_scraping.geocode_snap_ATRs'
    ])
        

