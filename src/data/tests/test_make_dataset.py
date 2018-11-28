import os
from .. import make_dataset
import yaml

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_make_feature_list(tmpdir):
    os.makedirs(os.path.join(tmpdir.strpath, 'processed'))

    make_dataset.make_feature_list({}, tmpdir)
    config_file = os.path.join(tmpdir.strpath, 'processed', 'features.yml')
    print(tmpdir)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    assert config == {
        'f_cat': ['width', 'cycleway_type', 'signal', 'oneway'],
        'f_cont': [
            'lanes',
            'hwy_type',
            'osm_speed',
            'width_per_lane'
        ]
    }
    make_dataset.make_feature_list({}, tmpdir, waze=True)
    with open(config_file) as f:
        config = yaml.safe_load(f)

    assert config == {
        'f_cat': ['width', 'cycleway_type', 'signal', 'oneway', 'jam'],
        'f_cont': [
            'lanes',
            'hwy_type',
            'osm_speed',
            'width_per_lane',
            'jam_percent'
        ]
    }

    additional_features = {
        'f_cont': 'AADT',
        'f_cat': 'SPEEDLIMIT Struct_Cnd Surface_Tp F_F_Class'
    }

    make_dataset.make_feature_list({
        'additional_features': additional_features}, tmpdir)
    with open(config_file) as f:
        config = yaml.safe_load(f)
    print(config)
    assert config == {
        'f_cat': [
            'width',
            'cycleway_type',
            'signal',
            'oneway',
            'SPEEDLIMIT',
            'Struct_Cnd',
            'Surface_Tp',
            'F_F_Class'
        ],
        'f_cont': [
            'lanes',
            'hwy_type',
            'osm_speed',
            'width_per_lane',
            'AADT'
        ]
    }
