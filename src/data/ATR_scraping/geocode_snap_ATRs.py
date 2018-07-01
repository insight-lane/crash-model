import json
import os
import csv
import rtree
import pyproj
import argparse
from .. import util
from . import ATR_util
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
import geopandas as gpd
from sklearn.neighbors import KNeighborsRegressor
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

ATR_FP = os.path.join(BASE_DIR, 'data/raw/volume/ATRs')
PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')

PROJ = pyproj.Proj(init='epsg:3857')


def geocode_and_parse(atrs, forceupdate):

    if not os.path.exists(os.path.join(
            PROCESSED_DATA_FP, 'geocoded_atrs.csv')) or forceupdate:
        print("No geocoded_atrs.csv found, geocoding addresses")

        # geocode, parse result - address, lat long
        results = []
        for atr in atrs:
            atr = atr
            if ATR_util.is_readable_ATR(os.path.join(ATR_FP, atr)):
                atr_address = ATR_util.clean_ATR_fname(
                    os.path.join(ATR_FP, atr))
                print(atr_address)
                geocoded_add, lat, lng = util.geocode_address(atr_address)
                print(str(geocoded_add) + ',' + str(lat) + ',' + str(lng))
                vol, speed, motos, light, heavy = ATR_util.read_ATR(
                    os.path.join(ATR_FP, atr))
                r = [
                    atr_address,
                    geocoded_add,
                    lat,
                    lng,
                    vol,
                    speed,
                    motos,
                    light,
                    heavy,
                    atr
                ]
                results.append(r)
                print(('Number geocoded: {}'.format(len(results))))

        with open(os.path.join(
                PROCESSED_DATA_FP, 'geocoded_atrs.csv'), 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow([
                'orig',
                'geocoded',
                'lat',
                'lng',
                'volume',
                'speed',
                'motos',
                'light',
                'heavy',
                'filename'
            ])
            for r in results:
                writer.writerow(r)
    else:
        print('geocoded_atrs.csv already exists, skipping geocoding')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory.")
    # Can force update
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether force update the maps')

    args = parser.parse_args()
    if args.datadir:
        PROCESSED_DATA_FP = os.path.join(args.datadir, 'processed')
        ATR_FP = os.path.join(
            args.datadir, 'raw', 'volume', 'ATRs')
        if not os.path.exists(ATR_FP):
            print("NO ATR directory found, skipping...")
            sys.exit()
    atrs = os.listdir(ATR_FP)

    geocode_and_parse(atrs, args.forceupdate)
    # Read in segments
    inter = util.read_geojson(os.path.join(
        PROCESSED_DATA_FP, 'maps/inters_segments.geojson'))
    non_inter = util.read_geojson(
        os.path.join(PROCESSED_DATA_FP, 'maps/non_inters_segments.geojson'))
    print("Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter)))

    # Combine inter + non_inter
    combined_seg = inter + non_inter

    # # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element[0].bounds)

    print('Created spatial index')

    # Read in atr lats
    atrs = util.csv_to_projected_records(
        os.path.join(PROCESSED_DATA_FP, 'geocoded_atrs.csv'), x='lng', y='lat')
    print("Read in data from {} atrs".format(len(atrs)))

    # Find nearest atr - 20 tolerance
    print("Snapping atr to segments")
    util.find_nearest(atrs, combined_seg, segments_index, 20)

    # Should deprecate once imputed atrs are used, but for the moment
    # this is needed for make_canon_dataset
    with open(os.path.join(PROCESSED_DATA_FP, 'snapped_atrs.json'), 'w') as f:
        json.dump([x['properties'] for x in atrs], f)

    atrs_df = json_normalize(atrs)
    
    atrs_df = atrs_df[['properties.near_id',
                        'properties.heavy', 
                        'properties.light', 
                        'properties.motos', 
                        'properties.speed',
                        'properties.volume']]

    # rename columns
    atrs_df.columns = ['id',
                       'heavy',
                       'light',
                       'motos',
                       'speed',
                       'volume']

    # remove atrs that didn't bind to a segment
    before = len(atrs_df)
    atrs_df = atrs_df[atrs_df['id'] != '']
    after = len(atrs_df)
    print(('Removed {} ATR(s) that did not bind to a segment'.format(before-after)))

    # change dtypes
    atrs_df['id'] = atrs_df['id']
    atrs_df['heavy'] = atrs_df['heavy'].astype(int)
    atrs_df['light'] = atrs_df['light'].astype(int)
    atrs_df['motos'] = atrs_df['motos'].astype(int)
    atrs_df['speed'] = atrs_df['speed'].astype(int)
    atrs_df['volume'] = atrs_df['volume'].astype(int)

    # remove ATRs that bound to same segment
    atrs_df.drop_duplicates('id', inplace=True)
    print(('Dropped {} ATRs that bound to same segment as another'.format(after - len(atrs_df))))

    # create dataframe of all segments
    seg_df = pd.DataFrame(combined_seg)
    seg_df.columns = ['geometry', 'seg_id']
    
    # seg_id column is read in as a dictionary
    # separate, get `id` value, and rejoin
    seg_df = pd.concat([seg_df['geometry'], seg_df.seg_id.apply(pd.Series)['id']], axis=1)

    # change to geo df for centroid method
    seg_gdf = gpd.GeoDataFrame(seg_df['id'], geometry=seg_df['geometry'] )

    # create two columns for x and y of centroid of segment
    seg_gdf['px'] = seg_gdf.geometry.centroid.apply(lambda p: p.x)
    seg_gdf['py'] = seg_gdf.geometry.centroid.apply(lambda p: p.y)
    
    # merge atrs and seg_gdf
    merged_df = pd.merge(seg_gdf, atrs_df, on='id', how='left')

    print(('Length of merged: {}, Length of seg_gdf: {}'.format(len(merged_df), len(seg_gdf))))
    
    # values to run KNN on
    col_to_predict = ['heavy','light','motos','speed','volume']

    for col in col_to_predict:
        print(('Predicting missing values for {} column'.format(col)))
        # split into X, y, X_pred for KNN regression
        X = merged_df[merged_df[col].notnull()][['px', 'py']]
        y = merged_df[merged_df[col].notnull()][col]
        X_pred = merged_df[merged_df[col].isnull()][['px', 'py']]

        # predict on missing segments
        knn = KNeighborsRegressor(3, weights='distance')
        y_pred = knn.fit(X, y).predict(X_pred)

        # create empty column to fill with predicted values
        col_name = col + '_pred'
        merged_df[col_name] = np.nan

        merged_df.loc[merged_df[col].isnull(), col_name] = y_pred

    # coalesce all columns
    print('Creating coalesced columns')

    for col in col_to_predict:
        col_name = col + '_coalesced'
        pred_col = col + '_pred'
        merged_df[col_name] = merged_df[col].combine_first(merged_df[pred_col])

    # drop predicted columns
    pred_cols = [col + '_pred' for col in col_to_predict]

    # drop 
    merged_df.drop(labels=pred_cols, axis=1, inplace=True)
    # in pandas 0.21.0 do:
    # merged_df.drop(columns=pred_cols, axis=1, inplace=True)

    # write to csv
    print('Writing to CSV')
    output_fp = os.path.join(PROCESSED_DATA_FP, 'atrs_predicted.csv')
    # force id into string
    merged_df['id'] = merged_df['id'].astype(str)
    merged_df.to_csv(output_fp, index=False)
