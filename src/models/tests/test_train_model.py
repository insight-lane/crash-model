import os
import ruamel.yaml
import pandas as pd
from .. import train_model
import data.config


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_features(tmpdir):
    test_data = pd.DataFrame(data={
        'width': [10, 12],
        'signal': [1, 0],
        'jam_percent': [1, 12],
        'lanes': [2, 1]
    })
    config_dict = {
        'name': 'cambridge',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'crashes_files': {'test': {}},
        'city': "Cambridge, Massachusetts, USA",
        'timezone': "America/New_York",
        'openstreetmap_features': {
            'categorical': {
                'signal': 'Signal',
                'test_missing': 'Missing Field'
            },
            'continuous': {'missing': 'Missing Field'}
        },
        'atr': '',
        'tmc': '',
        'concern': ''
    }

    config_filename = os.path.join(tmpdir, 'test.yml')
    with open(config_filename, "w") as f:
        ruamel.yaml.round_trip_dump(config_dict, f)
    config = data.config.Configuration(config_filename)

    f_cat, f_cont, feats = train_model.get_features(config, test_data)
    assert f_cat == ['signal']
    assert f_cont == []
    assert feats == ['signal']

def test_process_features(tmpdir):
    test_data = pd.DataFrame(data={
        'width': [10, 12],
        'signal': [1, 0],
        'jam_percent': [0, 0],
        'lanes': [2, 1],
        'segment_id': ['001', '002']
    })
    f_cat = ['signal', 'lanes']
    f_cont = ['width', 'jam_percent']
    features = ['signal', 'lanes', 'width', 'jam_percent']
    test_data, features, lm_features = train_model.process_features(features, f_cat, f_cont, test_data)
    assert set(features) == set(['intersection', 'signal_1', 'signal_0', 'log_width', 'lanes_2', 'lanes_1'])
    assert set(lm_features) == set(['intersection', 'signal_1', 'log_width', 'lanes_2'])
    

def test_initialize_and_run(tmpdir):
    # For now, just test the model runs
    model = pd.read_csv(os.path.join(TEST_FP, 'data', 'data_model.csv'))
    # Since we're going to test
    features = ['lanes0', 'oneway1', 'log_width', 'lanes1', 'signal2',
                'hwy_type1', 'hwy_type5', 'oneway0', 'signal1', 'hwy_type9',
                'lanes3', 'lanes2', 'intersection', 'osm_speed0',
                'osm_speed25', 'signal0', 'hwy_type0']
    train_model.initialize_and_run(model, features, features, 'target',
                                   tmpdir, seed=1)
