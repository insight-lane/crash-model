"""
Title: make_preds_viz.py

Author: terryf82 https://github.com/terryf82

Merge predictions with relevant segment data for use by visualization.

Inputs:
    seg_with_predicted.json (predictions)
    inter_and_non_int.geojson (segments)

Output:
    preds_viz.json
"""

import argparse
import os
import pandas as pd
import geojson
import sys

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

DATA_FP = os.path.join(BASE_DIR, 'data')


def combine_predictions_and_segments(predictions, segments):
    """
    Combine predictions data with certain properties of their related segment.
    """

    print("combining predictions with segments")
    combined_preds = []
    for pred_data in predictions:
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
                    geometry=segment["geometry"],
                    properties=pred_data,
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
    parser.add_argument("-d", "--datadir", type=str,
                        help="data directory")

    args = parser.parse_args()

    # print(os.getcwd())

    # confirm files exist & load data
    predictions_file = os.path.join(
        DATA_FP, args.datadir, "processed", "seg_with_predicted.json")
    if not os.path.exists(predictions_file):
        sys.exit("predictions file not found at {}, exiting".format(
            predictions_file))

    # load the predictions
    print("loading predictions: ", end="")
    preds_data = pd.read_json(
        predictions_file, orient="index", typ="series", dtype=False)
    print("{} found".format(len(preds_data)))

    segments_file = os.path.join(
        DATA_FP, args.datadir, "processed", "maps", "inter_and_non_int.geojson")
    if not os.path.exists(segments_file):
        sys.exit("segment file not found at {}, exiting".format(segments_file))

    # load the segments
    print("loading segments: ", end="")
    segs_features = pd.read_json(segments_file)
    # TODO segments data standard should probably key each segment by its id
    segs_data = segs_features["features"]
    print("{} found".format(len(segs_data)))

    # output the combined prediction + segment data for use
    preds_viz = combine_predictions_and_segments(preds_data, segs_data)
    write_preds_as_geojson(preds_viz, os.path.join(
        DATA_FP, args.datadir, "processed", "preds_viz.geojson"))
