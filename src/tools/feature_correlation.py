import argparse
import os
import pandas as pd
from data.util import read_geojson


def get_correlation(datadir, outputfile, features):

    # Read in segments
    inter = read_geojson(os.path.join(
        datadir, 'processed', 'maps', 'inters_segments.geojson'))
    non_inter = read_geojson(os.path.join(
        datadir, 'processed', 'maps', 'non_inters_segments.geojson'))
    print("Read in {} intersection, {} non-intersection segments".format(
        len(inter), len(non_inter)))

    # Combine inter + non_inter
    combined_seg = inter + non_inter
    df = pd.DataFrame.from_dict([x[1] for x in combined_seg])
    df = df.fillna(0)
    df = df[features]

    pd.set_option('display.max_colwidth', -1)
    corr = df.corr()
    print(corr)
    corr.to_csv(outputfile, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="city's data directory",
                        required=True)
    parser.add_argument("-o", "--outputfile", type=str,
                        help="csv output file",
                        required=True)

    parser.add_argument("-features", "--featlist", nargs="+",
                        help="List of segment features to compare")
    args = parser.parse_args()

    get_correlation(args.datadir, args.outputfile, args.featlist)
