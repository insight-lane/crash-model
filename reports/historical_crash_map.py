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
    dow_crashes.csv
    hourly_crashes.csv
"""

#Import the necessary Python moduless
import pandas as pd
import geopandas as gpd
import shapely.geometry
from shapely.geometry import Point
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

RAW_FP = BASE_DIR + '/data/raw'
MAP_FP = BASE_DIR + '/data/processed/maps'
DATA_FP = BASE_DIR + '/data/processed'

### Generate historical crash dataset
# read CAD data
cad = pd.read_csv(RAW_FP + '/cad_crash_events_with_transport_2016_wgs84.csv', parse_dates=['CALENDAR_DATE'])

# create points from lat/lon and read into geodataframe
geometry = [Point(xy) for xy in zip(cad.X, cad.Y)]
crs = {'init': 'epsg:4326'}

# get week of the year
cad['week'] = cad['CALENDAR_DATE'].dt.week
df = cad['week']

geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
geo_df.to_file('cad.geojson', driver="GeoJSON")





### Generate model predictions dataset
# read in model output and reformat
car = pd.read_csv(DATA_FP + '/car_preds_weekly_named.csv', dtype={'segment_id': str})
week_cols = list(car.columns[2:56])
car_weekly = pd.melt(car, id_vars=['segment_id', 'st_name'], value_vars=week_cols,
                     var_name='week', value_name='pred')
car_weekly['week'] = pd.to_numeric(car_weekly['week'])
car_weekly['id'] = car_weekly['segment_id']


# Read in shapefile as a GeoDataframe
streets = gpd.read_file(MAP_FP + '/inter_and_non_int.shp')

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
crashes = pd.read_csv(DATA_FP + '/vz_predict_dataset.csv', dtype={'segment_id': str})

# roll up crashes to the weekly level
weekly_crashes = crashes.groupby(['week'], as_index=False)['crash'].sum()
weekly_crashes.to_csv('weekly_crashes.csv', index=False)


### Generate day of week crash dataset
weekday_map= {0:'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}
cad['dow'] = cad['CALENDAR_DATE'].dt.dayofweek
cad['dow_name'] = cad['dow'].map(weekday_map)
dow_crashes = cad.groupby(['dow', 'dow_name'], as_index=False)['N_EVENTS'].sum()
dow_crashes.to_csv('dow_crashes.csv', index=False)


### Generate time of day crash dataset
cad['hour'] = cad['TIME'].str.split(':').str.get(0).astype(int)

# add indicator for weekday/weekend to see if there's a difference in crash distribution
cad['weekend'] = (cad['dow']//5==1).astype(int)

hourly_crashes = cad.groupby(['weekend', 'hour'], as_index=False)['N_EVENTS'].sum()
hourly_crashes['pct_crash'] = hourly_crashes.groupby(['weekend'])['N_EVENTS'].apply(lambda x: x/x.sum())
hourly_crashes['weekend_lbl'] = hourly_crashes['weekend'].map({0:'Weekday', 1:'Weekend'})
hourly_crashes.to_csv('hourly_crashes.csv', index=False)
