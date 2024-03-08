
class Segment(object):
    "A segment contains a dict of properties and a shapely shape"

    def __init__(self, geometry, properties):
        
        self.geometry = geometry
        self.properties = properties
        

class Intersection(object):
    """
    Creates an Intersection object
    Args:
        count (int): Unique identifier for the intersection.
        lines (list of shapely.geometry.linestring): List of lines forming the intersection.
        properties (list of dict): List of dictionaries containing properties for each line.
        data (dict, optional): Additional data associated with the intersection. Defaults to an empty dictionary.
        nodes (list of dict, optional): List of dictionaries containing information about nodes in the intersection. Defaults to an empty list.
        connected_segments (list of int, optional): List of IDs of segments connected to the intersection. Defaults to an empty list.

    """

    def __init__(self, segment_id, lines, data, properties,
                 nodes=[], connected_segments=[]):
        self.id = segment_id
        self.lines = lines
        self.data = data
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
