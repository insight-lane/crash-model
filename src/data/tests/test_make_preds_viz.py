import os
import pandas as pd
import ruamel
import shutil
import data.config
from .. import make_preds_viz

DATA_FP = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    "data",
    "viz_preds_tests",
)


def test_make_preds_viz_boston(tmpdir):
    """
    Confirm that predictions & segments are combined as expected.
    """
    # load the test predictions & segments
    preds_test = pd.read_json(
        os.path.join(DATA_FP,
                     "single_prediction.json"),
        orient="index", typ="series", dtype=False
    )
    
    segs_test = pd.read_json(os.path.join(
        DATA_FP, "single_segment.geojson"))["features"]
    
    # combine the two
    preds_combined_test = make_preds_viz.combine_predictions_and_segments(preds_test, segs_test)
    
    # write to file
    tmpdir_test_path = os.path.join(tmpdir.strpath, "preds_viz.geojson")
    make_preds_viz.write_preds_as_geojson(preds_combined_test, tmpdir_test_path)
    
    # compare the new file's contents to test data
    tmpdir_preds_viz = pd.read_json(os.path.join(tmpdir.strpath, "preds_viz.geojson"))
    preds_viz_test = pd.read_json(os.path.join(
        DATA_FP, "single_prediction_viz.geojson")
    )
    
    assert (tmpdir_preds_viz.equals(preds_viz_test))


def test_write_all_preds(tmpdir):
    config_dict = {
        'name': 'cambridge',
        'crashes_files': {
            'file1': {}
        },
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York",

    }
    config_filename = os.path.join(tmpdir, 'test.yml')

    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    os.makedirs(os.path.join(tmpdir, 'processed'))
    os.makedirs(os.path.join(tmpdir, 'processed', 'maps'))
    shutil.copy(
        os.path.join(
            DATA_FP,
            'single_prediction.json'),
        os.path.join(
            tmpdir,
            'processed',
            'seg_with_predicted.json'
        )
    )
    shutil.copy(
        os.path.join(
            DATA_FP,
            'single_segment.geojson'),
        os.path.join(
            tmpdir,
            'processed',
            'maps',
            'inter_and_non_int.geojson'
        )
    )
    make_preds_viz.write_all_preds(tmpdir, config)
    assert os.path.exists(os.path.join(
        tmpdir, 'processed', 'preds_viz.geojson'))


def test_write_all_preds_split_column(tmpdir):
    config_dict = {
        'name': 'cambridge',
        'crashes_files': {
            'file1': {
                'optional': {
                    'split_columns': {
                        'pedestrian': {}
                    }
                }

            }
        },
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York",

    }
    config_filename = os.path.join(tmpdir, 'test.yml')

    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    os.makedirs(os.path.join(tmpdir, 'processed'))
    os.makedirs(os.path.join(tmpdir, 'processed', 'maps'))
    shutil.copy(
        os.path.join(
            DATA_FP,
            'single_prediction.json'),
        os.path.join(
            tmpdir,
            'processed',
            'seg_with_predicted_pedestrian.json'
        )
    )
    shutil.copy(
        os.path.join(
            DATA_FP,
            'single_segment.geojson'),
        os.path.join(
            tmpdir,
            'processed',
            'maps',
            'inter_and_non_int.geojson'
        )
    )
    make_preds_viz.write_all_preds(tmpdir, config)
    assert os.path.exists(os.path.join(
        tmpdir, 'processed', 'preds_viz_pedestrian.geojson'))
