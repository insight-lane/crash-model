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


## 1) Extract intersections
- Reads in road segment data (data/raw/Boston_Segments.shp)
- Finds point locations where roads intersect
- Creates a shapefile of intersections (inters.shp)
- <b>Usage:</b> python extract_intersections.py ../data/raw/Boston_Segments.shp
- <b>Results:</b>
    - data/processed/maps/inters.shp (and related files)


## 2) Create segments
- Reads in intersections and road segments
- Creates buffer (hard-coded 20m) around intersections
- Connects any parts of road segments within intersection buffer to intersection
    - Road features from connected road segments linked to intersection id (for later aggregation)
- Separates out non-intersection segments
-Creates unique segment ids where all non-intersections have a '00' prefix <br>
- <b>Usage:</b> python create_segments.py
- <b>Dependencies:</b>
    - data/processed/maps/inters.shp
    - data/processed/maps/ma\_co\_spatially\_joined\_streets.shp
        - Descriptions of the attributes from ma_co_spatially_joined_streets.shp can be found in data/docs/MassDOTRoadInvDictionary.pdf
- <b>Results:</b>
    - data/processed/inters_segments.shp
    - data/processed/non_inters_segments.shp
    - data/processed/inters_data.json


## 3) Join segments and point data
- Reads in crash/concern point data and intersection/non-intersection segments
- Snaps points to nearest segment
    - Tolerance of 30m for crashes, 20m for concerns
- Writes shapefile of joined points and json data file
- Includes coordinates and near_id referring to segment id (intersection or non intersection)
- <b>Usage:</b> python join_segments_crash_concern.py
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
- <b>Usage:</b> python make_canon_dataset.py
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



