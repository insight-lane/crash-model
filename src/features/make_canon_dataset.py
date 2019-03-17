
# coding: utf-8
# Generate canonical dataset for hackathon
# Developed by: bpben
import json
import pandas as pd
from data.util import read_geojson, group_json_by_location, group_json_by_field
import os
import argparse
import warnings

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def read_records(fp, id_col):
    """
    Read point data, output segments with crash counts
    Args:
        fp - file, probably a crash_joined.json file
        id_col - column that corresponds to segment id, probably near_id
    Returns:
        Pandas dataframe with the segment/crash info
    """

    with open(fp, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    print("total number of records in {}:{}".format(fp, len(df)))
    
    df_g = df.groupby([id_col]).size()
    return(df_g)


def road_make(feats, inters_fp, non_inters_fp, agg='max'):
    """ Makes road feature df, intersections + non-intersections

    agg : aggregation type (default is max)
    IMPORTANT: if the aggregation type changes, need to also update
        how aggregation is calculated in src/data/add_map.py
    """

    # Read in inters data (json), turn into df with inter index
    df_index = []
    df_records = []
    print("reading ", inters_fp)
    with open(inters_fp, 'r') as f:
        inters = json.load(f)
        # Append each index to dataframe
        for idx, lines in inters.items():

            # Each intersection has more than one segment
            # Add each segment's properties to df_records
            df_records.extend(lines)
            df_index.extend([idx] * len(lines))
    inters_df = pd.DataFrame(df_records, index=df_index)

    # Read in non_inters data:
    print("reading ", non_inters_fp)
    non_inters = read_geojson(non_inters_fp)
    non_inters_df = pd.DataFrame([x[1] for x in non_inters])
    non_inters_df.set_index('id', inplace=True)

    # Combine inter + non_inter
    combined = pd.concat([inters_df, non_inters_df], sort=True)
    missing_feats = [x for x in feats if x not in combined.columns]
    feats = [x for x in feats if x in combined.columns]
    if missing_feats:
        warnings.warn(
            str(len(missing_feats))
            + " feature(s) missing, skipping (" +
            ', '.join(missing_feats)
            + ")")
    # Since there are multiple segments per intersection,
    # aggregating inters data = apply aggregation (default is max)
    aggregated = getattr(combined[feats].groupby(combined.index), agg)

    # return aggregation and adjacency info (orig_id)
    return(aggregated(), combined['orig_id'])


def read_concerns(fp, id_col):
    """
    Turns a json file of spatial only features into a pandas dataframe
    """

    items = json.load(open(fp))
    grouped_by_source = group_json_by_field(items, 'source')

    data_frames = []
    for source, items in grouped_by_source.items():
        results, grouped = group_json_by_location(items)
        segments = [k for k in list(grouped.keys()) if k]
        results = {source: [grouped[k]['count'] for k in segments]}
        df = pd.DataFrame(results, index=segments)
        data_frames.append((source, df))
    return data_frames


def aggregate_roads(feats, datadir, concerns=[]):

    # read/aggregate crash/concerns
    crash = read_records(os.path.join(datadir, 'crash_joined.json'),
                         'near_id')
    crash_concern = pd.concat([crash], axis=1)
    crash_concern.columns = ['crash']

    # if null for a certain week = 0 (no crash)
    crash_concern.reset_index(inplace=True)

    crash_concern = crash_concern.fillna(0)
    # Make near_id string (for matching to segments)
    crash_concern['near_id'] = crash_concern['near_id'].astype('str')

    # combined road feature dataset parameters
    inters_fp = os.path.join(datadir, 'inters_data.json')
    non_inters_fp = os.path.join(datadir, 'maps', 'non_inters_segments.geojson')

    # create combined road feature dataset
    aggregated, adjacent = road_make(feats, inters_fp, non_inters_fp)
    print("road features being included: ", ', '.join(feats))

    # Add any concern types if applicable
    filename = os.path.join(datadir, 'concern_joined.json')
    if os.path.exists(filename):

        concerns = read_concerns(
            filename, 'near_id'
        )
        for concern_type, result in concerns:

            f = {concern_type: result}
            aggregated = aggregated.assign(**f)
            aggregated = aggregated.fillna(0)
    else:
        aggregated = aggregated.fillna(0)

    # All features as int
    aggregated = aggregated.apply(lambda x: x.astype('int'))

    return aggregated, adjacent, crash_concern


def combine_crash_with_segments(crash_concern, aggregated):

    # join segment features to crash/concern
    crash_concern_roads = pd.merge(
        aggregated, crash_concern,
        left_index=True,
        right_on='near_id', right_index=False,
        how='outer'
    )
    crash_concern_roads = crash_concern_roads.rename(
        columns={'near_id': 'segment_id'})
    return crash_concern_roads


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datadir", type=str,
                        help="Can give alternate data directory")
    parser.add_argument("-features", "--featlist", nargs="+", default=[
        'AADT', 'SPEEDLIMIT', 'Struct_Cnd', 'Surface_Tp', 'F_F_Class'],
        help="List of segment features to include")
    parser.add_argument('-concerns', '--concern_info', nargs="+",
                        help="A list of comma separated concern info, " +
                        "containing filename, latitude, longitude and " +
                        "time columns",
                        default=['concern,Vision_Zero_Entry.csv,,,'])

    args = parser.parse_args()

    # Can override the hardcoded data directory
    if args.datadir:
        DATA_FP = os.path.join(args.datadir, 'processed')
        MAP_FP = os.path.join(DATA_FP, 'maps')

    # Can override the hardcoded feature list
    feats = ['AADT', 'SPEEDLIMIT',
             'Struct_Cnd', 'Surface_Tp',
             'F_F_Class']
    if args.featlist:
        feats = args.featlist

    print("Data directory: " + DATA_FP)

    aggregated, adjacent, crash_concern = aggregate_roads(
        feats,
        DATA_FP,
        concerns=args.concern_info
    )

    crash_concern_roads = combine_crash_with_segments(
        crash_concern, aggregated)

    # output canon dataset
    print("exporting canonical dataset to ", DATA_FP)

    crash_concern_roads.set_index('segment_id').to_csv(
        os.path.join(DATA_FP, 'vz_predict_dataset.csv.gz'),
        compression='gzip')

