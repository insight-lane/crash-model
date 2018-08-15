"""
Title: plot_points.py
 
Author: @andhint, @bpben, @alicefeng

This script visualizes point-level data on a map.  
 
Usage:
    --name: name of the data to be plotted
            this will be used as the name of the layers in the map so they must be unique
    --filename: filename of the dataset
            must be csvs with separate columns named "X" and "Y" for the X and Y coordinates 

Inputs:
    csv files of point-level data to be visualized
    
Output:
    plot_points.html - a Leaflet map with point-level data plotted on it
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium import FeatureGroup, CircleMarker
import argparse
import os


# all datasets must be stored in the "data/processed/" directory
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

DATA_FP = BASE_DIR + '/data/processed/'


# parse arguments
parser = argparse.ArgumentParser(description="Plot point-level data on a map")
parser.add_argument("-n", "--name", nargs="+",
                    help="name of the layer, must be unique")
parser.add_argument("-f", "--filename", nargs="+",
                    help="name of the dataset file to be plotted on the map, must specify at least 1")
parser.add_argument("-lat", "--latitude",
                    help="alternate latitude for the base map")
parser.add_argument("-lon", "--longitude",
                    help="alternate longitude for the base map")
parser.add_argument("-dir", "--datadir",
                    help="alternate data directory for the files")

args = parser.parse_args()

# zip layer names and filenames
if len(args.name) == len(args.filename):
    match = list(zip(args.name, args.filename))
else:
    raise Exception("Number of layers and files must match")

latitude = args.latitude or 42.3601
longitude = args.longitude or -71.0589

if args.datadir:
    DATA_FP = args.datadir

def process_data(filename):
    """Preps data for plotting on a map

    Reads in dataset with separate columns for X, Y coordinates and converts them into (lat, long) points 

    Args:
        filename: name of the file with the predictions

    Returns:
        a dataframe with point geometries added to it
    """
    df = pd.read_csv(DATA_FP + filename)
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    crs = {'init': 'epsg:4326'}

    geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    return geo_df

def add_layer(dataset, layername, mapname, color):
    """Plots predictions on a Leaflet map

    Creates a FeatureGroup to hold all of the points.
    FeatureGroup is added to the map as a layer.

    Args:
        dataset: a dataframe with the data to be plotted
        modelname: name of the model to be used as the layer name
        mapname: name of the map to be plotted on
        color: color used for the points in the layer

    Returns:
        a layer of points added to the map
    """
    feature_group = FeatureGroup(name=layername)
    for point in dataset['geometry']:
        CircleMarker(location=[point.y, point.x],
                     radius=4,
                     color=color,
                     fill_color=color).add_to(feature_group)

    feature_group.add_to(mapname)




### Make map

# First create basemap
boston_map = folium.Map(
    [latitude, longitude], tiles='Cartodb dark_matter', zoom_start=12)
folium.TileLayer('Cartodb Positron').add_to(boston_map)

# Create sequence of colors so different layers appear in different colors
colors = ['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854']

# Plot data as separate layers
for i in range(len(match)):
    data = process_data(match[i][1])
    add_layer(data, match[i][0], boston_map, colors[i])

# Add control to toggle between model layers
folium.LayerControl(position='bottomright').add_to(boston_map)


# Save map as separate html file
boston_map.save('plot_points.html')
