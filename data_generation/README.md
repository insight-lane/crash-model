# Crash model data generation

This directory contains the code for taking the data from the raw segments shapefile to the canonical dataset for the hackathon.

## Data dependencies
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

## Process map
1) Extract intersections : Boston Segments -> extract\_intersections.py -> inters.shp

2) Create segments : inters.shp + ma\_co\_spatially\_joined\_streets.shp -> create\_segments.ipynb -> inters\_segments.shp + non\_inters\_segments.shp

3) Join segments and point data : inters/non-inters + CAD crash data + Vision Zero comments -> join\_segments\_crash\_concern.ipynb -> crash/concern\_joined.shp

4) Make canonical dataset: crash/concern\_joined + inters/non-inters -> make\_canon\_dataset.ipynb -> vz\_predict\_dataset.csv.gz

## 1) Extract intersections
- Reads in road segment data
- Finds point locations where roads intersect

## 2) Create segments
- Reads in intersections and road segments
- Creates buffer (hard-coded 20m) around intersections
- Connects any parts of road segments within intersection buffer to intersection
    - Road features from connected road segments linked to intersection id (for later aggregation)
- Separates out non-intersection segments

## 3) Join segments and point data
- Reads in crash/concern point data and intersection/non-intersection segments
- Snaps points to nearest segment
    - Tolerance of 30m for crashes, 20m for concerns
- Writes shapefile of joined points and json data file

## 4) Make canonical dataset
- Reads in crash/concern data
- Aggregates crash/concern (default by week)
- Reads in road features for intersections and non-intersections
- Aggregates road features to max value
    - e.g. intersection features set to max of all roads joined to it
- Creates dataframe with 52 weeks for each segment
- Joins weekly crash/concerns to dataframe