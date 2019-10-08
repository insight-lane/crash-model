
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
            'preds_viz_pedestrian.geojson'
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
        'crashes_rollup_pedestrian.geojson'))
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'preds_viz_pedestrian.geojson'))


def test_make_js_config_brisbane(tmpdir):

    config_dict = {
        'name': 'brisbane',
        'crashes_files': {
            'file1': {}
        },
        'speed_unit': 'kph',
        'city_latitude': -27.4697707,
        'city_longitude': 153.0251235,
        'city_radius': 10,
        'city': "Brisbane, Australia",
        'timezone': "Australia/Brisbane",

    }
    config_filename = os.path.join(tmpdir, 'test.yml')

    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    # Generate a test config for Brisbane
    pipeline.make_js_config(
        tmpdir,
        config
    )

    # check that the file contents generated is identical to a pre-built string
    expected_file_contents = """var config = [
    {
        name: "Brisbane, Australia",
        id: "brisbane",
        latitude: -27.4697707,
        longitude: 153.0251235,
        speed_unit: "kph",
        file: "data/brisbane/preds_viz.geojson",
        crashes: "data/brisbane/crashes_rollup.geojson"
    }
]"""
    expected_file_contents = expected_file_contents.lstrip()
    
    with open(tmpdir.join(
            '/src/showcase/data/config_brisbane.js'
    ), 'r') as test_file:
        test_file_contents = test_file.read()
    assert test_file_contents == expected_file_contents


def test_make_js_config_boston(tmpdir):

    config_dict = {
        'name': 'boston',
        'crashes_files': {
            'file1': {
                'optional': {
                    'split_columns': {
                        'pedestrian': {},
                        'bike': {}
                    }
                }
            }
        },
        'speed_unit': 'mph',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'city': "Boston, Massachusetts, USA",
        'timezone': "America/New_York",

    }
    config_filename = os.path.join(tmpdir, 'test.yml')

    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    # Generate a test config for Boston
    pipeline.make_js_config(
        tmpdir,
        config
    )

    # check that the file contents generated is identical to a pre-built string
    expected_file_contents = """var config = [
    {
        name: "Boston, Massachusetts, USA (pedestrian)",
        id: "boston_pedestrian",
        latitude: 42.3600825,
        longitude: -71.0588801,
        speed_unit: "mph",
        file: "data/boston/preds_viz_pedestrian.geojson",
        crashes: "data/boston/crashes_rollup_pedestrian.geojson"
    },
    {
        name: "Boston, Massachusetts, USA (bike)",
        id: "boston_bike",
        latitude: 42.3600825,
        longitude: -71.0588801,
        speed_unit: "mph",
        file: "data/boston/preds_viz_bike.geojson",
        crashes: "data/boston/crashes_rollup_bike.geojson"
    },
]"""
    expected_file_contents = expected_file_contents.lstrip()

    with open(tmpdir.join(
            '/src/showcase/data/config_boston.js'
    ), 'r') as test_file:
        test_file_contents = test_file.read()
    assert test_file_contents == expected_file_contents
