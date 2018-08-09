"""
Title: merge_preds_segments.py

Author: terryf82 https://github.com/terryf82

Merge predictions with relevant segment data for visualization.

Inputs:
    seg_with_predicted.csv (predictions)
    inter_and_non_int.geojson (segments)

Output:
    predictions_with_segments.json
"""

import argparse
import os
import pandas as pd

CURR_FP = os.path.dirname(
    os.path.abspath(__file__))
BASE_FP = os.path.dirname(os.path.dirname(CURR_FP))

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", type=str,
                        help="path to city's data folder")
    
    args = parser.parse_args()
    
    # confirm files exist
    segments_file = os.path.join(BASE_FP, args.folder, "processed/maps/inter_and_non_int.geojson")
    if not os.path.exists(segments_file):
        print("segment file not found at {}, exiting".format(segments_file))
        exit(1)
    
    predictions_file = os.path.join(BASE_FP, args.folder, "processed/seg_with_predicted.json")
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
    predictions_data = pd.read_json(predictions_file, dtype=False)
    predictions = predictions_data.to_dict()
    print("{} found".format(len(predictions)))
    
    merged_preds_segs = []
    for pred_id, pred_data in predictions.items():
        pred_segment_id = pred_data["segment_id"]
        
        for segment in segments:
            if pred_segment_id == segment["id"]:
                merged_preds_segs.append({ "id": pred_id,
                                          "segment": {
                                              "id": segment["id"],
                                              "display_name": segment["properties"]["display_name"],
                                              "geometry": segment["geometry"]
                                          },
                                          "year": pred_data["year"],
                                          "week": pred_data["week"],
                                          "value": pred_data["prediction"]
                                          })
                break
        
    print(merged_preds_segs[0])
        
