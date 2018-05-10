"""
Title: historical_crash_map.py
 
Author: @alicefeng
 
This script creates the datasets needed to power the viz. This file only needs to be
run once prior to using the map for the first time.

Inputs (one for each city):
    jsons of crash data
    csv of model predictions
    inter_and_non_int.shp

Output:
    geojson of historical crash data
    geojson of predictions merged with geometries
    weekly_crashes.csv
    dow_crashes.csv
    hourly_crashes.csv
"""

# Import the necessary Python modules
import json
import pandas as pd
from pandas.io.json import json_normalize
import geopandas as gpd
import shapely.geometry
from shapely.geometry import Point
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)))))

DATA_FP = os.path.join(BASE_DIR, 'data')


def make_crash_df(city):
    crash_fp = os.path.join(DATA_FP, city, 'standardized', 'crashes.json')
    with open(crash_fp, 'r') as json_file:
        crashes_json = json.load(json_file)
    crashes_df = json_normalize(crashes_json)

    crashes_df['city'] = city

    crashes_df['dateOccurred'] = pd.to_datetime(crashes_df['dateOccurred'])

    # get year and ISO week number
    crashes_df['year'] = crashes_df['dateOccurred'].dt.year
    crashes_df['week'] = crashes_df['dateOccurred'].dt.week

    # some years the last week = 1, make it 52 in that case
    crashes_df.loc[(crashes_df.week==1) & (crashes_df.dateOccurred.dt.month==12), 'week'] = 52

    # some years the first few days in the year are put into week 52 of the previous week,
    # put them in week 1
    crashes_df.loc[(crashes_df.week>=52) & (crashes_df.dateOccurred.dt.month==1), 'week'] = 1

    return crashes_df[['city', 'location.latitude', 'location.longitude', 'year', 'week', 'dateOccurred']]


def make_preds_gdf(city):
    # read in model output
    seg_file = os.path.join(DATA_FP, city, 'processed', 'seg_with_predicted.csv')

    output = pd.read_csv(seg_file, dtype={'segment_id': str})
    output['id'] = output['segment_id']
    output['city'] = city

    output = output[output.year == 2017] #temporary

    # Read in shapefile as a GeoDataframe
    map_fp = os.path.join(DATA_FP, city, 'processed/maps')
    streets = gpd.read_file(map_fp + '/inter_and_non_int.shp')

    # Set the projection as EPSG:3857 since the shapefile didn't export with one
    streets.crs = {'init': 'epsg:3857'}

    # Then reproject to EPSG:4326 to match what Leaflet uses
    streets = streets.to_crs({'init': 'epsg:4326'})

    # Join geometry to the crash data
    preds_joined = streets.merge(output, on='id')

    preds = preds_joined[['geometry', 'city', 'id', 'year', 'week', 'prediction']]

    return preds


if __name__ == '__main__':


    # Generate historical crash dataset
    boston_crashes = make_crash_df("boston")
    cam_crashes = make_crash_df("cambridge")
    dc_crashes = make_crash_df("dc")

    all_crashes = pd.concat([boston_crashes, cam_crashes, dc_crashes])

    crashes_2017 = all_crashes[all_crashes.year == 2017]

    # create points from lat/lon and read into geodataframe
    geometry = [Point(xy) for xy in zip(crashes_2017['location.longitude'], crashes_2017['location.latitude'])]
    crs = {'init': 'epsg:4326'}

    df = crashes_2017[['city', 'year', 'week']]

    geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    if os.path.exists('crashes.geojson'):
        os.remove('crashes.geojson')
    geo_df.to_file('crashes.geojson', driver='GeoJSON')


    ### Generate model predictions dataset
    boston_preds = make_preds_gdf("boston")
    cam_preds = make_preds_gdf("cambridge")

    all_preds = pd.concat([boston_preds, cam_preds])

    # export joined predictions as GeoJSON 
    # IMPORTANT: it's a known bug that Fiona won't let you overwrite GeoJSON files so you have 
    # to first delete the file from your hard drive before re-exporting
    if os.path.exists('preds.json'):
        os.remove('preds.json')
    all_preds.to_file('preds.json', driver='GeoJSON')





    ### Generate weekly crash dataset
    weekly_crashes = crashes_2017.groupby(['city', 'year', 'week']).size().reset_index(name='counts')
    weekly_crashes.to_csv('weekly_crashes.csv', index=False)


    ##### Generate day of week crash dataset
    ##weekday_map= {0:'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}
    ##crashes_2017['dow'] = crashes_2017['dateOccurred'].dt.dayofweek
    ##crashes_2017['dow_name'] = crashes_2017['dow'].map(weekday_map)
    ##dow_crashes = crashes_2017.groupby(['city', 'year', 'dow', 'dow_name']).size().reset_index(name='counts')
    ##dow_crashes.to_csv('dow_crashes.csv', index=False)
    ##
    ##
    ##### Generate time of day crash dataset
    ##crashes_2017['hour'] = crashes_2017['dateOccurred'].dt.hour
    ##
    ### add indicator for weekday/weekend to see if there's a difference in crash distribution
    ##crashes_2017['weekend'] = (crashes_2017['dow']//5==1).astype(int)
    ##
    ##hourly_crashes = crashes_2017.groupby(['city', 'year', 'weekend', 'hour']).size().reset_index(name='counts')
    ##hourly_crashes['pct_crash'] = hourly_crashes.groupby(['weekend'])['counts'].apply(lambda x: x/x.sum())
    ##hourly_crashes['weekend_lbl'] = hourly_crashes['weekend'].map({0:'Weekday', 1:'Weekend'})
    ##hourly_crashes.to_csv('hourly_crashes.csv', index=False)
