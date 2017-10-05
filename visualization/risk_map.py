"""
Title: risk_map.py
 
Author: @bpben, @alicefeng

This script generates a map of the "risk estimates" from model predictions.  
 
Usage:
    arg[1] = filename of predictions
      predictions must be csvs with two columns; segment_id, prediction_column
    arg[2] = column name of prediction_columns
    arg[3] = 'T' if needs to be normalized

Output:
    <<arg[1]>>.html
"""

import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
import sys

# all model outputs must be stored in the data\processed directory
fp = '../data/processed/'

# parse arguments
try:
  filename, prediction_column = sys.argv[1:3]
except:
  print("Must provide filename, prediction_column as first and second argument")
  raise

# check to normalize
normalize = False
if len(sys.argv)==4:
  if sys.argv[3]=='T':
    normalize = True

# read in predictions
output = pd.read_csv(fp + filename, dtype={'segment_id':'str'})

# filename is csvname
#fname = sys.argv[1].split('/')[-1].split('.')[0]

# Read in shapefile as a GeoDataframe
streets = gpd.read_file('../data/processed/maps/inter_and_non_int.shp')

# Set the projection as EPSG:3857 since the shapefile didn't export with one
streets.crs = {'init': 'epsg:3857'}

# Then reproject to EPSG:4326 to match what Leaflet uses
streets = streets.to_crs({'init': 'epsg:4326'})

# Merge on model results to the GeoDataframe
streets_w_risk = streets.merge(output, left_on='id',right_on='segment_id')

# third argument = T or F, normalize
if normalize==True:
	streets_w_risk[prediction_column] = streets_w_risk[prediction_column] / streets_w_risk[prediction_column].max()

# Make map

# First create basemap
boston_map = folium.Map([42.3601, -71.0589], tiles='Cartodb dark_matter', zoom_start=12)

# Create style function to color segments based on their risk score
#color_scale = cm.linear.YlOrRd.scale(0, 1)
color_scale = cm.linear.YlOrRd.scale(streets_w_risk[prediction_column].min(), 
                                     streets_w_risk[prediction_column].max())
    
# Then add on GeoDataframe of risk scores
folium.GeoJson(streets_w_risk[streets_w_risk[prediction_column]>0],  # filter dataframe to only seg with risk>0 to reduce size
              name='Benchmark Model',
			  style_function=lambda feature: {
                  'color': color_scale(feature['properties'][prediction_column])
              }).add_to(boston_map)

# Add control to toggle between model layers
folium.LayerControl(position='bottomright').add_to(boston_map)

# Finally, add legend
color_scale.caption = "Risk Score"
boston_map.add_child(color_scale)

# Save map as separate html file
boston_map.save(sys.argv[1]+'.html')