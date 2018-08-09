
# coding: utf-8
# Generate canonical dataset for hackathon
# Developed by: bpben
import json
import pandas as pd
from data.util import read_geojson, group_json_by_location, group_json_by_field
import os
import argparse


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

MAP_FP = os.path.join(BASE_DIR, 'data/processed/maps')
DATA_FP = os.path.join(BASE_DIR, 'data/processed')


def read_records(fp, date_col, id_col, agg='week'):
    """ Read point data, output count by aggregation level
    agg : datepart for aggregation
    date_col : column name with date information
    id_col : column name with inter/non-inter id (for grouping)
    """

    with open(fp, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    df[date_col] = pd.to_datetime(df[date_col])
    print("total number of records in {}:{}".format(fp, len(df)))
    
    # get date according to iso calendar
    df['isodate'] = df[date_col].apply(lambda d: d.isocalendar())
    df['week'] = df['isodate'].apply(lambda x: x[1])
    df['year'] = df['isodate'].apply(lambda x: x[0])

    # aggregate
    print("aggregating by ", agg)
    df[agg] = df[date_col].apply(lambda x: getattr(x, agg))
    df_g = df.groupby([id_col, 'year', agg]).size()

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
    combined = pd.concat([inters_df, non_inters_df])

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
                         'dateOccurred', 'near_id')
    cr_con = pd.concat([crash], axis=1)
    cr_con.columns = ['crash']

    # if null for a certain week = 0 (no crash)
    cr_con.reset_index(inplace=True)
    cr_con = cr_con.fillna(0)
    # Make near_id string (for matching to segments)
    cr_con['near_id'] = cr_con['near_id'].astype('str')

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

    return aggregated, adjacent, cr_con


def group_by_date(cr_con, aggregated):
    # for each year, get iso week max, observation for each segment

    all_years = cr_con.year.unique()
    for y in all_years:
        # 2017 doesn't have full year, use last obs
        if y == 2017:
            yr_max = cr_con[cr_con.year==2017].week.max()
        else:
            yr_max = pd.Timestamp('12-31-{}'.format(y)).week
            # some years the last week = 1, make it 52 in that case
            if yr_max==1:
                yr_max = 52

        # We might have data that starts midyear
        yr_min = cr_con[cr_con.year == y].week.min()

        # if this is the first year
        # doing this because multiindex is hard to set up placeholder
        if y == all_years[0]:
            all_weeks = pd.MultiIndex.from_product(
                [aggregated.index, [y], list(range(yr_min, yr_max))],
                names=['segment_id', 'year', 'week'])
        else:
            yr_index = pd.MultiIndex.from_product(
                [aggregated.index, [y], list(range(yr_min, yr_max))],
                names=['segment_id', 'year', 'week'])
            all_weeks = all_weeks.union(yr_index)

    # crash/concern for each week, for each year for each segment
    cr_con = cr_con.set_index(
        ['near_id', 'year', 'week']).reindex(all_weeks, fill_value=0)

    cr_con.reset_index(inplace=True)

    # join segment features to crash/concern
    cr_con_roads = cr_con.merge(
        aggregated, left_on='segment_id', right_index=True, how='outer')

    return cr_con_roads


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

    aggregated, adjacent, cr_con = aggregate_roads(
        feats,
        DATA_FP,
        concerns=args.concern_info
    )

    # Need to rename?
    cr_con_roads = group_by_date(cr_con, aggregated)

    # output canon dataset
    print("exporting canonical dataset to ", DATA_FP)

    cr_con_roads.set_index('segment_id').to_csv(
        os.path.join(DATA_FP, 'vz_predict_dataset.csv.gz'),
        compression='gzip')

    # output adjacency info
    # need to include ATRs
    if os.path.exists(os.path.join(DATA_FP, 'snapped_atrs.json')):
        atrs = pd.read_json(os.path.join(DATA_FP, 'snapped_atrs.json'))
        adjacent = adjacent.reset_index()
        adjacent = adjacent.merge(
            atrs[['near_id', 'orig']],
            left_on='index',
            right_on='near_id',
            how='left'
        )
        adjacent.drop(['near_id'], axis=1, inplace=True)
        adjacent.columns = ['segment_id', 'orig_id', 'atr_address']
        adjacent.to_csv(os.path.join(
            DATA_FP, 'adjacency_info.csv'), index=False)
    else:
        print("No ATRs found, skipping...")
