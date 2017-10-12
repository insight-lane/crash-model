"""
Title: historical_crash_map.py
 
Author: @alicefeng
 
This script creates the data needed to power the map of crashes that occurred on Boston's
streets in 2016 along with an overlay of our model predictions.  It preps weekly model
output for joining on the geometries of the predicted segments to enable mapping.  Finally,
it exports this joined data as a GeoJSON file to be used in the map.

It also generates the data used for the bar graph of total weekly crashes.

This file only needs to be run once to generate the dataset prior to
using the map for the first time.

Inputs:
    vz_predict_dataset.csv (i.e., the canonical dataset)
    csv of model predictions
    inter_and_non_int.shp

Output:
    geojson of predictions merged with geometries
    weekly_crashes.csv
"""

#Import the necessary Python moduless
import pandas as pd
import geopandas as gpd
import shapely.geometry

fp = '../data/processed/'

# read in model output and reformat
car = pd.read_csv(fp + 'car_preds_weekly_named.csv', dtype={'segment_id': str})
week_cols = list(car.columns[2:56])
car_weekly = pd.melt(car, id_vars=['segment_id', 'st_name'], value_vars=week_cols,
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

# export joined predictions as GeoJSON 
# IMPORTANT: it's a known bug that Fiona won't let you overwrite GeoJSON files so you have 
# to first delete the file from your hard drive before re-exporting
car_preds = car_joined[['geometry', 'id', 'week', 'pred', 'st_name']]
car_preds.to_file("car_preds_named.json", driver='GeoJSON')



# read in historical crash data
crashes = pd.read_csv(fp + 'vz_predict_dataset.csv', dtype={'segment_id': str})

# roll up crashes to the weekly level
weekly_crashes = crashes.groupby(['week'], as_index=False)['crash'].sum()
weekly_crashes.to_csv(fp + 'weekly_crashes.csv', index=False)
