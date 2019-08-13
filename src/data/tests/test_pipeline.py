
import os
import shutil
import pipeline
import ruamel
import data.config


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_copy_files(tmpdir):

    base_dir = os.path.join(tmpdir, 'base')
    data_dir = os.path.join(tmpdir, 'data')
    print(TEST_FP)
    os.makedirs(base_dir)
    os.makedirs(os.path.join(base_dir, 'processed'))
    os.makedirs(data_dir)
    os.makedirs(os.path.join(data_dir, 'processed'))

    orig_file = os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'single_prediction_viz.geojson')
    print(orig_file)

    shutil.copy(
        os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'single_prediction_viz.geojson'),
        os.path.join(
            data_dir,
            'processed',
            'preds_viz.geojson'
        )
    )
    shutil.copy(
        os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'crashes_rollup_all.geojson'),
        os.path.join(
            data_dir,
            'processed',
            'crashes_rollup_all.geojson'
        )
    )
    shutil.copy(
        os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'crashes_rollup_pedestrian.geojson'),
        os.path.join(
            data_dir,
            'processed',
            'crashes_rollup_pedestrian.geojson'
        )
    )
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

    pipeline.copy_files(
        base_dir,
        data_dir,
        config
    )
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'crashes_rollup_all.geojson'))
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'crashes_rollup_pedestrian.geojson'))
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'preds_viz.geojson'))
