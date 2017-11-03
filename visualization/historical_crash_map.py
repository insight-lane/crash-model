"""
Title: historical_crash_map.py
 
Author: @alicefeng
 
This script creates the datasets needed to power MVP. This file only needs to be
run once prior to using the map for the first time.

Inputs:
    cad_crash_events_with_transport_2016_wgs84.csv
    vz_predict_dataset.csv (i.e., the canonical dataset)
    csv of model predictions
    inter_and_non_int.shp

Output:
    geojson of historical crash data
    geojson of predictions merged with geometries
    weekly_crashes.csv
"""

#Import the necessary Python moduless
import pandas as pd
import geopandas as gpd
import shapely.geometry
from shapely.geometry import Point

fp = '../data/processed/'

### Generate historical crash dataset
# read CAD data
df = pd.read_csv('data/raw/cad_crash_events_with_transport_2016_wgs84.csv')

# create points from lat/lon and read into geodataframe
geometry = [Point(xy) for xy in zip(df.X, df.Y)]
crs = {'init': 'epsg:4326'}

# get week of the year
df['timestamp'] = pd.to_datetime(df['CALENDAR_DATE'])
df['week'] = df['timestamp'].dt.week
df = df['week']

geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
geo_df.to_file('cad.geojson', driver="GeoJSON")





### Generate model predictions dataset
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





### Generate weekly crash dataset
# read in historical crash data
crashes = pd.read_csv(fp + 'vz_predict_dataset.csv', dtype={'segment_id': str})

# roll up crashes to the weekly level
weekly_crashes = crashes.groupby(['week'], as_index=False)['crash'].sum()
weekly_crashes.to_csv(fp + 'weekly_crashes.csv', index=False)
