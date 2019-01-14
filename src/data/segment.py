from shapely.geometry import MultiLineString


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
        coords = []
        for line in lines:
            coords += [[x for x in line.coords]]

        self.geometry = MultiLineString(coords)

        self.properties = properties
        self.display_name = ''
        self.center_x = None
        self.center_y = None

        
