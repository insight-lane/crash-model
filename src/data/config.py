import sys
import pytz
import yaml


# Configuration object
class Configuration(object):
    """A configuration object deals with everything that we specify
     in the city-specific config file, along with a few hard-coded features
    """
    def __init__(self, filename):
        with open(filename) as f:
            config = yaml.safe_load(f)

        if 'city' not in config or config['city'] is None:
            sys.exit('City is required in config file')
        self.city = config['city']
        
        if 'city_latitude' not in config or config['city_latitude'] is None:
            sys.exit('city_latitude is required in config file')
        self.city_latitude = config['city_latitude']

        if 'city_longitude' not in config or config['city_longitude'] is None:
            sys.exit('city_longitude is required in config file')
        self.city_longitude = config['city_longitude']

        if 'city_radius' not in config or config['city_radius'] is None:
            sys.exit('city_radius is required in config file')
        self.city_radius = config['city_radius']

        if 'map_geography' in config and config['map_geography']:
            self.map_geography = config['map_geography']
        else:
            # The default, if not set, is polygon
            self.map_geography = 'polygon'
        if 'boundary_shapefile' in config and config['boundary_shapefile']:
            self.boundary_shapefile = config['boundary_shapefile']
            if 'map_geography' not in config \
               or not config['map_geography'] \
               or config['map_geography'] != 'shapefile':
                sys.exit('If boundary_shapefile is set, map_geography must be shapefile')

        self.default_features, self.categorical_features, \
            self.continuous_features = self.get_feature_list(config)

        self.name = config['name']
        self.startdate = str(config['startdate']) \
            if 'startdate' in config and config['startdate'] else None
        self.enddate = str(config['enddate']) \
            if 'enddate' in config and config['enddate'] else None
        self.timezone = pytz.timezone(config['timezone'])
        self.crashes_files = config['crashes_files']
        
        self.data_source = config['data_source'] if 'data_source' in config \
            else None
        self.additional_map_features = config['additional_map_features'] \
            if 'additional_map_features' in config \
               else None
        if 'atr' in config and config['atr'] and 'atr_cols' in config and config['atr_cols']:
            self.atr = config['atr']
            self.atr_cols = ['speed_coalesced', 'volume_coalesced']
        else:
            self.atr_cols = None
        if 'tmc' in config and config['tmc'] and 'tmc_cols' in config and config['tmc_cols']:
            self.tmc = config['tmc']
            self.tmc_cols = ['Conflict']
        else:
            self.tmc_cols = None

        self.features = self.default_features + self.categorical_features \
            + self.continuous_features

    def get_feature_list(self, config):
        """
        Make the list of features, and write it to the city's data folder
        That way, we can avoid hardcoding the feature list in multiple places.
        If you add extra features, the only place you should need to add them
        is here
        Args:
            Config - the city's config file
        """

        # Features drawn from open street maps
        feat_types = {'f_cat': [], 'f_cont': [], 'default': []}

        # Run through the possible feature types
        for feat_type in ['openstreetmap_features',
                          'waze_features', 'additional_map_features']:
            if feat_type in config:
                if 'categorical' in config[feat_type]:
                    feat_types['f_cat'] += [x for x in config[
                        feat_type]['categorical'].keys()]
                if 'continuous' in config[feat_type]:
                    feat_types['f_cont'] += [x for x in config[
                        feat_type]['continuous'].keys()]

        # Add point-based features, in a different format because
        # each feature has its own file and accompanying details
        if 'data_source' in config and config['data_source']:
            for additional in config['data_source']:
                if 'feat_type' not in additional:
                    feat_types['default'].append(additional['name'])
                elif additional['feat_type'] == 'categorical':
                    feat_types['f_cat'].append(additional['name'])
                elif additional['feat_type'] == 'continuous':
                    feat_types['f_cont'].append(additional['name'])

        # May eventually want to rename this feature to be more general
        # For now, all atr features are continuous
        if 'atr_cols' in config and config['atr_cols']:
            feat_types['f_cont'] += config['atr_cols']

        return feat_types['default'], feat_types['f_cat'], feat_types['f_cont']


