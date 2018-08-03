## helper functions for training/predicting
# Developed by: bpben
import pandas as pd

def format_crash_data(data, col, target_week, target_year):
    """ formats crash data for train/test 
    target_week: week to predict (make into binary target)
    target_year: year for predicted week
    note: data must be available for 4 months prior to target
    gets previous week count, previous month count, previous quarter count, avg per week
    """
    all_dates = data[['year','week']].drop_duplicates()
    all_dates.reset_index(drop=True, inplace=True)
    target_idx = all_dates[(all_dates.year==target_year)&(all_dates.week==target_week)].index.values[0]

    pre_week = tuple(all_dates.loc[target_idx-1].values)
    pre_month = all_dates.loc[list(range(target_idx-4, target_idx))].values
    pre_quarter = all_dates.loc[list(range(target_idx-12, target_idx))].values

    # format data to take in intervals defined above
    formatted_data = data.set_index(['segment_id','year','week'])[col].unstack(level=[1,2])
    week_data = pd.DataFrame(formatted_data[pre_week])
    week_data.columns = ['pre_week']
    week_data['pre_month'] = formatted_data[pre_month].max(axis=1)
    week_data['pre_quarter'] = formatted_data[pre_quarter].max(axis=1)
    week_data['avg_week'] = formatted_data[all_dates.loc[:target_idx-1].values].mean(axis=1)

    # binarize target
    week_data['target'] = (formatted_data[tuple(all_dates.loc[target_idx].values)]>0).astype(int)
    week_data = week_data.reset_index()

    return(week_data[['segment_id','target', 'pre_week',
                      'pre_month', 'pre_quarter', 'avg_week']])

def format_pred_data(model_data, pred_data):
    """ format in accordance with prediction data standard """
    