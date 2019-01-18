import py
import os
import initialize_city

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def mockreturn(address):
    return "Brisbane, Australia", -27.4697707, 153.0251235, 'S'


def test_initialize_city_brisbane_no_supplemental(tmpdir, monkeypatch):

    monkeypatch.setattr(initialize_city, 'geocode_address', mockreturn)

    # Generate a test config for Brisbane
    initialize_city.make_config_file(
        tmpdir.join('/test_config_brisbane_no_supplemental.yml'),
        'Brisbane, Australia',
        'Australia/Brisbane',
        'brisbane',
        'test_crashes.csv',
        'test_concerns.csv',
        False
    )

    # check that the file contents generated is identical to a pre-built string
    with open(tmpdir.join(
            '/test_config_brisbane_no_supplemental.yml'), 'r') as test_file:
        test_file_contents = test_file.read()
    with open(os.path.join(
            TEST_FP, 'data', 'config_brisbane_no_supplemental.yml'), 'r'
    ) as test_file:
        expected_file_contents = test_file.read()
    assert test_file_contents == expected_file_contents


def test_supplemental_arg_changes_content_of_config_file(tmpdir, monkeypatch):

    monkeypatch.setattr(initialize_city, 'geocode_address', mockreturn)

    # Generate a test config for Brisbane
    initialize_city.make_config_file(
        tmpdir.join('/test_config_brisbane_supplemental.yml'),
        'Brisbane, Australia',
        'Australia/Brisbane',
        'brisbane',
        'test_crashes.csv',
        'test_concerns.csv',
        ['parking_tickets_dummy_file_1.csv']
    )

    with open(tmpdir.join(
            '/test_config_brisbane_supplemental.yml'), 'r') as test_file:
        expected_file_contents = test_file.read()

    with open(tmpdir.join(
            '/test_config_brisbane_supplemental.yml'), 'r') as test_file:
        test_file_contents = test_file.read()
    assert test_file_contents == expected_file_contents


def test_make_js_config_brisbane(monkeypatch):

    def mockreturn(address):
        return "Brisbane, Australia", -27.4697707, 153.0251235, 'S'

    monkeypatch.setattr(initialize_city, 'geocode_address', mockreturn)
    tmpdir = py.path.local('/tmp')

    # Generate a test config for Brisbane
    initialize_city.make_js_config(
        tmpdir.join('/test_js_config_brisbane.js'),
        'Brisbane, Australia',
        'brisbane',
    )

    # check that the file contents generated is identical to a pre-built string
    expected_file_contents = """var config = {
    MAPBOX_TOKEN: "",
    cities: [
        {
            name: "Brisbane, Australia",
            id: "brisbane",
            latitude: -27.4697707,
            longitude: 153.0251235,
        }
    ]
}
"""

    with open(tmpdir.join('/test_js_config_brisbane.js'), 'r') as test_file:
        test_file_contents = test_file.read()

    assert test_file_contents == expected_file_contents
