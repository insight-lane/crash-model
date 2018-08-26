"""
Title: make_preds_final.py

Author: terryf82 https://github.com/terryf82

Merge predictions with relevant segment data for use by visualization.

Inputs:
    seg_with_predicted.json (predictions)
    inter_and_non_int.geojson (segments)

Output:
    preds_final.json
"""

import argparse
import os
import pandas as pd
import geojson
import json

def combine_predictions_and_segments(preds_file, segs_file):
    """
    Combine predictions data with certain properties of their related segment.
    """
    
    # load the predictions
    print("loading predictions: ", end="")
    predictions = pd.read_json(
        preds_file, orient="index", typ="series", dtype=False)
    print("{} found".format(len(predictions)))
    
    # load the segments
    print("loading segments: ", end="")
    segments_data = pd.read_json(segs_file)
    # TODO segments data standard should probably key each segment by its id
    segments = segments_data["features"]
    print("{} found".format(len(segments)))

    print("combining predictions with segments")
    combined_preds = []
    for pred_id, pred_data in predictions.items():
        for segment in segments:
            # find the matching segment to obtain the display name
            if str(pred_data["segment_id"]) == str(segment["id"]):
                pred_data["segment"] = {
                    "id": str(segment["id"]),
                    "display_name": segment["properties"]["display_name"],
                    "center_x": segment["properties"]["center_x"],
                    "center_y": segment["properties"]["center_y"]
                }

                combined_preds.append(geojson.Feature(
                    geometry = segment["geometry"],
                    properties = pred_data,
                ))
                break
    
    return combined_preds

def write_preds_as_geojson(preds, outfp):
    """
    Output the combined predictions & segments to a geojson file.
    """
    
    preds_collection = geojson.FeatureCollection(preds)
    with open(outfp, "w") as outfile:
        geojson.dump(preds_collection, outfile)
        
        print("wrote {} assembled predictions to file {}".format(
        len(preds), outfp))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", type=str,
                        help="path to destination's data folder")

    args = parser.parse_args()

    # confirm required files exist
    predictions_file = os.path.join(args.folder, "processed/seg_with_predicted.json")
    if not os.path.exists(predictions_file):
        sys.exit("predictions file not found at {}, exiting".format(predictions_file))
        
    segments_file = os.path.join(args.folder, "processed/maps/inter_and_non_int.geojson")
    if not os.path.exists(segments_file):
        sys.exit("segment file not found at {}, exiting".format(segments_file))
    
    preds_final = combine_predictions_and_segments(predictions_file, segments_file)
    write_preds_as_geojson(preds_final, os.path.join(args.folder, "processed/preds_final.geojson"))
