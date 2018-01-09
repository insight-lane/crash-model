# -*- coding: utf-8 -*-
import os
import subprocess

DATA_FP = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)))) + '/osm-data/'


if __name__ == '__main__':

    city = 'Boston, Massachusetts, USA'

    subprocess.check_call([
        'python',
        '-m',
        'data.osm_create_maps',
        city,
        DATA_FP
    ])

