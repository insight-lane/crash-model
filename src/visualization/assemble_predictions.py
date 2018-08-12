"""
Title: assemble_predictions.py

Author: terryf82 https://github.com/terryf82

Merge predictions with relevant segment data for visualization.

Inputs:
    seg_with_predicted.csv (predictions)
    inter_and_non_int.geojson (segments)

Output:
    assembled_predictions.json
"""

import argparse
import os
import pandas as pd
import json

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", type=str,
                        help="path to city's data folder")

    args = parser.parse_args()

    # confirm files exist
    segments_file = os.path.join(
        BASE_FP, args.folder, "processed/maps/inter_and_non_int.geojson")
    if not os.path.exists(segments_file):
        print("segment file not found at {}, exiting".format(segments_file))
        exit(1)

    predictions_file = os.path.join(
        BASE_FP, args.folder, "processed/seg_with_predicted.json")
    if not os.path.exists(segments_file):
        print("predictions file not found at {}, exiting".format(predictions_file))
        exit(1)

    # load the segments
    print("loading segments: ", end="")
    segments_data = pd.read_json(segments_file)
    # TODO segments data standard should key each segment by its id
    segments = segments_data["features"]
    print("{} found".format(len(segments)))

    # load the predictions
    print("loading predictions: ", end="")
    predictions = pd.read_json(
        predictions_file, orient="index", typ="series", dtype=False)
    print("{} found".format(len(predictions)))

    print("matching predictions with segments")
    assembled_preds = []
    for pred_id, pred_data in predictions.items():
        for segment in segments:
            # find the matching segment and merge in relevant properties
            if pred_data["segment_id"] == segment["id"]:
                pred_data["segment"] = {
                    "id": segment["id"],
                    "display_name": segment["properties"]["display_name"],
                    # "geometry": segment["geometry"]
                }

                assembled_preds.append({
                    "type": "Feature",
                    "properties": pred_data,
                    "geometry": segment["geometry"]
                })
                break
    
    # add the assembled predictions into a geoJSON-comaptible structure
    geo_assembled_preds = {
        "type": "FeatureCollection",
        "features": assembled_preds
    }

    geo_assembled_preds_file = os.path.join(
        BASE_FP, args.folder, "processed/assembled_preds.json")

    with open(geo_assembled_preds_file, "w") as f:
        json.dump(geo_assembled_preds, f)

    print("wrote {} assembled predictions to file {}".format(
        len(assembled_preds), geo_assembled_preds_file))
