import json
import rtree
from geography import read_shp, find_nearest, parse_atrs
from geography import read_atrs, geocode_atrs

DATA_PATH = '../data'


if __name__ == '__main__':

    atr_address = parse_atrs()
    geocode_atrs(atr_address)
    # Read in segments
    inter = read_shp(DATA_PATH+'/processed/maps/inters_segments.shp')
    non_inter = read_shp(DATA_PATH+'/processed/maps/non_inters_segments.shp')
    print "Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter))

    # Combine inter + non_inter
    combined_seg = inter + non_inter

    # Create spatial index for quick lookup
    segments_index = rtree.index.Index()
    for idx, element in enumerate(combined_seg):
        segments_index.insert(idx, element[0].bounds)

    # Read in atr lats
    atrs = read_atrs()

    # Find nearest atr - 20 tolerance
    print "snapping atr to segments"
    find_nearest(atrs, combined_seg, segments_index, 20)
    with open(DATA_PATH+'/processed/snapped_atrs.json', 'w') as f:
        json.dump([x['properties'] for x in atrs], f)

