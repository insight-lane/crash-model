# Crash model data generation

This directory contains the code for taking the data from the raw segments shapefile to the canonical dataset for the hackathon.

## Data dependencies

All of these can be found in the data.zip file on data.world.  Download and unzip in the top boston-crash-modeling directory.

- Boston\_Segments.shp : Boston routable road segments [link](http://bostonopendata-boston.opendata.arcgis.com/datasets/cfd1740c2e4b49389f47a9ce2dd236cc_8)
- Vision\_Zero\_Entry.csv : Vision Zero comments [link](https://data.boston.gov/dataset/vision-zero-entry)
- cad\_crash\_events\_with\_transport\_2016\_wgs84.csv : CAD crash data for 2016, projected to WGS84 [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)
- ma\_co\_spatially\_joined\_streets.shp : Boston Segments with Mass DOT road feature information [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)
- inters.shp : Intersection points based on Boston Segments [link](https://data.world/data4democracy/boston-crash-model) (ask coordinator for invite)

## Module dependencies
If using conda, you can get all the depencies using the [environment.yml](https://github.com/Data4Democracy/boston-crash-modeling/blob/master/environment.yml) file.
Python modules: Use requirements\_spatial.txt

rtree additionally requires download and installation of [libspatialindex](http://libspatialindex.github.io/)
(For Anaconda install, can use [conda-forge](https://anaconda.org/conda-forge/libspatialindex))

Although it's not necessary, QGIS (http://www.qgis.org/en/site/forusers/download.html) might be helpful to visualize shape files and easily see their attributes

## Process map

All of the data generation scripts should be run from the top directory (boston-crash-modeling) using the following scheme: `python -m <import path> <args>`.  See below for specific examples.

## 1) Extract intersections
- Reads in road segment data (data/raw/Boston_Segments.shp)
- Finds point locations where roads intersect
- Creates a shapefile of intersections (inters.shp)
- **Usage:** python -m data_generation.make_segments.extract_intersections data/raw/Boston_Segments.shp
- **Results:**
    - data/processed/maps/inters.shp (and related files)


## 2) Create segments
- Reads in intersections and road segments
- Creates buffer (hard-coded 20m) around intersections
- Connects any parts of road segments within intersection buffer to intersection
    - Road features from connected road segments linked to intersection id (for later aggregation)
- Separates out non-intersection segments
-Creates unique segment ids where all non-intersections have a '00' prefix <br>
- **Usage:** python -m data_generation.make_segments.create_segments
- **Dependencies:**
    - data/processed/maps/inters.shp
    - data/processed/maps/ma\_co\_spatially\_joined\_streets.shp
        - Descriptions of the attributes from ma_co_spatially_joined_streets.shp can be found in data/docs/MassDOTRoadInvDictionary.pdf
- **Results:**
    - data/processed/inters_segments.shp
    - data/processed/non_inters_segments.shp
    - data/processed/inters_data.json


## 3) Join segments and point data
- Reads in crash/concern point data and intersection/non-intersection segments
- Snaps points to nearest segment
    - Tolerance of 30m for crashes, 20m for concerns
- Writes shapefile of joined points and json data file
- Includes coordinates and near_id referring to segment id (intersection or non intersection)
- <b>Usage:</b> python -m data_generation.crash_and_concern.join_segments_crash_concern
- <b>Dependencies:</b>
    - inters/non_inters shape data
    - CAD crash data: data/raw/cad_crash_events_with_transport_2016_wgs84.csv
  Vision Zero comments: data/raw/Vision_Zero_Entry.csv
- <b>Results:</b>
    - crash_joined.shp
    - concern_joined.shp


## 4) Make canonical dataset
- Reads in crash/concern data
- Aggregates crash/concern (default by week)
- Reads in road features for intersections and non-intersections
- Aggregates road features to max value
    - e.g. intersection features set to max of all roads joined to it
- Creates dataframe with 52 weeks for each segment
- Joins weekly crash/concerns to dataframe
- <b>Usage:</b> python -m data_generation.make_canonical.make_canon_dataset
- <b>Dependencies:</b>
    - crash/concern_joined
    - inters/non_inters
- <b>Results:</b>
    - vz_perdict_dataset.csv.gz

## 5) Process the ATRs
- Adds coordinates for the Automated traffic recordings, along with some of the traffic count information.
- Also snaps them to match up to road segments
- <b>Usage:</b> python geocode_snap_ATRs.py
- <b>Dependencies:</b>
    - atr files
    - data/processed/maps/inters_segments.shp
    - data/processed/maps/non_inters_segments.shp
- <b>Results:</b>
    - data/processed/geocoded_atrs.csv
    - data/processed/snapped_atrs.json

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
