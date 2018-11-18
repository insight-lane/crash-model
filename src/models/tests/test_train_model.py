import os
import pandas as pd
from .. import train_model

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_features():
    data = pd.DataFrame(data={
        'width': [10, 12],
        'signal': [1, 0],
        'jam_percent': [1, 12],
        'lanes': [2, 1]
    })
    f_cat, f_cont, feats = train_model.get_features(
        {'atr': '', 'tmc': '', 'concern': ''},
        data,
        os.path.join(TEST_FP, 'data')
    )
    assert f_cat == ['width']
    assert f_cont == ['lanes', 'signal', 'jam_percent']
    assert feats == ['lanes', 'signal', 'jam_percent', 'width']
    

def test_initialize_and_run(tmpdir):
    # For now, just test the model runs
    model = pd.read_csv(os.path.join(TEST_FP, 'data', 'data_model.csv'))
    # Since we're going to test
    features = ['lanes0', 'oneway1', 'log_width', 'lanes1', 'signal2',
                'hwy_type1', 'hwy_type5', 'oneway0', 'signal1', 'hwy_type9',
                'lanes3', 'lanes2', 'intersection', 'osm_speed0',
                'osm_speed25', 'signal0', 'hwy_type0']
    train_model.initialize_and_run(model, features, features, 'segment',
                                   tmpdir, seed=1)
