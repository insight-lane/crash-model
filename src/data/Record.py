class Record():
    "A record contains a dict of properties and a point in 4326 projection"

    def __init__(self, properties):
        self.point = self._get_reproject_point(properties['location'])
        self.properties = properties

        self.schema = {
            'geometry': 'Point',
            'properties': {
                'id': 'str',
                'near_id': 'str',
            }
        }

    @property
    def schema(self):
        return util.make_schema('Point', self.properties)

    @property
    def near_id(self):
        if 'near_id' in self.properties:
            return self.properties['near_id']
        return None

    def _get_reproject_point(self, location):
        """
        Turn a 4326 projection into 3857
        """
        lon, lat = pyproj.transform(
            pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:3857'),
            location['longitude'], location['latitude']
        )
        return Point(float(lon), float(lat))

#    @property
#    def shape_properties(self):
#        return self.
#        properties = {}
#        for attr, value in self.__dict__.iteritems():
#            if attr not in ('point', 'schema', 'timestamp'):
#                properties[attr] = str(value)
#        return properties


class Crash(Record):
    def __init__(self, properties):
        Record.__init__(self, properties)

    @property
    def timestamp(self):
        return parse(self.properties['dateOccurred'])


class Concern(Record):
    def __init__(self, properties):
        Record.__init__(self, properties)

        # Leaving these out pending ascii encoding on transformation side
        self.properties['category'] = ''
        self.properties['summary'] = ''

    @property
    def timestamp(self):
        return parse(self.properties['dateCreated'])

