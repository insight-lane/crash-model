# Transform a concerns CSV into compatible JSON document.
# Author terryf82 https://github.com/terryf82

import json
import os
import pandas as pd
from collections import OrderedDict

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

DATA_DIR = os.path.join(BASE_DIR, "src/osm-data/dc/raw")

concerns_path = os.path.join(DATA_DIR, "concerns.csv")

if not os.path.exists(concerns_path):
    print "concerns input not found, skipping"

else:
    print "converting concerns csv to json"
    raw_concerns_df = pd.read_csv(concerns_path)
    raw_concerns_dict = raw_concerns_df.to_dict("records")

    valid_concerns = []

    for key in raw_concerns_dict:
        valid_concern = OrderedDict([
            ("id", key["OBJECTID"]),
            ("dateCreated", key["REQUESTDATE"]),
            ("status", key["STATUS"]),
            ("tags", [key["REQUESTTYPE"]]),
            ("location", OrderedDict([
                ("latitude", key["X"]),
                ("longitude", key["Y"])
            ])),
            ("summary", key["COMMENTS"])
        ])

        valid_concerns.append(valid_concern)

    with open(os.path.join(BASE_DIR, "src/osm-data/dc/validated/concerns.json"), "w") as f:
        json.dump(valid_concerns, f)

    print "done, {} valid concerns loaded".format(len(valid_concerns))
