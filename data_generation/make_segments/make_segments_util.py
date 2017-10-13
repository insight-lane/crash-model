import fiona
from shapely.geometry import Point, shape, mapping


def write_shp(schema, fp, data, shape_key, prop_key):
    """ Write Shapefile
    schema : schema dictionary
    shape_key : column name or tuple index of Shapely shape
    prop_key : column name or tuple index of properties
    """
    with fiona.open(fp, 'w', 'ESRI Shapefile', schema) as c:
        for i in data:
            c.write({
                'geometry': mapping(i[shape_key]),
                'properties': i[prop_key],
            })

