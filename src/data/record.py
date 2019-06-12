from . import util
from dateutil.parser import parse


class Record(object):
    "A record contains a dict of properties and a point in 4326 projection"

    def __init__(self, properties, point=None):
        if point:
            self.point = point
        else:
            self.point = util.get_reproject_point(
                properties['location']['latitude'],
                properties['location']['longitude'])
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

        # Skip vehicles for now
        self.properties['vehicles'] = ''

    @property
    def timestamp(self):
        return parse(self.properties['dateOccurred'])

