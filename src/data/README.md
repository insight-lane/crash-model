# Crash model data generation

This directory contains all the data_generation steps of the pipeline process, starting with standardized json crash and concern files

## Data dependencies

The data for our pilot cities, Boston, Cambridge, and DC have already been generated, and can be found in the data.zip file on data.world.  Download and unzip in the top boston-crash-modeling directory.


## Boston-specific feature additions

- Boston\_Segments.shp : Boston routable road segments [link](http://bostonopendata-boston.opendata.arcgis.com/datasets/cfd1740c2e4b49389f47a9ce2dd236cc_8)
- Vision\_Zero\_Entry.csv : Vision Zero comments [link](https://data.boston.gov/dataset/vision-zero-entry)
- cad\_crash\_events\_with\_transport\_2016\_wgs84.csv : CAD crash data for 2016, projected to WGS84 [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)
- ma\_co\_spatially\_joined\_streets.shp : Boston Segments with Mass DOT road feature information [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)
- inters.shp : Intersection points based on Boston Segments [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)



Since Boston was our pilot city, we generate additional features from maps they provided (in addition to the ones we pull from open street map).  If you're only interested in other cities, no need to read this section.

To add Boston's specific data to the boston model, the following arguments are added to the configuration file:
- extra_map: A map in 4326 projection
- extra_map3857: A map in 3857 projection
- additional_features: a list of strings that are features you want to grab from extra_map3857

## Process map

All of the python data generation scripts should be run from the src directory (boston-crash-modeling/src/) using the following scheme: `python -m <import path> <args>`.

The simplest way to run the data generation scripts is `python -m data.make_dataset_osm -c <config file> -d <data directory>`.  This will run each data generation script with the configuration arguments you provide in a .yml file.  There are version controlled configuration files for our demo cities, e.g. src/config/config_boston.yml.  The data directory is where you store your raw crash data.  Typically this is in a data in the top level directory, and the directory stucture looks like this:

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
- **Usage:** `python -m data.osm_create_maps 'Boston, Massachusetts, USA' ../data/` (can replace Boston with any other city, and can use a different data directory
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

## 2) Extract intersections
- Reads in road segment data (data/raw/Boston_Segments.shp).  Boston_Segments is in EPSG:4326 projection
- Finds point locations where roads intersect
- Creates a shapefile of intersections (inters.shp)
- **Usage:** `python -m data.extract_intersections data/raw/Boston_Segments.shp`
- **Results:**
    - data/processed/maps/inters.shp (and related files)


## 3) Create segments
- Reads in intersections and road segments
    - Creates unique ids for the road segments (orig_id) from ma\_co\_spatially\_joined\_streets.shp
- Creates buffer (hard-coded 20m) around intersections
- Connects any parts of road segments within intersection buffer to intersection
    - Road features from connected road segments linked to intersection id (for later aggregation)
- Separates out non-intersection segments
-Creates unique segment ids where all non-intersections have a '00' prefix <br>
- **Usage:** `python -m data.create_segments`
- **Dependencies:**
    - data/processed/maps/inters.shp (EPSG:4326 projection)
    - data/processed/maps/ma\_co\_spatially\_joined\_streets.shp (Mercator projection:3857)
        - Descriptions of the attributes from ma_co_spatially_joined_streets.shp can be found in data/docs/MassDOTRoadInvDictionary.pdf
- **Results:**
    - data/processed/maps/inters_segments.shp
    - data/processed/maps/non_inters_segments.shp
    - data/processed/maps/inter_and_non_int.shp
    - data/processed/inters_data.json

## 4) Add features from a new map
- Takes two different maps of intersection segments, non-intersection segments and their intersection data json files, and finds mappings between the maps.  Intersections are mapped to intersections, and non-intersection segments are mapped to non-intersection segments.  Features are written out to the non_inters_segments shapefile and to the inters_data.json file (inters_segments does not contain feature information).  The default features, pulled from the Boston data are AADT, SPEEDLIMIT, Struct_Cnd, Surface_Tp, and F_F_Class.
- **Usage:** `python -m data.add_map ../data/ ../data/processed/maps/boston' (the second argument is the directory where the second set of shapefiles that you want to map to the open street map shapefiles are located)
- **Results:**
    - data/processed/maps/non_inters_segments.shp (modified with new features)
    - data/processed/inters_data.json (modified with new features)

## 5) Join segments and point data
- Reads in crash/concern point data and intersection/non-intersection segments
- Snaps points to nearest segment
    - Tolerance of 30m for crashes, 20m for concerns
- Writes shapefile of joined points and json data file
- Includes coordinates and near_id referring to segment id (intersection or non intersection)
- <b>Usage:</b> `python -m data.join_segments_crash_concern`
- <b>Dependencies:</b>
    - inters/non_inters shape data
    - CAD crash data: data/raw/cad_crash_events_with_transport_2016_wgs84.csv
  Vision Zero comments: data/raw/Vision_Zero_Entry.csv
- <b>Results:</b>
    - crash_joined.shp
    - concern_joined.shp

## 6) Process the ATRs
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

## 7) Process turning movement counts

## 8) Make canonical dataset
- Reads in crash/concern data
- Aggregates crash/concern (default by week)
- Reads in road features for intersections and non-intersections
- Aggregates road features to max value
    - e.g. intersection features set to max of all roads joined to it
- Creates dataframe with 52 weeks for each segment
- Joins weekly crash/concerns to dataframe
- <b>Usage:</b>`python -m features.make_canon_dataset`
- <b>Dependencies:</b>
    - crash/concern_joined
    - inters/non_inters
- <b>Results:</b>
    - vz_predict_dataset.csv.gz

# Data Standards

-this is meant to address [issue #32](https://github.com/Data4Democracy/boston-crash-modeling/issues/32) brought up by @therriault

## 1) Where is data stored and in what format?
-all data should be stored on data.world
    -data should be seperated into `raw` or `processed` folder as appropriate
    -shape files should have seperate folder `maps` within `raw` and `processed`
-all data should be stored in CSV format with the exception of shape files

## 2) How are dates and times handled?
-each segment will have an entry for each week of the year (1 to 53 as each year is 52.2 weeks)

## 3) Put outcomes and features in model-ready format
-any non-temporal feature for a segment will have the same value across all weeks
-this allows us the ability to use temporal and non-temporal models with minimal data-wrangling
-example

| segment_id | week | temporal_feature | static_feature |
|------------|------|------------------|----------------|
| 1          | 1    | 0.5              | 76             |
| 1          | 2    | 0.75             | 76             |
| 1          | 3    | 0.8              | 76             |
| 1          | ...  | ...              | ...            |
| 1          | 53   | 0.95             | 76             |
| 2          | 1    | 0.2              | 34             |
| 2          | 2    | 0.15             | 34             |
| 2          | 3    | 0.23             | 34             |
| 2          | ...  | ...              | ...            |
| 2          | 53   | 0.27             | 34             |
| 3          | 1    | 0.45             | 45             |
| 3          | 2    | 0.41             | 45             |


## 4) How to deal with new generated features?
-generate a new csv for each feature with the above layout of 53 weeks/segment so data can be easily joined with the canonical dataset
-create or edit data dictionary within data/docs from data.world explaining the generated data
