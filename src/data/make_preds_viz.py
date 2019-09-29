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
import data.config


def combine_predictions_and_segments(predictions, segments):
    """
    Combine predictions data with certain properties of their related segment.
    """

    print("combining predictions with segments")
    combined_preds = []

    # turns segments into a dict for quick lookup
    segments_dict = {str(segment["id"]): segment for segment in segments}

    for pred_data in predictions:
        segment = segments_dict[str(pred_data["segment_id"])]
        prop = {
            "prediction": pred_data["prediction"],
            "crash": pred_data["crash"],
            "segment_id": pred_data["segment_id"]
        }
        # Eventually handle osm_speed vs SPEEDLIMIT as part
        # of the configuration
        if 'SPEEDLIMIT' in pred_data:
            prop['SPEEDLIMIT'] = pred_data['SPEEDLIMIT']
        elif 'osm_speed' not in pred_data:
            prop['osm_speed'] = 0
        else:
            prop['osm_speed'] = pred_data['osm_speed']

        prop["segment"] = {
            "id": str(segment["id"]),
            "display_name": segment["properties"]["display_name"],
            "center_x": segment["properties"]["center_x"],
            "center_y": segment["properties"]["center_y"]
        }

        combined_preds.append(geojson.Feature(
            geometry=segment["geometry"],
            properties=prop
        ))

    # Sort highest risk to lowest risk
    combined_preds = sorted(
        combined_preds,
        key=lambda x: x['properties']['prediction'],
        reverse=True
    )

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


def write_all_preds(DATA_FP, config):
    """
    For each split column, read prediction file and write postprocessed file
    Args:
        DATA_FP - the data directory
        config - a configuration object
    """
    # confirm files exist & load data
    files = {}
    for column in config.split_columns:
        files["seg_with_predicted_" + column + '.json'] = column
    if not files:
        files["seg_with_predicted.json"] = None

    for filename, column in files.items():
        predictions_file = os.path.join(
            DATA_FP, "processed", filename)
        if not os.path.exists(predictions_file):
            sys.exit("predictions file not found at {}, exiting".format(
                predictions_file))

        # load the predictions
        print("loading predictions: ", end="")
        preds_data = pd.read_json(
            predictions_file, orient="index", typ="series", dtype=False)
        print("{} found".format(len(preds_data)))

        segments_file = os.path.join(
            DATA_FP, "processed", "maps", "inter_and_non_int.geojson")
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
        output_file = "preds_viz"
        if column:
            output_file += "_" + column
        output_file += ".geojson"

        write_preds_as_geojson(preds_viz, os.path.join(
            DATA_FP, "processed", output_file))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="data directory")
    parser.add_argument("-c", "--config", type=str,
                        help="yml file for model config"
    )

    args = parser.parse_args()
    config = data.config.Configuration(args.config)
    write_all_preds(args.datadir, config)
