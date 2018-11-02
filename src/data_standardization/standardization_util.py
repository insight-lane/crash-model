import dateutil.parser as date_parser
from datetime import datetime, timedelta
import json
from jsonschema import validate
from dateutil import tz


def parse_date(date, timezone, time=None, time_format=None):
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
    if date.hour == 0 and date.minute == 0 and date.second == 0 and time:
        
        if time_format == "military":
            # military times less than 4 chars require padding with leading zeros
            # e.g 155 becomes 0155
            while (len(str(time)) < 4):
                time = "0" + str(time)
            
            # ignore invalid times
            if int(time) <= 2359:
                date = date_parser.parse(
                    date.strftime('%Y-%m-%d ') + datetime.strptime(str(time), '%H%M').strftime('%I:%M%p').lower()
                )
            
            else:
                date = date_parser.parse(
                    date.strftime('%Y-%m-%d ')
                )
            
        elif time_format == "seconds":
            date = date + timedelta(seconds=int(time))
        
        else:
            date = date_parser.parse(
                date.strftime('%Y-%m-%d ') + str(time)
            )

    # Add timezone if it wasn't included in the string formatting originally
    if not date.tzinfo:
        date = timezone.localize(date)
    # If the timezone was set to utc, reformat into local time with offset
    elif date.tzinfo == tz.tzutc():
        date = date.astimezone(timezone)
    date_time = date.isoformat()
    
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
