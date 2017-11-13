# Crash model visualization

This directory contains the code relevant to the visualization efforts for this project.

## Visualization Products

_risk_map.py_ - This script can be used to plot predictions generated from multiple models on a single Leaflet map of Boston.  It color-codes each segment based on the magnitude of the predicted risk.

To run this script, you need the following inputs:
- inter_and_non_int.shp (created in create_segments.py)
- csv files of predictions (each row should have 1 prediction per segment and be stored in the `data/processed/` directory)

The script takes the following flag arguments on the command line:

-m = model names (these will be the names of the layers on your map)

-f = csv file names (one for each model and specified in the same order as the model names)

-c = names of the predictions columns (one for each file and specified in the same order as the model names)

-n = optional flag to indicate if predictions need to be normalized

An example of how to run this script to plot the output from two models is as follows:
```
python risk_map.py -m model1 model2 -f model1_output.csv model2_output.csv -c risk_score preds
```

_plot_points.py_ - This script can be used to plot point-level data on a Leaflet map of Boston.

To run this script, you need the following inputs:
- csv files of point-level data (there should separate columns named "X" and "Y" for the X and Y coordinates. The files should be stored in the `data/processed/` directory)

The script takes the following flag arguments on the command line:

-n = name of the data to be plotted (these will be the names of the layers on your map)

-f = csv file names (one for each set of data and specified in the same order as the layer names)

An example of how to run this script is as follows:
```
python plot_points.py -n crashes -f cad_crash_events.csv
```

_historical_crash_map.html_ - This static site plots historical crash data and model predictions for a given week in 2016.  Users can scrub the slider to see different weeks visualized on the map.  A bar graph at the bottom summarizes the total number of crashes by week.

To run this site, you need the following:
- the /css and /js subdirectories with the files contained within
- cad.geojson and car_preds_named.json
- to run historical_crash_map.py to generate the data needed for the bar graph.  Place the generated csv file in the same directory as the html file.
