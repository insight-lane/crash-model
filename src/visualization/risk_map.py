"""
Title: risk_map.py
 
Author: @bpben, @alicefeng

This script generates a map of the "risk estimates" from model predictions.  
 
Usage:
    --modelname: name of the models
            these will be used as the name of the layers in the map so they must be unique
    --filename: filename of predictions
              predictions must be csvs with two columns; segment_id, prediction_column
    --colname: name of the predictions column
    --normalize: optional flag to indicate it predictions need to be normalized

Inputs:
    csv files of model predictions
    inter_and_non_int.shp - a Shapefile with both intersection and non-intersection segments and their segment_ids
    
Output:
    risk_map.html - a Leaflet map with model predictions visualized on it
"""

import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
import argparse
import os

# all model outputs must be stored in the "data/processed/" directory
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

def process_data(filename, colname, normalize=False):
        """Preps model output for plotting on a map

        Reads in model output and filters to non-zero predictions.
        Spatially joins the data to a shapefile of Boston's road network to match segments with
        their predicted crash risk.
        Normalizes the predictions if needed.

        Args:
            filename: name of the file with the predictions
            colname: name of the predictions column

        Returns:
            a dataframe that links segment_ids, predictions and spatial geometries
        """
        output = pd.read_csv(os.path.join(DATA_FP, filename), dtype={'segment_id':'str'})

        # filter dataframe to only seg with risk>0 to reduce size
        output = output[output[colname]>0]

        # Merge on model results to the GeoDataframe
        streets_w_risk = streets.merge(output, left_on='id',right_on='segment_id')

        # normalize predictions if specified
        if normalize:
            print("Normalizing predictions...")
            streets_w_risk[colname] = streets_w_risk[colname] / streets_w_risk[colname].max()

        return streets_w_risk

def add_layer(dataset, modelname, colname, mapname):
        """Plots predictions on a Leaflet map

        Args:
            dataset: a dataframe with the data to be plotted
            modelname: name of the model to be used as the layer name
            colname: name of the predictions column
            mapname: name of the map to be plotted on

        Returns:
            a GeoJSON layer added to the map
        """
        folium.GeoJson(dataset,
                       name=modelname,
                       style_function=lambda feature: {
                               'color': color_scale(feature['properties'][colname])
                               }).add_to(mapname)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # parse arguments
    parser.add_argument("-m", "--modelname", nargs="+",
                        help="name of the model, must be unique")
    parser.add_argument("-f", "--filename", nargs="+",
                        help="name of the file with the predictions to be plotted on the map, must specify at least 1")
    parser.add_argument("-c", "--colname", nargs="+",
                        help="column name that has the predictions, must be specified in the same order as the filenames")
    parser.add_argument("-lat", "--latitude",
                        help="alternate latitude for the base map")
    parser.add_argument("-lon", "--longitude",
                        help="alternate longitude for the base map")
    parser.add_argument("-n", "--normalize",
                        help="normalize risk scores",
                        action='store_true')
    parser.add_argument("-dir", "--datadir",
                        help="alternate data directory for the files")
    args = parser.parse_args()

    # zip filenames and column names
    if len(args.modelname) == len(args.filename) == len(args.colname):
        match = zip(args.modelname, args.filename, args.colname)
    else:
        raise Exception("Number of models, files and column names must match")

    latitude = args.latitude or 42.3601
    longitude = args.longitude or -71.0589

    MAP_FP = os.path.join(args.datadir, 'processed/maps')
    DATA_FP = os.path.join(args.datadir, 'processed')
    
    # Read in shapefile as a GeoDataframe
    streets = gpd.read_file(os.path.join(MAP_FP, 'inter_and_non_int.geojson'))

    ### Make map

    # First create basemap
    boston_map = folium.Map([latitude, longitude], tiles='Cartodb dark_matter', zoom_start=12)
    folium.TileLayer('Cartodb Positron').add_to(boston_map)

    # Create style function to color segments based on their risk score
    color_scale = cm.linear.YlOrRd.scale(0, 1)

    # Plot model predictions as separate layers
    for model in match:
        predictions = process_data(model[1], model[2], normalize=args.normalize)
        add_layer(predictions, model[0], model[2], boston_map)

    # Add control to toggle between model layers
    folium.LayerControl(position='bottomright').add_to(boston_map)

    # Finally, add legend
    color_scale.caption = "Risk Score"
    boston_map.add_child(color_scale)

    # Save map as separate html file
    boston_map.save(os.path.join(MAP_FP, 'risk_map.html'))