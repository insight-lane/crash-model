## helper functions for training/predicting
# Developed by: bpben

def format_crash_data(data, col, target_week, target_year):
    """ formats crash data for train/test 
    target_week: week to predict (make into binary target)
    target_year: year for predicted week
    note: data must be available for 4 months prior to target
    gets previous week count, previous month count, previous quarter count, avg per week
    """
    sliced = data.loc[(slice(None),slice(None,target_year), slice(1, target_week)),:]

    assert target_week>16
    pre_week = target_week - 1
    pre_month = range(pre_week-4, target_week)
    pre_quarter = range(pre_month[0]-12, target_week)
    
    # week interval for each segment
    # full range = pre_quarter : target
    sliced = data.loc[(slice(None),slice(target_year,target_year), slice(1, target_week)),:]
    week_data = sliced[col].unstack(2)
    week_data.reset_index(level=1, inplace=True)
    
    # aggregate
    week_data['pre_month'] = week_data[pre_month].sum(axis=1)
    week_data['pre_quarter'] = week_data[pre_quarter].sum(axis=1)
    week_data['pre_week'] = week_data[pre_week]

    # avg as of target week
    except_target = data.loc[(slice(None),
                       slice(target_year,target_year),
                       slice(target_week,None)),:].index
    avg_week = data.drop(except_target)
    avg_week = avg_week.reset_index().groupby('segment_id')[col].mean()
    avg_week.name = 'avg_week'
    # join to week data
    week_data = week_data.join(avg_week)

    # binarize target
    week_data['target'] = (week_data[target_week]>0).astype(int)
    week_data = week_data.reset_index()

    return(week_data[['segment_id','target', 'pre_week',
                      'pre_month', 'pre_quarter', 'avg_week']])