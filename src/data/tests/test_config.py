import os
import ruamel.yaml
import data.config


def write_to_file(filename, d):
    with open(filename, "w") as f:
        ruamel.yaml.round_trip_dump(d, f)


def test_get_feature_list(tmpdir):

    config_dict = {
        'city': 'Boston, Massachusetts, USA',
        'name': 'boston',
        'city_latitude': 42.3600825,
        'city_longitude': -71.0588801,
        'city_radius': 15,
        'timezone': 'America/New_York',
        'crashes_files': {'test': {}},
        'openstreetmap_features': {
            'categorical': {
                'width': 'Width',
                'cycleway_type': 'Bike lane',
                'signal': 'Signal',
                'oneway': 'One Way',
                'lanes': 'Number of lanes'
            },
            'continuous': {
                'width_per_lane': 'Average width per lane'
            }
        },
    }

    yml_file = os.path.join(tmpdir, 'test.yml')
    write_to_file(yml_file, config_dict)
    config = data.config.Configuration(yml_file)
    assert config.continuous_features == ['width_per_lane']
    assert config.categorical_features == [
        'width', 'cycleway_type', 'signal', 'oneway', 'lanes', 'osm_speed']
    assert set(config.features) == set([
        'width', 'cycleway_type', 'signal',
        'oneway', 'lanes', 'width_per_lane',
        'osm_speed'
    ])

    config_dict['waze_features'] = {
        'categorical': {'jam': 'Existence of a jam'},
        'continuous': {'jam_percent': 'Percent of time there was a jam'}
    }
    write_to_file(yml_file, config_dict)
    config = data.config.Configuration(yml_file)

    assert config.continuous_features == ['width_per_lane', 'jam_percent']
    assert config.categorical_features == [
        'width', 'cycleway_type', 'signal',
        'oneway', 'lanes', 'jam', 'osm_speed']
    assert set(config.features) == set([
        'width_per_lane', 'jam_percent',
        'width', 'cycleway_type', 'signal',
        'oneway', 'lanes', 'jam', 'osm_speed'])

    config_dict['waze_features'] = {}
    config_dict['openstreetmap_features'] = {}
    config_dict['additional_map_features'] = {
        'extra_map': 'test',
        'continuous': {'AADT': 'test name'},
        'categorical': {
            'Struct_Cnd': 'test name3',
            'Surface_Tp': 'test name4',
            'F_F_Class': 'test name5'
        }
    }
    config_dict['speed_limit'] = 'SPEEDLIMIT'

    write_to_file(yml_file, config_dict)
    config = data.config.Configuration(yml_file)

    assert set(config.categorical_features) == set([
        'SPEEDLIMIT', 'Struct_Cnd', 'Surface_Tp', 'F_F_Class'])
    assert config.continuous_features == ['AADT']
    assert set(config.features) == set([
        'SPEEDLIMIT', 'Struct_Cnd', 'Surface_Tp', 'F_F_Class', 'AADT'])
