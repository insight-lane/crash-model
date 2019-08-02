from pyproj import Transformer
from . import util
from dateutil.parser import parse

# transformer object between 4326 projection and 3857 projection
transformer_4326_to_3857 = Transformer.from_proj(
    4326, 3857, always_xy=True)
# transformer object between 3857 projection and 4326 projection
transformer_3857_to_4326 = Transformer.from_proj(
    3857, 4326, always_xy=True)


class Record(object):
    "A record contains a dict of properties and a point in 4326 projection"

    def __init__(self, properties, point=None):
        if point:
            self.point = point
        else:
            self.point = util.get_reproject_point(
                properties['location']['latitude'],
                properties['location']['longitude'],
                transformer_4326_to_3857)
        self.properties = properties

    @property
    def schema(self):
        return util.make_schema('Point', self.properties)

    def _get_near_id(self):
        if 'near_id' in self.properties:
            return self.properties['near_id']
        return None

    def _set_near_id(self, near_id):
        self.properties['near_id'] = near_id
    
    near_id = property(_get_near_id, _set_near_id)

    @property
    def timestamp(self):
        if 'timestamp' in self.properties:
            return self.properties['timestamp']
        else:
            return ''


class Crash(Record):
    def __init__(self, properties):
        Record.__init__(self, properties)

    @property
    def timestamp(self):
        return parse(self.properties['dateOccurred'])

