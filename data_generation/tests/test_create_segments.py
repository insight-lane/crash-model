from ..make_segments import create_segments
import fiona
from shapely.geometry import Point, mapping
from fiona.crs import from_epsg


def test_reproject_and_read(tmpdir):
    make_shape_file(tmpdir)
    results = create_segments.reproject_and_read(
        tmpdir.strpath, tmpdir.strpath + '/outfile')

    assert results[0][0].coords
    reprojected = fiona.open(tmpdir.strpath + '/outfile')
    assert reprojected.crs == {'init': u'epsg:3857'}


def make_shape_file(tmpdir):
    tmppath = tmpdir.strpath

    schema = {
        'geometry': 'Point',
        'properties': {
            'id_1': 'int',
            'id_2': 'int'
        }
    }
    with fiona.open(tmppath, 'w', 'ESRI Shapefile', schema,
                    crs=from_epsg(3857)) as infile:
        infile.write({
            'geometry': mapping(Point(-71.08724754844711, 42.352043744961)),
            'properties': {'id_1': 1, 'id_2': 2}
        })

