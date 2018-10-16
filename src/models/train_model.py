# Training code for D4D Boston Crash Model project
# Developed by: bpben

import numpy as np
import pandas as pd
import scipy.stats as ss
from sklearn.metrics import roc_auc_score
import os
import argparse
import yaml
from .model_utils import format_crash_data
from .model_classes import Indata, Tuner, Tester
import sklearn.linear_model as skl

# all model outputs must be stored in the "data/processed/" directory
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

def predict_forward(split_week, split_year, seg_data, crash_data):
    """simple function to predict crashes for specific week/year"""
    test_crash = format_crash_data(crash_data, 'crash', split_week, split_year)
    test_crash_segs = test_crash.merge(seg_data, left_on='segment_id', right_on='segment_id')
    preds = trained_model.predict_proba(test_crash_segs[best_model_features])[::,1]
    try: 
        perf = roc_auc_score(test_crash_segs['target'], preds)
    except ValueError:
        print('Only one class present, likely no crashes in the week')
        perf = 0
    print(('Week {0}, year {1}, perf {2}'.format(split_week, split_year, perf)))
    if perf<=perf_cutoff:
        print(('Model performs below AUC %s, may not be usable' % perf_cutoff))
    return(preds)

#Model parameters
params = dict()

#cv parameters
cvp = dict()
cvp['pmetric'] = 'roc_auc'
cvp['iter'] = 5 #number of iterations
cvp['folds'] = 5 #folds for cv (default)
cvp['shuffle'] = True

#LR parameters
mp = dict()
mp['LogisticRegression'] = dict()
mp['LogisticRegression']['penalty'] = ['l1','l2']
mp['LogisticRegression']['C'] = ss.beta(a=5,b=2) #beta distribution for selecting reg strength
mp['LogisticRegression']['class_weight'] = ['balanced']

#xgBoost model parameters
mp['XGBClassifier'] = dict()
mp['XGBClassifier']['max_depth'] = list(range(3, 7))
mp['XGBClassifier']['min_child_weight'] = list(range(1, 5))
mp['XGBClassifier']['learning_rate'] = ss.beta(a=2,b=15)

# cut-off for model performance
# generally, if the model isn't better than chance, it's not worth reporting
perf_cutoff = 0.5

def set_defaults(config={}):
    """
    Sets defaults if not given in the config file.
    Default is just to use the open street map features and crash file
    args:
        config - dict
    """
    if 'seg_data' not in list(config.keys()):
        config['seg_data'] = 'vz_predict_dataset.csv.gz'
    if 'concern' not in list(config.keys()):
        config['concern'] = ''
    if 'atr' not in list(config.keys()):
        config['atr'] = ''
    if 'tmc' not in list(config.keys()):
        config['tmc'] = ''
    if 'f_cont' not in list(config.keys()):
        config['f_cont'] = ['width']
    if 'f_cat' not in list(config.keys()):
        config['f_cat'] = ['lanes', 'hwy_type', 'osm_speed', 'oneway',
                           'signal']

    # Add features for additional data sources
    if 'data_source' in config and config['data_source']:
        for source in config['data_source']:
            config[source['feat']].append(source['name'])

    if 'process' not in list(config.keys()):
        config['process'] = True
    if 'time_target' not in list(config.keys()):
        config['time_target'] = [15, 2017]
    if 'weeks_back' not in list(config.keys()):
        config['weeks_back'] = 1
    if 'name' not in list(config.keys()):
        config['name'] = 'boston'
    if 'level' not in list(config.keys()):
        config['level']  = 'week'


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # parse arguments
    parser.add_argument("-c", "--config", type=str,
                        help="yml file for model config, default is a " + 
                        "base config with open street map data and crashes only"
    )
    parser.add_argument('-d', '--datadir', type=str,
                        help="data directory")

    args = parser.parse_args()

    config = {}
    if args.config:
        config_file = args.config
        with open(config_file) as f:
            config = yaml.safe_load(f)
    set_defaults(config)

    DATA_FP = os.path.join(BASE_DIR, 'data', config['name'], 'processed/')
    print(('Outputting to: %s' % DATA_FP))

    # Default
    seg_data = os.path.join(DATA_FP, 'vz_predict_dataset.csv.gz')
    # Override default if given
    if config['seg_data'] is not None:
        seg_data = os.path.join(DATA_FP, config['seg_data'])

    # Default
    atr_data = os.path.join(DATA_FP, 'atrs_predicted.csv')
    # Override default if given
    if config['atr'] == '':
        atr_data = ''
    elif config['atr'] is not None:
        atr_data = config['atr']

    # Default
    tmc_data = os.path.join(DATA_FP, 'tmc_summary.json')
    # Override default if given
    if config['tmc'] == '':
        tmc_data = ''
    elif config['tmc'] is not None:
        tmc_data = config['tmc']

    week = int(config['time_target'][0])
    year = int(config['time_target'][1])
    f_cat = config['f_cat']
    f_cont = config['f_cont']

    # Read in data
    data = pd.read_csv(seg_data, dtype={'segment_id':'str'})
    data.sort_values(['segment_id', 'year', 'week'], inplace=True)
    if config['level'] == 'week':
        # get segments with non-zero crashes
        # this is necessary to constrain the problem for weekly predictions
        data = data.set_index('segment_id').loc[data.groupby('segment_id').crash.sum()>0]
        data.reset_index(inplace=True)

    # segment chars
    # Dropping continuous features that don't exist
    new_feats = []
    for f in f_cont:
        if f not in data.columns.values:
            print("Feature " + f + " not found, skipping")
        else:
            new_feats.append(f)
    f_cont = new_feats

    data_segs = data.groupby('segment_id')[f_cont+f_cat].max()  # grab the highest values from each column
    data_segs.reset_index(inplace=True)

    # create featureset holder
    features = f_cont+f_cat
    print(('Segment features included: {}'.format(features)))

    # add concern
    if config['concern']!='':
        print('Adding concerns')
        concern_observed = data[data.year==2016].groupby('segment_id')[config['concern']].max()
        features.append(config['concern'])
        data_segs = data_segs.merge(concern_observed.reset_index(), on='segment_id')

    # add in atrs if filepath present
    if config['atr']!='':
        print('Adding atrs')
        atrs = pd.read_csv(DATA_FP+config['atr'], dtype={'id':'str'})
        # for some reason pandas reads the id as float before str conversions
        atrs['id'] = atrs.id.apply(lambda x: x.split('.')[0])
        data_segs = data_segs.merge(atrs[['id']+config['atr_cols']],
                                                                left_on='segment_id', right_on='id')
        features += config['atr_cols']

    # add in tmcs if filepath present
    if config['tmc']!='':
        print('Adding tmcs')
        tmcs = pd.read_json(DATA_FP+config['tmc'],
                                           dtype={'near_id':str})[['near_id']+config['tmc_cols']]
        data_segs = data_segs.merge(tmcs, left_on='segment_id', right_on='near_id', how='left')
        data_segs[config['tmc_cols']] = data_segs[config['tmc_cols']].fillna(0)
        features += config['tmc_cols']

    # features for linear model
    lm_features = features

    # add crash data
    # create lagged crash values
    crash_lags = format_crash_data(data, 'crash', week, year)

    # add to features
    crash_cols = ['pre_week','pre_month','pre_quarter','avg_week']
    features += crash_cols

    if config['process']:
        print(('Processing categorical: {}'.format(f_cat)))
        for f in f_cat:
            t = pd.get_dummies(data_segs[f])
            t.columns = [f+str(c) for c in t.columns]
            data_segs = pd.concat([data_segs, t], axis=1)
            features += t.columns.tolist()
            # for linear model, allow for intercept
            lm_features += t.columns.tolist()[1:]
        # aadt - log-transform
        print(('Processing continuous: {}'.format(f_cont)))
        for f in f_cont:
            data_segs['log_%s' % f] = np.log(data_segs[f]+1)
            features += ['log_%s' % f]
            lm_features += ['log_%s' % f]
        # add segment type
        data_segs['intersection'] = data_segs.segment_id.map(lambda x: x[:2]!='00').astype(int)
        features += ['intersection']
        lm_features += ['intersection']

        # remove duplicated features
        features = list(set(features) - set(f_cat+f_cont))
        lm_features = list(set(lm_features) - set(f_cat+f_cont))

    # create model data
    data_model = crash_lags.merge(data_segs, left_on='segment_id', right_on='segment_id')
    print("full features:{}".format(features))

    #Initialize data
    df = Indata(data_model, 'target')
    #Create train/test split
    df.tr_te_split(.7)

    #Parameters for model
    # class weight
    # this needs to adapt to the model data, so can't be specified up from
    a = data_model['target'].value_counts(normalize=True)
    w = 1/a[1]
    mp['XGBClassifier']['scale_pos_weight'] = [w]

    #Initialize tuner
    tune = Tuner(df)
    try: 
        #Base XG model
        tune.tune('XG_base', 'XGBClassifier', features, cvp, mp['XGBClassifier'])
        #Base LR model
        tune.tune('LR_base', 'LogisticRegression', lm_features, cvp, mp['LogisticRegression'])
    except ValueError:
        print('CV fails, likely very few of target available, try rerunning at segment-level')
        raise
    # Run test
    test = Tester(df)
    test.init_tuned(tune)
    test.run_tuned('LR_base', cal=False)
    test.run_tuned('XG_base', cal=False)

    # choose best performing model
    best_perf = 0
    best_model = None
    for m in test.rundict:
        if test.rundict[m]['roc_auc']>best_perf:
            best_perf = test.rundict[m]['roc_auc']
            best_model = test.rundict[m]['model']
            best_model_features = test.rundict[m]['features']
    # check for performance above certain level
    if best_perf<=perf_cutoff:
        print(('Model performs below AUC %s, may not be usable' % perf_cutoff))

    # train on full data
    trained_model = best_model.fit(data_model[best_model_features], data_model['target'])

    # running this to test performance at different weeks
    tuned_model = skl.LogisticRegression(**test.rundict['LR_base']['bp'])

    # predict back number of weeks according to config
    all_weeks = data[['year','week']].drop_duplicates().sort_values(['year','week']).values
    back_weeks = all_weeks[-config['weeks_back']:]
    pred_weeks = np.zeros([back_weeks.shape[0], data_segs.shape[0]])
    for i, yw in enumerate(back_weeks):
        preds = predict_forward(yw[1], yw[0], data_segs, data)
        pred_weeks[i] = preds

    # create dataframe with segment-year-week index
    df_pred = pd.DataFrame(pred_weeks.T,
            index=data_segs.segment_id.values,
            columns=pd.MultiIndex.from_tuples([tuple(w) for w in back_weeks]))
    # has year-week column index, need to stack for year-week index
    df_pred = df_pred.stack(level=[0,1])
    df_pred = df_pred.reset_index()
    df_pred.columns = ['segment_id', 'year', 'week', 'prediction']
    df_pred.to_csv(os.path.join(DATA_FP, 'seg_with_predicted.csv'), index=False)

    # output for manipulation by 
    data_plus_pred = df_pred.merge(data_model, on=['segment_id'])
    data_plus_pred.to_json(os.path.join(DATA_FP, 'seg_with_predicted.json'), orient='index')


