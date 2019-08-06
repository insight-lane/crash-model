import json
import os
import rtree
import argparse
from . import util
from .record import Record
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
import geopandas as gpd
from sklearn.neighbors import KNeighborsRegressor
import sys


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data/processed')
STANDARDIZED_DATA_FP = os.path.join(BASE_DIR, 'data', 'standardized')


def update_properties(segments, df, features):
    """
    Takes a segment list and a dataframe, and writes out updated
    intersection and non-intersection segments
    Args:
        segments - a list of intersection and non-intersection segments
        df - a dataframe of features
        features - a list of features to extract from the dataframe
    Returns:
        nothing - writes to inter_segments.geojson and non_inter_segments.geojson
    """

    df = df[['id'] + features]
    df = df.fillna('')
    # a dict where the id is the key and the value is the feature

    values = df.to_dict()
    id_mapping = {value: key for key, value in values['id'].items()}
    for segment in segments:
        seg_id = str(segment.properties['id'])

        if seg_id in id_mapping:
            for feature in features:
                if values[feature][id_mapping[seg_id]] == '':
                    segment.properties[feature] = None
                else:
                    segment.properties[feature] = values[feature][id_mapping[seg_id]]

    inters = [x for x in segments if util.is_inter(x.properties['id'])]
    non_inters = [x for x in segments if not util.is_inter(x.properties['id'])]
    util.write_segments(non_inters, inters, os.path.join(
        PROCESSED_DATA_FP, 'maps'))


def read_volume():
    """
    Read the standardized volume data, snap to nearest segments,
    and read relevant data
    Args:
        None - reads from file
    Returns:
        volume - a list of geojson points with volume properties
    """
    volume = []
    with open(os.path.join(STANDARDIZED_DATA_FP, 'volume.json')) as data_file:
        data = json.load(data_file)
        for record in data:

            if record['location']['longitude'] and record[
                    'location']['latitude']:

                properties = {
                    'speed': record['speed']['averageSpeed'],
                    'heavy': record['volume']['totalHeavyVehicles'],
                    'light': record['volume']['totalLightVehicles'],
                    'bikes': record['volume']['bikes'],
                    'volume': record['volume']['totalVolume'],
                    'orig': record['location']['address']
                }

                properties['location'] = {
                    'latitude': float(record['location']['latitude']),
                    'longitude': float(record['location']['longitude'])
                }
                record = Record(properties)

                volume.append(record)

    return [{'point': x.point, 'properties': x.properties} for x in volume]

    return volume


def propagate_volume():
    """
    Propagate volume from given volume data to other segments
    Args:
        None - reads segment and volume data from file
    Returns:
        None - writes results to file
    """
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
        segments_index.insert(idx, element.geometry.bounds)

    print('Created spatial index')

    volume = read_volume()

    # Find nearest atr - 20 tolerance
    print("Snapping atr to segments")
    util.find_nearest(volume, combined_seg, segments_index, 20)

    # Should deprecate once imputed atrs are used, but for the moment
    # this is needed for make_canon_dataset
    with open(os.path.join(PROCESSED_DATA_FP, 'snapped_atrs.json'), 'w') as f:
        json.dump([x['properties'] for x in volume], f)

    volume_df = json_normalize(volume)
    
    volume_df = volume_df[[
        'properties.near_id',
        'properties.heavy',
        'properties.light',
        'properties.bikes',
        'properties.speed',
        'properties.volume'
    ]]

    # rename columns
    volume_df.columns = [
        'id',
        'heavy',
        'light',
        'bikes',
        'speed',
        'volume'
    ]

    # remove atrs that didn't bind to a segment
    before = len(volume_df)
    volume_df = volume_df[volume_df['id'] != '']
    after = len(volume_df)
    print(('Removed {} volume(s) that did not bind to a segment'.format(
        before-after)))

    # change dtypes
    volume_df['id'] = volume_df['id']
    volume_df['heavy'] = volume_df['heavy'].astype(int)
    volume_df['light'] = volume_df['light'].astype(int)
    volume_df['bikes'] = volume_df['bikes'].astype(int)
    volume_df['speed'] = volume_df['speed'].astype(int)
    volume_df['volume'] = volume_df['volume'].astype(int)

    # remove ATRs that bound to same segment
    volume_df.drop_duplicates('id', inplace=True)
    print(('Dropped {} volumes that bound to same segment as another'.format(
        after - len(volume_df))))

    # create dataframe of all segments
    seg_df = pd.DataFrame([(x.geometry, x.properties) for x in combined_seg])
    seg_df.columns = ['geometry', 'seg_id']
    
    # seg_id column is read in as a dictionary
    # separate, get `id` value, and rejoin
    seg_df = pd.concat([seg_df['geometry'], seg_df.seg_id.apply(
        pd.Series)['id']], axis=1)

    # change to geo df for centroid method
    seg_gdf = gpd.GeoDataFrame(seg_df['id'], geometry=seg_df['geometry'])

    # create two columns for x and y of centroid of segment
    seg_gdf['px'] = seg_gdf.geometry.centroid.apply(lambda p: p.x)
    seg_gdf['py'] = seg_gdf.geometry.centroid.apply(lambda p: p.y)
    
    # merge atrs and seg_gdf
    merged_df = pd.merge(seg_gdf, volume_df, on='id', how='left')

    print(('Length of merged: {}, Length of seg_gdf: {}'.format(
        len(merged_df), len(seg_gdf))))
    
    # values to run KNN on
    col_to_predict = ['heavy', 'light', 'bikes', 'speed', 'volume']

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
    update_properties(
        combined_seg,
        merged_df,
        ['volume', 'speed', 'volume_coalesced', 'speed_coalesced']
    )


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
        STANDARDIZED_DATA_FP = os.path.join(args.datadir, 'standardized')

    if not os.path.exists(os.path.join(STANDARDIZED_DATA_FP, 'volume.json')):
        print("No volumes found, skipping...")
        sys.exit()

    propagate_volume()


