import os
import shutil
from shapely.geometry import Polygon
import networkx as nx
import json
import fiona
from .. import osm_create_maps
from .. import util
from .. import config
from ..record import transformer_4326_to_3857

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_get_width():
    assert osm_create_maps.get_width('15.2') == 15
    assert osm_create_maps.get_width('') == 0
    assert osm_create_maps.get_width("['14.9', '12.2']") == 0
    assert osm_create_maps.get_width('t') == 0


def test_get_speed():
    assert osm_create_maps.get_speed('') == 0
    assert osm_create_maps.get_speed('signals') == 0
    assert osm_create_maps.get_speed('60') == 60
    assert osm_create_maps.get_speed("['90', '100']") == 100


def test_reproject_and_clean_feats(tmpdir):

    tmppath = tmpdir.strpath
    shutil.copy(
        TEST_FP + '/data/processed/maps/osm_elements.geojson',
        tmppath
    )

    # For now, just make sure it runs
    osm_create_maps.clean_ways(
        tmppath + '/osm_elements.geojson',
        tmppath + '/docs'
    )


def test_expand_polygon():

    test_polygon = {
        'type': 'Polygon',
        'coordinates': [[[-71.0770265, 42.3364517], [-71.0810509, 42.3328703],
                         [-71.0721386, 42.3325241]]]
    }
    points_file = os.path.join(TEST_FP, 'data', 'osm_crash_file.json')

    # Too many points fall outside of the polygon to buffer
    result = osm_create_maps.expand_polygon(test_polygon, points_file)
    assert result is None

    polygon_coords = [util.get_reproject_point(
        x[1], x[0], transformer_4326_to_3857, coords=True
    ) for x in test_polygon['coordinates'][0]]
    orig_shape = Polygon(polygon_coords)

    result = osm_create_maps.expand_polygon(test_polygon, points_file,
                                            max_percent=.7)

    result_coords = [util.get_reproject_point(
        x[1], x[0], transformer_4326_to_3857, coords=True
    ) for x in result.exterior.coords]
    result_shape = Polygon(result_coords)

    # Check whether the new polygon has a larger area than the old one
    assert result_shape.area > orig_shape.area

    records = util.read_records(points_file, 'crash')

    # The first two points are outside the original shape
    # and the last point is within
    assert orig_shape.contains(records[0].point) is False
    assert orig_shape.contains(records[1].point) is False
    assert orig_shape.contains(records[2].point)

    # The first point should be within the new shape, but not the
    # second point, since it was too far from the original shape
    assert result_shape.contains(records[0].point)
    assert result_shape.contains(records[1].point) is False
    assert result_shape.contains(records[2].point)


def mockreturn(config):
    G1 = nx.read_gpickle(os.path.join(TEST_FP, 'data', 'osm_output.gpickle'))
    return G1


def test_simple_get_roads(tmpdir, monkeypatch):

    monkeypatch.setattr(osm_create_maps, 'get_graph', mockreturn)
    c = config.Configuration(
        os.path.join(TEST_FP, 'data', 'config_features.yml'))
    osm_create_maps.simple_get_roads(c, tmpdir)

    with open(os.path.join(tmpdir, 'features.geojson')) as f:
        data = json.load(f)
    signals = [x for x in data['features']
               if x['properties']['feature'] == 'signal']
    assert len(signals) == 2
    intersections = [x for x in data['features']
                     if x['properties']['feature'] == 'intersection']
    assert len(intersections) == 14
    crosswalks = [x for x in data['features']
                  if x['properties']['feature'] == 'crosswalk']
    assert len(crosswalks) == 9

    nodes = fiona.open(os.path.join(tmpdir, 'osm_nodes.shp'))
    ways = fiona.open(os.path.join(tmpdir, 'osm_ways.shp'))

    # It's just coincidence that the number of ways and nodes is the same
    assert len(nodes) == 28
    assert len(ways) == 28
