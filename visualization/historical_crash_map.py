"""
Title: historical_crash_map.py
 
Author: @alicefeng
 
This script creates the data needed to power the map of historical crash
data for crashes that occurred on Boston's streets in 2016.  It uses
the canonical dataset which has crash counts by week and segment and
then joins on the geometries for those segments to enable mapping.  Finally,
it exports this joined data as a GeoJSON file to be used in the map.

This file only needs to be run once to generate the dataset prior to
using the map for the first time.

Inputs:
    vz_predict_dataset.csv (i.e., the canonical dataset)
    inter_and_non_int.shp

Output:
    historical_crashes.json
"""

#Import the necessary Python moduless
import pandas as pd
import geopandas as gpd
import shapely.geometry

fp = '../data/processed/'

# read in historical crash data
# subset to only week-segments that had crashes
crashes = pd.read_csv(fp + 'vz_predict_dataset.csv', dtype={'segment_id': str})
crashes = crashes[crashes.crash>0]
crashes['id'] = crashes['segment_id'].astype('str')

# read in model output
car = pd.read_csv(fp + 'car_preds_weekly.csv', dtype={'segment_id': str})
week_cols = list(car.columns[2:])
car_weekly = pd.melt(car, id_vars=['segment_id'], value_vars=week_cols,
                     var_name='week', value_name='pred')
car_weekly['week'] = pd.to_numeric(car_weekly['week'])
car_weekly['id'] = car_weekly['segment_id']

# Read in shapefile as a GeoDataframe
streets = gpd.read_file('../data/processed/maps/inter_and_non_int.shp')

# Set the projection as EPSG:3857 since the shapefile didn't export with one
streets.crs = {'init': 'epsg:3857'}

# Then reproject to EPSG:4326 to match what Leaflet uses
streets = streets.to_crs({'init': 'epsg:4326'})

# Join geometry to the crash data
#crashes_joined = streets.merge(crashes, on='id')
car_joined = streets.merge(car_weekly, on='id')

# export joined historical crash data as GeoJSON 
# IMPORTANT: it's a known bug that Fiona won't let you overwrite GeoJSON files so you have 
# to first delete the file from your hard drive before re-exporting
#historical_crashes = crashes_joined[['geometry', 'id', 'week', 'crash']]
#historical_crashes.to_file("historical_crashes.json", driver='GeoJSON')
car_preds = car_joined[['geometry', 'id', 'week', 'pred']]
car_preds.to_file("car_preds.json", driver='GeoJSON')

# roll up crashes to the weekly level
#weekly_crashes = crashes.groupby(['week'], as_index=False)['crash'].sum()
#weekly_crashes.to_csv(fp + 'weekly_crashes.csv', index=False)
