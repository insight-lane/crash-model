from .. import update_configs
import os


TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_add_feature(tmpdir):

    # Write a test config to file
    test_config = """
# Test comments are preserved

openstreetmap_features:
  categorical:
    width: Width
"""
    config_filename = os.path.join(tmpdir, 'test.yml')
    with open(config_filename, "w") as f:
        f.write(test_config)

    update_configs.add_feature(config_filename, [
        'openstreetmap_features',
        'categorical',
        'test',
        'Test Name'
    ])
    update_configs.add_feature(config_filename, [
        'openstreetmap_features',
        'continuous',
        'another_test',
        'Test Name2'
    ])

    with open(config_filename) as f:
        result = f.read()
    assert result == """# Test comments are preserved

openstreetmap_features:
  categorical:
    width: Width
    test: Test Name
  continuous:
    another_test: Test Name2
"""
