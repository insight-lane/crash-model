# Crash model pipeline

This directory contains the code for taking the data from the csv crash files, standardizing the crash data, generating the feature set, training a model to predict risk on segments, and visualizing the results.

## Module dependencies
If using conda, you can get all the depencies using the [environment_linux.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_linux.yml), [environment_mac.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_mac.yml), or [environment_pc.yml](https://github.com/Data4Democracy/crash-model/blob/master/environment_pc.yml) files.
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
- Any other point-based feature (in a csv file with a latitude and longitude).
- Automated traffic counts in some locations
- Turning movement counts in some locations

We also can map city-specific maps (and features associated with their roads) to the base open street map.

## Running the pipeline: data generation through visualization

This section walks you through how to generate and visualize data for any of our demo cities (Boston MA, Cambridge MA or Washigton D.C), or for any city that you have suitable data for (at a minimum crashes, ideally concerns as well).

The demo city data is stored as *data-latest.zip* using data-world. Contact one of the project leads if you don't yet have access.

### Visualization
- If you want to visualize the data, you'll need to create a mapbox account (https://www.mapbox.com/)

### Initializing a city
- If you're running on a new city (that does not have a configuration file in src/data/config), you will need to initialize it first to create directories and generate a config.  In the src directory, run `python initialize_city.py -city <city name> -f <folder name> -crash <crash file> --supplemental <supplemental file1>,<supplemental file2>`. You should give the full path to the crash file and any supplemental files, and they will be copied into the city's data directory as part of initialization. Concern files are given as supplemental files, as are any other point-based features.
    - City name is the full name of the city, e.g. "Cambridge, MA, USA".
    - Folder name is what you'd like the city's data directory to be named, e.g. "cambridge".
    - The latitude and longitude will be auto-populated by the initialize_city script, but you can modify this
    - If you wish to create a default map from a radius instead of the open street map city boundaries, you can specify it by setting 'map_geography: radius'. If you would like to specify a particular polygon, you can set 'map_geography' to 'shapefile' and boundary_shapefile to the name of the file with one or more polygons making a boundary region. The shapefile should be saved into <your city's directory>/raw/maps/
    - The time zone will be auto-populated as your current time zone, but you can modify this if it's for a city outside of the time zone on your computer (we use tz database time zones: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
    - If you give a startdate and/or an enddate, the system will only look at crashes that fall within that date range
    - The crash file is a csv file of crashes that includes (at minimum) columns for latitude, longitude, and date of crashes.
		- Windows users should modify their filepath to use forward slashes (/) rather than the default backslash (\\)
    - The concern files or any other point-based feature files are optional: a csv of concerns that includes (at minimum) a latitude, longitude and date of a concern file.
		- Windows users should modify their filepath to use forward slashes (/) rather than the default backslash (\\)
    - Supplemental files are optional: any number of csv files that contain a lat/lon point and some type of feature you'd like to extract

- Once you have run the initialize_city script, you need to manually edit the configuration file found in e.g. src/config/config_cambridge:
        - If OpenStreetMaps does not have polygon data for your city, the road network will need to be constructed manually. Set the city_latitude and city_longitude values to the centerpoint of the city, and the city_radius to an appropriate distance (in km) that you would like the road network to be built for, e.g 15 for 15km radius from the specified lat / lng.
        - For your csv crash file, enter the column header for id, latitude, longitude, and date.  If time is in a different column than date, give that column header as well. If your csv file does not contain an id field, just put ID here, and the csv will be modified to add an ID
        - If you have any supplemental files, they will be listed under data_source. For each data source, you'll need to enter the column headers for latitude, longitude, and date.
        - Modify time_target to be the last month and year of your crash data (this is legacy and you won't need to do this unless you want to do week-by-week modeling)
        - We also allow you to specify addditional features in the crash file to include in the training data set. This has been designed to handle mode (pedestrian, bike, vehicle) but designed to handle any set of features in the crash file. Here is an example of how to handle mode if it is specified as a single column with different value for each mode

```
      split_columns:
        pedestrian:
          column_name: Type
          column_value: PED
        bike:
          column_name: Type
          column_value: CYC
        vehicle:
          column_name: Type
          column_value: AUTO
```

- And here is an example of how to handle mode if there is a column for bike, and a column for pedestrian, but no column for vehicle. Since a crash is counted as a vehicle crash if it is not a pedestrian or a bike crash, you use the not_column field to specify the bike/pedestrian columns

```

      split_columns:
        pedestrian:
          column_name: Count_Unit_Pedestrian
          column_value: any
        bike:
          column_name: Count_Unit_Bicycle
          column_value: any
        vehicle:
          not_column: pedestrian bike

```
- export your mapbox api key (from when you made a mapbox account) as an environment variable called MAPBOX_TOKEN
- Running the initialize_city script will also generate a javascript config file in the showcase data directory, e.g. `src/showcase/data/config_boston.js`. You'll want to set a CONFIG_FILE environment variable to be that file: `export CONFIG_FILE=data/config_boston.js` but replace boston with your city's folder name
- If the city name given in the initialize_city script (e.g. Boston, Massachusetts, USA) ends with 'USA', the speed unit set in the javascript config file will be 'mph', otherwise it will be 'kph'. If you'd like to change this, you can manually set it in the config_<city>.js file.

### Geocoding

- If your crash file provides addresses but not latitude/longitude, you'll need to geocode your crash file before running the pipeline. This can be done from the src directory by running `python -m tools.geocode_batch -d <data directory created from the initalize_city script> -f <crash filename> -a <address field in the crash csv file> -c <city name, e.g. "Boston, Massachusetts, USA"`. If you have a very large number of entries to geocode, you may choose to use mapbox's geocoder instead of google's (the default for this script). In that case, you can also pass in your mapbox token to the script with the -m flag.

### Running on existing cities
- Cities we have already set up on the showcase can be viewed using the default configuration file. If you'd prefer to view these cities, use that configuration file instead: `export CONFIG_FILE=static/config.js'

- Run the pipeline: `python pipeline.py -c <config file>`

## Individual pipeline steps

To learn more about any individual steps (which are themselves often broken up into a number of steps), look at the README in that directory

### 1) Data Standardization

Found in src/data_standardization <br><br>
Cities can provide csv files containing crash and point-based feature data (including, but not limited to concerns).  Due to the varying recording methodologies used across cities, we run this step to turn csv files into compatible JSON files.

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

Once you have run the pipeline you can visualize results from your city, or you can view the showcase locally <br>

To run locally:
- `cd showcase`
- You should have already exported your MAPBOX_TOKEN and CONFIG_FILE earlier in following along with this README, so check that those are set
- `flask run`

If you have set split columns in the config .yml file, you can select which split column's map you'd like to look at. Most frequently this would be mode, so you would see (for example) 'Boston, Massachusetts (bike)', 'Boston, Massachusetts (pedestrian)', and 'Boston, Massachusetts (vehicle)', showing the risk map and crashes for each mode type.

Details about other visualization scripts can be found in the README under src/visualization
