
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

    def __init__(self, segment_id, lines, all_data, properties,
                 nodes=[], connected_segments=[]):
        self.id = segment_id
        self.lines = lines
        self.data = all_data
        self.properties = properties
        self.geometry = None
        # Nodes are the points (with openstreetmap node id) in the intersection
        self.nodes = nodes
        self.connected_segments = connected_segments


class IntersectionBuffer(object):
    """
    An intersection buffer consists of a polygon, and a list of
    records associated with the intersection points
    """
    def __init__(self, buffer, points):
        self.buffer = buffer
        self.points = points
