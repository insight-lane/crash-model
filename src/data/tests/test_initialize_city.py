import py
import sys
import initialize_city


def mockreturn(address):
    return "Brisbane, Australia", -27.4697707, 153.0251235, 'S'


def test_initialize_city_brisbane_no_supplemental(monkeypatch):

    monkeypatch.setattr(initialize_city, 'geocode_address', mockreturn)
    tmpdir = py.path.local('/tmp')

    # Generate a test config for Brisbane
    initialize_city.make_config_file(
        tmpdir.join('/test_config_brisbane.yml'),
        'Brisbane, Australia',
        'brisbane',
        'test_crashes.csv',
        'test_concerns.csv'
    )

    # check that the file contents generated is identical to a pre-built string
    expected_file_contents = """# City name
city: Brisbane, Australia
# City centerpoint latitude & longitude (default geocoded values set)
city_latitude: -27.4697707
city_longitude: 153.0251235
# Radius of city's road network from centerpoint in km, required if OSM has no polygon data (defaults to 20km)
city_radius: 20
# The folder under data where this city's data is stored
name: brisbane
# If given, limit crashes to after start_year and before end_year
# Recommended to limit to just a few years for now
start_year: 
end_year: 


#################################################################
# Configuration for data standardization

# crash file configurations
crashes_files:
  test_crashes.csv:
    required:
      id: 
      latitude: 
      longitude: 
      # If date supplied in single column:
      date_complete: 
      # If date is separated into year/month/day:
      date_year: 
      date_month: 
      # Leave date_day empty if not available
      date_day: 
      # If time is available and separate from date:
      time: 
      # If time specified, time_format is one of:
      # default (HH:MM:SS)
      # seconds (since midnight)
      # military (HHMM)
      time_format: 
    optional:
      summary: 
      address: 
      vehicles: 
      bikes: 

# List of concern type information
concern_files:
  - name: concern
      filename: test_concerns.csv
      latitude: 
      longitude: 
      time: 


# week on which to predict crashes (week, year)
# Best practice is to choose a week towards the end of your crash data set
# in format [month, year]
time_target: [30, 2017]
# specify how many weeks back to predict in output of train_model
weeks_back: 1"""

    with open(tmpdir.join('/test_config_brisbane.yml'), 'r') as test_file:
        test_file_contents = test_file.read()

    assert test_file_contents == expected_file_contents


def test_supplemental_argument_should_change_content_of_config_file(monkeypatch):

    monkeypatch.setattr(initialize_city, 'geocode_address', mockreturn)
    tmpdir = py.path.local('/tmp')

    # Generate a test config for Brisbane
    initialize_city.make_config_file(
        tmpdir.join('/test_config_brisbane.yml'),
        'Brisbane, Australia',
        'brisbane',
        'test_crashes.csv',
        'test_concerns.csv',
        ['parking_tickets_dummy_file_1.csv']
    )

    # check that the file contents generated is identical to a pre-built string
    expected_file_contents = """# City name
city: Brisbane, Australia
# City centerpoint latitude & longitude (default geocoded values set)
city_latitude: -27.4697707
city_longitude: 153.0251235
# Radius of city's road network from centerpoint in km, required if OSM has no polygon data (defaults to 20km)
city_radius: 20
# The folder under data where this city's data is stored
name: brisbane
# If given, limit crashes to after start_year and before end_year
# Recommended to limit to just a few years for now
start_year: 
end_year: 


#################################################################
# Configuration for data standardization

# crash file configurations
crashes_files:
  test_crashes.csv:
    required:
      id: 
      latitude: 
      longitude: 
      # If date supplied in single column:
      date_complete: 
      # If date is separated into year/month/day:
      date_year: 
      date_month: 
      # Leave date_day empty if not available
      date_day: 
      # If time is available and separate from date:
      time: 
      # If time specified, time_format is one of:
      # default (HH:MM:SS)
      # seconds (since midnight)
      # military (HHMM)
      time_format: 
    optional:
      summary: 
      address: 
      vehicles: 
      bikes: 

# List of concern type information
concern_files:
  - name: concern
      filename: test_concerns.csv
      latitude: 
      longitude: 
      time: 


# Additional data sources
data_source:
  - name: parking_tickets
    filename: parking_tickets_dummy_file_1.csv
    address: 
    date: 
    time: 
    category: 
    notes: 
    # Feature is categorical (f_cat) or continuous (f_cont)
    feat: 

# week on which to predict crashes (week, year)
# Best practice is to choose a week towards the end of your crash data set
# in format [month, year]
time_target: [30, 2017]
# specify how many weeks back to predict in output of train_model
weeks_back: 1"""

    with open(tmpdir.join('/test_config_brisbane.yml'), 'r') as test_file:
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
