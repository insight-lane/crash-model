
class Segment(object):
    "A segment contains a dict of properties and a shapely shape"

    def __init__(self, geometry, properties):
        
        self.geometry = geometry
        self.properties = properties
        

class Intersection(object):
    """
    lines is a list of all the component lines
    properties is a list of dicts of component properties rather than a dict
    """

    def __init__(self, segment_id, lines, properties):
        self.id = segment_id
        self.lines = lines

        self.properties = properties
        self.display_name = ''
        self.center_x = None
        self.center_y = None
        self.geometry = None


class IntersectionBuffer(object):
    """
    An intersection buffer consists of a polygon, and a list of
    records associated with the intersection points
    """
    def __init__(self, buffer, points):
        self.buffer = buffer
        self.points = points
