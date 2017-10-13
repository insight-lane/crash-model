from shapely.geometry import Point, shape, mapping
import fiona


def read_shp(fp):
    """ Read shp, output tuple geometry + property """
    out = [(shape(line['geometry']), line['properties'])
           for line in fiona.open(fp)]
    return(out)
