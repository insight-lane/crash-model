# Crash model data generation

This directory contains all the data_generation steps of the pipeline process, starting with standardized json crash and point-based feature files

## Data dependencies

The data for our pilot cities, Boston, Cambridge, and DC have already been generated, and can be found in the data.zip file on data.world.  Download and unzip in the top boston-crash-modeling directory.

## Process map

All of the python data generation scripts should be run from the src directory (boston-crash-modeling/src/) using the following scheme: `python -m <import path> <args>`.

The simplest way to run the data generation scripts is `python -m data.make_dataset -c <config file> -d <data directory>`.  This will run each data generation script with the configuration arguments you provide in a .yml file.  There are version controlled configuration files for our demo cities, e.g. src/config/config_boston.yml.  The data directory is where you store your raw crash data.  Typically this is in a data in the top level directory, and the directory stucture looks like this:

    ├── data
    │   ├── boston
    │   │   ├── raw - where unprocessed csv files live
    │   │   ├── processed - Generated json files with data, and training dataset
    │   │   │   ├─ maps - Generated maps
    │   │   ├── docs - stores automatically generated documentation about certain features
    │   │   ├── standardized


You can alternatively run each of the data generation scripts individually.  Each script is described below

### 1) Create maps from open street maps

- Given a city name, queries open street maps for the city segments.  Simplifies the street network by combining some ways.  Cleans up features, and writes the segments with their cleaned features out to shapefile
- **Usage:** `python -m data.osm_create_maps 'Boston, MA, USA' ../data/` (can replace Boston with any other city, and can use a different data directory
- **Results:**
    - data/processed/maps/osm_ways.shp
    - data/processed/maps/osm_nodes.shp
    - data/processed/maps/osm_ways_3857.shp (this is the file where the cleaned features are attached to ways)
    - data/docs/highway_keys.csv (a mapping from highway key number to the highway type string)
- **Features generated from open street maps:**
    - width (rounded to the nearest foot)
    - lanes (number of lanes)
    - hwy_type
    - osm_speed
    - Many others can be added.  In particular, one way still needs to be added

### 2) Create segments
- Reads in intersections and road segments
    - Creates unique ids for the road segments (orig_id)
- Creates buffer (hard-coded 20m) around intersections
- Connects any parts of road segments within intersection buffer to intersection
    - Road features from connected road segments linked to intersection id (for later aggregation)
- Separates out non-intersection segments
-Creates unique segment ids where all non-intersections have a '00' prefix <br>
- **Usage:** `python -m data.create_segments`
- **Dependencies:**
    - data/processed/maps/osm_ways_3857.shp (Mercator projection:3857)
        - Descriptions of the attributes from ma_co_spatially_joined_streets.shp can be found in data/docs/MassDOTRoadInvDictionary.pdf
- **Results:**
    - data/processed/maps/inters_segments.shp
    - data/processed/maps/non_inters_segments.shp
    - data/processed/maps/inter_and_non_int.shp
    - data/processed/inters_data.json

### 3) (Optional) Add features from a city-specific map

Since Boston was our pilot city, we generate additional features from maps they provided (in addition to the ones we pull from open street map).  Theoretically you can add maps from other cities, but right now we only guarantee support for Boston's additional maps.  If you're not interested in Boston, or in adding additional maps, no need to read this section.

#### To add city-specific map features using the make_dataset script, you add the following arguments to the configuration file:
- extra_map: A map in 4326 projection (for Boston, this is Boston\_Segments.shp : Boston routable road segments [link](http://bostonopendata-boston.opendata.arcgis.com/datasets/cfd1740c2e4b49389f47a9ce2dd236cc_8)
- extra_map3857: A map in 3857 projection (for Boston, this is ma_cob_spatially_joined_streets.shp with Mass DOT road feature information [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)
- additional_features: a list of strings that are features you want to grab from extra_map3857 (for Boston, these are AADT SPEEDLIMIT Struct_Cnd Surface_Tp F_F_Class)

To add Boston's specific data to the boston model, we need to find the intersections of the roads.  This is done by running the extract_intersections script:

#### Extract intersections
- Reads in road segment data (data/raw/Boston_Segments.shp).  Boston_Segments is in EPSG:4326 projection
- Finds point locations where roads intersect
- Creates a shapefile of intersections (inters.shp)
- **Usage:** `python -m data.extract_intersections data/raw/Boston_Segments.shp -d <folder name, e.g. boston>`
- **Results:**
    - data/processed/maps/boston/inters.shp (and related files)

#### Create segments
- create_segments needs to be run on the city-specific maps in order to generate the intersection and non-intersection segments and data.
- For Boston, it would be run like this `python -m data.create_segments -d ../data/boston/ -n boston -r ../data/boston/raw/ma_cob_spatially_joined_streets.shp`

#### Add map
- add_map.py takes two different maps of intersection segments, non-intersection segments and their intersection data json files, and finds mappings between the maps.  Intersections are mapped to intersections, and non-intersection segments are mapped to non-intersection segments.  Features are written out to the non_inters_segments shapefile and to the inters_data.json file (inters_segments does not contain feature information).  The default features, pulled from the Boston data are AADT, SPEEDLIMIT, Struct_Cnd, Surface_Tp, and F_F_Class.
- **Usage:** `python -m data.add_map ../data/ ../data/processed/maps/boston' (the second argument is the directory where the second set of shapefiles that you want to map to the open street map shapefiles are located)
- **Results:**
    - data/processed/maps/non_inters_segments.shp (modified with new features)
    - data/processed/inters_data.json (modified with new features)

### 4) Join segments and point data
- Reads in crash point data and intersection/non-intersection segments
- Snaps points to nearest segment
    - Tolerance of 30m for crashes, 20m for concerns
- Writes shapefile of joined points and json data file
- Includes coordinates and near_id referring to segment id (intersection or non intersection)
- <b>Usage:</b> `python -m data.join_segments_crash`
- <b>Dependencies:</b>
    - inters/non_inters shape data
    - CAD crash data: data/raw/cad_crash_events_with_transport_2016_wgs84.csv
  Vision Zero comments: data/raw/Vision_Zero_Entry.csv
- <b>Results:</b>
    - crash_joined.shp

### 5) (Optional) Process the Automated Traffic Recordings (ATRs)
- We only process ATRs for Boston at this time
- Adds coordinates for the Automated traffic recordings, along with some of the traffic count information.
- Also snaps them to match up to road segments
- <b>Usage:</b> `python -m data.ATR_scraping.geocode_snap_ATRs`
- <b>Dependencies:</b>
    - atr files
    - data/processed/maps/inters_segments.shp
    - data/processed/maps/non_inters_segments.shp
- <b>Results:</b>
    - data/processed/geocoded_atrs.csv
    - data/processed/snapped_atrs.json

### 6) (Optional) Process turning movement counts (TMCs)
- We only process TMCs for Boston at this time

### 7) Make canonical dataset
- This script lives in src/features, but can be run using make_dataset
- Reads in crash data
- Aggregates crash/concern (default by week)
- Reads in road features for intersections and non-intersections
- Aggregates road features to max value
    - e.g. intersection features set to max of all roads joined to it
- Creates dataframe with 52 weeks for each segment
- Joins weekly crashes to dataframe
- <b>Usage:</b>`python -m features.make_canon_dataset`
- <b>Dependencies:</b>
    - crash_joined
    - inter_and_non_int.geojson
- <b>Results:</b>
    - vz_predict_dataset.csv.gz

