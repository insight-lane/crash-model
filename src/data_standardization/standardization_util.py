import dateutil.parser as date_parser
import re
from datetime import timedelta
import json
from jsonschema import validate


def parse_date(date, time=None):
    """
    Turn a date (and optional time) into a datetime string
    in standardized format
    """

    # If date is badly formatted, skip
    try:
        # Date can either be a date or a date time
        date = date_parser.parse(date)
    except ValueError as _:
        print("{} is badly formatted, skipping".format(date))
        return None

    # If there's no time in the date given, look at the time field
    # if available
    if date.hour == 0 and date.minute == 0 and date.second == 0 \
       and time:

        # special case of seconds past midnight
        if re.match(r"^\d+$", str(time)) and int(time) >= 0 \
           and int(time) < 86400:
            date = date + timedelta(seconds=int(time))

        else:
            date = date_parser.parse(
                date.strftime('%Y-%m-%d ') + str(time)
            )

    # TODO add timezone to config ("Z" is UTC)
    date_time = date.strftime("%Y-%m-%dT%H:%M:%SZ")

    return date_time


def parse_address(address):
    """
    Some cities have the lat/lon as part of the address.
    If that's the format, parse out these values
    """
    lines = address.split('\n')
    if len(lines) == 3 and lines[2]:
        lat, lon = lines[2][1:-1].split(', ')
        return float(lat), float(lon)
    return None, None


def validate_and_write_schema(schema_path, schema_values, output_file):
    """
    Validate a schema according to a schema file, and write to file
    Args:
        schema_path - the schema filename
        schema_values - a list of dicts
        output_file
    """

    with open(schema_path) as schema:
        validate(schema_values, json.load(schema))

    with open(output_file, "w") as f:
        json.dump(schema_values, f)

    print("- output written to {}".format(output_file))
