"""
Title: risk_map.py
 
Author: @bpben, @alicefeng
 
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

import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
import sys

# must provide filepath for prediction csv
try:
	output = pd.read_csv(sys.argv[1], converters={'segment_id':str})
except:
	print("Must provide filepath as first argument to script")
	raise

output['id'] = output['segment_id'].astype('str')

# filename is csvname
fname = sys.argv[1].split('/')[-1].split('.')[0]

# Read in shapefile as a GeoDataframe
streets = gpd.read_file('../data/processed/maps/inter_and_non_int.shp')

# Set the projection as EPSG:3857 since the shapefile didn't export with one
streets.crs = {'init': 'epsg:3857'}

# Then reproject to EPSG:4326 to match what Leaflet uses
streets = streets.to_crs({'init': 'epsg:4326'})

# Merge on model results to the GeoDataframe
streets_w_risk = streets.merge(output, on='id')

# second argument = column name for risk score
score_col = sys.argv[2]
#streets_w_risk['pred_normalize'] = streets_w_risk.pred / streets_w_risk.pred.max()
# third argument = T or F, normalize
if sys.argv[3] == 'T':
	streets_w_risk['pred_normalize'] = streets_w_risk[score_col] / streets_w_risk[score_col].max()
else:
	streets_w_risk['pred_normalize'] = streets_w_risk[score_col]

# Make map

# First create basemap
boston_map = folium.Map([42.3601, -71.0589], tiles='Cartodb Positron', zoom_start=12)  #"Cartodb dark_matter" also nice

# Create style function to color segments based on their risk score
#color_scale = cm.linear.YlOrRd.scale(0, 1)
color_scale = cm.linear.YlOrRd.scale(streets_w_risk['pred_normalize'].min(), 
                                     streets_w_risk['pred_normalize'].max())
    
# Then add on GeoDataframe of risk scores
folium.GeoJson(streets_w_risk[streets_w_risk.pred_normalize>0],  # filter dataframe to only seg with risk>0 to reduce size
              style_function=lambda feature: {
                  'color': color_scale(feature['properties']['pred_normalize'])
              }).add_to(boston_map)

# Finally, add legend
color_scale.caption = "Risk Score"
boston_map.add_child(color_scale)

# Save map as separate html file
boston_map.save(fname+'.html')