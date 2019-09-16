# Training code for D4D Boston Crash Model project
# Developed by: bpben

import numpy as np
import pandas as pd
import scipy.stats as ss
import os
import json
import argparse
from .model_classes import Indata, Tuner, Tester
import data.config

# all model outputs must be stored in the "data/processed/" directory
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))


def output_importance(trained_model, features, datadir, target):
    # output feature importances or coefficients
    if hasattr(trained_model, 'feature_importances_'):
        feature_imp_dict = dict(zip(features, trained_model.feature_importances_.astype(float)))
    elif hasattr(trained_model, 'coefficients'):
        feature_imp_dict = dict(zip(features, trained_model.coefficients.astype(float)))
    else:
        return("No feature importances/coefficients detected")

    # conversion to json
    if target=='crash':
        with open(os.path.join(datadir, 'feature_importances.json'), 'w') as f:
            json.dump(feature_imp_dict, f)
    else:
        with open(
            os.path.join(
                datadir, 'feature_importances_%s.json' % target), 'w') as f:
            json.dump(feature_imp_dict, f)

def set_params():

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
    mp['LogisticRegression']['solver'] = ['liblinear']

    #xgBoost model parameters
    mp['XGBClassifier'] = dict()
    mp['XGBClassifier']['max_depth'] = list(range(3, 7))
    mp['XGBClassifier']['min_child_weight'] = list(range(1, 5))
    mp['XGBClassifier']['learning_rate'] = ss.beta(a=2,b=15)

    # cut-off for model performance
    # generally, if the model isn't better than chance, it's not worth reporting
    perf_cutoff = 0.5
    return cvp, mp, perf_cutoff


def set_defaults(config):
    """
    Sets defaults if not given in the config file.
    args:
        config object
    """
    if not hasattr(config, 'seg_data'):
        config.seg_data = 'vz_predict_dataset.csv.gz'

        
def get_features(config, data):
    """
    Get features from the feature list created during data generation
    """

    features = config.features

    # segment chars
    # Dropping continuous features that don't exist
    new_feats_cont = []
    new_feats_cat = []
    new_feats_default = []

    for f in config.continuous_features:
        if f not in data.columns.values:
            print("Feature " + f + " not found, skipping")
        else:
            new_feats_cont.append(f)
    f_cont = new_feats_cont

    for f in config.categorical_features:
        if f not in data.columns.values:
            print("Feature " + f + " not found, skipping")
        else:
            new_feats_cat.append(f)
            
    f_cat = new_feats_cat
    for f in config.default_features:
        if f not in data.columns.values:
            print("Feature " + f + " not found, skipping")
        else:
            new_feats_default.append(f)
    f_default = new_feats_default

    # create featureset holder
    features = f_cont + f_cat + f_default

    print(('Segment features included: {}'.format(features)))
    if config.tmc_cols:
        features += config.tmc_cols

    return f_cat, f_cont, features


def predict(trained_model, data_model, best_model_features,
            features, target, datadir):
    """

    Args:

    Returns
        nothing, writes prediction segments to file
    """

    preds = trained_model.predict_proba(data_model[features])[::, 1]
    df_pred = data_model.copy(deep=True)
    df_pred['prediction'] = preds
    if target == 'crash':
        fn = 'seg_with_predicted'
    else:
        fn = 'seg_with_predicted_%s' % target
        # For each resulting seg_with_predicted dataset, whether or not
        # there was a crash is given in the 'crash' column
        df_pred = df_pred.rename(columns={target: 'crash'})

    df_pred.to_csv(os.path.join(datadir, fn+'.csv'), index=False)
    df_pred.to_json(os.path.join(datadir, fn+'.json'), orient='index')


def add_extra_features(data_segs, config, datadir):
    """
    Add concerns, atrs and tmcs
    Args:
        data_segs
        config
    Returns:
        updated data_segs
    """

    # add in tmcs if filepath present
    if config.tmc_cols:
        print('Adding tmcs')
        tmcs = pd.read_json(datadir+config.tmc, dtype={'near_id': str})[
            ['near_id'] + config.tmc_cols]
        data_segs = data_segs.merge(
            tmcs, left_on='segment_id', right_on='near_id', how='left')
        data_segs[config.tmc_cols] = data_segs[config.tmc_cols].fillna(0)

    return data_segs


def process_features(features, f_cat, f_cont, data_segs):
    # features for linear model
    lm_features = features

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

    return data_segs, features, lm_features


def initialize_and_run(data_model, features, lm_features, target,
                       datadir, seed=None):

    cvp, mp, perf_cutoff = set_params()

    # Initialize data
    df = Indata(data_model, target)
    # Create train/test split
    df.tr_te_split(.7, seed=seed)

    # Parameters for model
    # class weight
    # this needs to adapt to the model data, so can't be specified up from
    a = data_model[target].value_counts(normalize=True)
    w = 1/a[1]
    mp['XGBClassifier']['scale_pos_weight'] = [w]

    # Initialize tuner
    tune = Tuner(df)
    try: 
        # Base XG model
        tune.tune('XG_base', 'XGBClassifier', features, cvp, mp['XGBClassifier'])
        # Base LR model
        tune.tune('LR_base', 'LogisticRegression', lm_features, cvp, mp['LogisticRegression'])
    except ValueError:
        print('CV fails, likely very few of target available')
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
        if test.rundict[m]['roc_auc'] > best_perf:
            best_perf = test.rundict[m]['roc_auc']
            best_model = test.rundict[m]['model']
            best_model_features = test.rundict[m]['features']
    # check for performance above certain level
    if best_perf <= perf_cutoff:
        print(('Model performs below AUC %s, may not be usable' % perf_cutoff))

    # train on full data
    trained_model = best_model.fit(data_model[best_model_features], data_model[target])

    predict(trained_model, data_model, best_model_features,
            features, target, datadir)

    # output feature importances or coefficients

    output_importance(trained_model, features, datadir, target)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # parse arguments
    parser.add_argument("-c", "--config", type=str,
                        help="yml file for model config"
    )
    parser.add_argument('-d', '--datadir', type=str,
                        help="data directory")

    args = parser.parse_args()
    config = data.config.Configuration(args.config)
    set_defaults(config)

    DATA_FP = os.path.join(BASE_DIR, 'data', config.name)
    PROCESSED_DATA_FP = os.path.join(BASE_DIR, 'data', config.name, 'processed/')
    seg_data = os.path.join(PROCESSED_DATA_FP, config.seg_data)

    # get the targets
    if config.split_columns!=[]:
        targets = config.split_columns
    else:
        targets = ['crash']

    print(('Outputting to: %s' % PROCESSED_DATA_FP))

    # Read in data
    data = pd.read_csv(seg_data, dtype={'segment_id': 'str'})

    f_cat, f_cont, features = get_features(config, data)

    data = add_extra_features(data, config, PROCESSED_DATA_FP)
    # grab the highest values from each column
    data_segs = data.groupby('segment_id')[features].max()
    data_segs.reset_index(inplace=True)

    data_segs, features, lm_features = process_features(
        features, f_cat, f_cont, data_segs)
    print("full features:{}".format(features))

    for target in targets:
        # want any instance of target
        any_target = data.groupby('segment_id')[target].max()
        any_target = (any_target>0).astype(int)
        any_target.name = target
        data_model = data_segs.set_index('segment_id').join(any_target).reset_index()    
        print("running model for target: %s" % target )
        initialize_and_run(data_model, features, lm_features, target,
                           PROCESSED_DATA_FP)


