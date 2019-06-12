import argparse
import os
from jsonschema import validate
import json
from .boston_volume import BostonVolumeParser
import data.config

BASE_FP = None
PROCESSED_DATA_FP = None
CURR_FP = os.path.dirname(
    os.path.abspath(__file__))


def write_volume(volume_counts):

    schema_path = os.path.join(os.path.dirname(os.path.dirname(
        CURR_FP)), "standards", "volumes-schema.json")
    with open(schema_path) as volume_schema:
        validate(volume_counts, json.load(volume_schema))
        volume_output = os.path.join(BASE_FP, "standardized", "volume.json")
        with open(volume_output, "w") as f:
            json.dump(volume_counts, f)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="city config filename")
    parser.add_argument("-d", "--datadir", type=str,
                        help="data directory")

    args = parser.parse_args()
    BASE_FP = os.path.join(args.datadir)

    config = data.config.Configuration(args.config)
    if config.name == 'boston':
        volume_counts = BostonVolumeParser(args.datadir).get_volume()
        write_volume(volume_counts)
    else:
        print("No volume data given for {}".format(config.name))
