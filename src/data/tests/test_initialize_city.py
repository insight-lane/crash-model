import .. import initialize_city

def test_initialize_city_brisbane():

    # Generate a test config for Brisbane
    initialize_city.make_config_file(
        'test_config_brisbane.yml',
        'Brisbane, Australia',
        'brisbane',
        'test_crashes.csv',
        'test_concerns.csv'
    )

    # check that the file contents generated is identical to a pre-built string
    # assert...
