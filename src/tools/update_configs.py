# Update config files
import argparse
import ruamel.yaml


def add_feature(filename, feat_info):
    """
    Add new features to a config file
    Args:
        filename - config file
        feat_info - a list consisting of
          - feature set type (e.g. openstreetmap_features)
          - feature type (categorical or continuuous)
          - feature (the name of the feature, e.g. width)
          - feature name (human readable feature name)
        If the feature set type doesn't exist, it will be added,
        but it needs to be in the set of feature set types possible:
        openstreetmap_features or waze_features
    """
    with open(filename, 'r') as myfile:
        yaml_str = myfile.read()

    config = ruamel.yaml.round_trip_load(yaml_str)

    if len(feat_info) != 4:
        print("Wrong number of args to -a")
        return
    
    feat_set = feat_info[0]
    if feat_set not in ('openstreetmap_features', 'waze_features'):
        print("feature set given is not valid")
        return

    feat_type = feat_info[1]
    feat = feat_info[2]
    feat_name = feat_info[3]

    # If the feature set doesn't exist, add it
    if feat_set not in config:
        config.insert(
            len(config), feat_set, ruamel.yaml.comments.CommentedMap())

    # if the feat_type doesn't exist, add it
    if feat_type not in config[feat_set]:
        config[feat_set][feat_type] = {}
    # if the feature does not exist, add it
    if feat not in config[feat_set][feat_type]:
        config[feat_set][feat_type][feat] = feat_name
    else:
        print("Feature already exists, skipping")
    with open(filename, "w") as f:
        ruamel.yaml.round_trip_dump(config, f)


if __name__ == '__main__':
    """
    Examples
    - Add a feature to open street map features
    - -a "openstreetmap_features categorical test human readable name"
    - Add a feature to waze features
    - Remove a feature from osm or waze
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filenames", nargs="+",
                        help="config filenames",
                        required=True)
    parser.add_argument("-a", "--addfeatures", nargs="+",
                        help="Feature to add, a string with feature set " +
                        "(e.g. openstreetmap_features)," +
                        "feature type (categorical or continuous), " +
                        "feature name, human readable feature name in quotes")
    args = parser.parse_args()

    if args.addfeatures:
        for filename in args.filenames:
            add_feature(filename, args.addfeatures)

