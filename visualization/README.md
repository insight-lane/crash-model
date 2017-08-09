# Crash model visualization

This directory contains the code relevant to the visualization efforts for this project.

## Visualization Scripts

_make_map.ipynb_ - This notebook can be used to plot predictions of crash risk rates generated from a model on a Leaflet map of Boston.  It color-codes each segment based on the magnitude of the predicted risk.

To run this script, you need the following inputs:
- inter_and_non_int.shp - this is a shapefile that combines intersection and non-intersection segments for the entire city while preserving the IDs assigned to them in create_segments.py.  This file is created in create_segments.py
- a .csv file of predicted crash risk - each row should have 1 prediction per segment
