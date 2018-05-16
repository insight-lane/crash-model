# Crash model pipeline

This directory contains the code for taking the data from the csv crash files, standardizing the crash data, generating the feature set, training a model to predict risk on segments, and visualizing the results.

## Module dependencies
If using conda, you can get all the depencies using the [environment.yml](https://github.com/Data4Democracy/boston-crash-modeling/blob/master/environment.yml) file.
Python modules: Use requirements\_spatial.txt

rtree additionally requires download and installation of [libspatialindex](http://libspatialindex.github.io/)
(For Anaconda install, can use [conda-forge](https://anaconda.org/conda-forge/libspatialindex))

## Useful Tools

Although it's not necessary, QGIS (http://www.qgis.org/en/site/forusers/download.html) might be helpful to visualize shape files and easily see their attributes

## Code conventions

## Testing

We use Travis continuous integration to ensure that our test suite passes before branches can be merged into master.  To run the tests locally, run `py.test` in the src/ directory.

## Overview

We use open street map to generate basic information about a city.  Then we find intersections and segments in between intersections.  We take one or more csv files of crash data and map crashes to the intersection or non-intersection segments on our map.  And we have the ability to add a number of other data sources to generate features beyond those from open street map.  Most of the additional features are currently Boston-specific.
These features include
- Concerns submitted to the city of Boston's vision zero platform http://app01.cityofboston.gov/VZSafety/.  Concerns are not Boston-specific, but not very many cities gather these type of concerns.  Some other cities have other sources of concern data.  We use See Click Fix data (https://seeclickfix.com/) as our concern data for Cambridge, MA.
- Automated traffic counts in some locations
- Turning movement counts in some locations

We also can map city-specific maps (and features associated with their roads) to the base open street map.

## Running the pipeline: data generation through visualization

Although the processed data for our demo cities exist on data.world, you may wish to generate the data from scratch, or you may be interested in generating data for a new city.  This section walks you through how to generate and visualize data for a new city:

- If you want to visualize the data, you need to create a mapbox account (https://www.mapbox.com/)
- Automatically generate a config file for your city.  In the src directory, run `python initialize_city.py -city <city name> -f <folder name> -crash <crash file> --concern <concern file>`.
    - City name is the full name of the city, e.g. "Cambridge, MA, USA".
    - Folder name is what you'd like the city's data directory to  be named, e.g. "cambridge".
    - The crash file is a csv file of crashes that includes (at minimum) columns for latitude, longitude, and date of crashes.
    - The concern file is a csv of concerns that includes (at minimum) a latitude, longitude and date of a concern file.
- Manually edit the configuration file found in e.g. src/config/config_cambridge:
    - For your csv crash file, enter the column header for id, latitude, longitude, and date.  If time is in a different column than date, give that column header as well.
    - If you have a csv concern file, enter the column headers for latitude, longitude, and date.
    - Modify time_target to be the last month and year of your crash data
    - Manually edit config.js in src/visualization/reports/config.js to add your mapbox api key (from when you made a mapbox account) as MAPBOX_TOKEN

- Run the pipeline: `python pipeline.py -c <config file>`

## Individual pipeline steps

To learn more about any individual steps (which are themselves often broken up into a number of steps), look at the README in that directory

### 1) Data Transformation

Found in src/data_transformation <br><br>
Cities can provide csv files containing crash and concern data.  But because there isn't very much standardization of crash or concern data across cities, we use this step to turn csv files into formatted json files.

2) Data Generation

Found in src/data <br><br>
The data generation steps create a set of maps of road segments for the city, generates features for the road segments, and for each crash, assign it to its nearest road segment.

3) Feature Generation

Found in src/features <br><br>
Documented in the README under src/data/ <br><br>
The feature generation step takes the data from the data generation step, and turns them into a feature set.

4) Training the model

Found in src/models <br><br>

5) Visualizing the results

Found in src/visualization <br><br>
