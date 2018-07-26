import dateutil.parser as date_parser
import re
from datetime import timedelta


def parse_date(date, time=None):

    # Date can either be a date or a date time
    date = date_parser.parse(date)
    # If there's no time in the date given, look at the time field
    # if available
    if date.hour == 0 and date.minute == 0 and date.second == 0 \
       and time:

        # special case of seconds past midnight
        if re.match(r"^\d+$", str(time)) and int(time) >= 0 \
           and int(time) < 86400:
            date = date + timedelta(seconds=time)

        else:
            date = date_parser.parse(
                date.strftime('%Y-%m-%d ') + str(time)
            )

    # TODO add timezone to config ("Z" is UTC)
    date_time = date.strftime("%Y-%m-%dT%H:%M:%SZ")

    return date_time
