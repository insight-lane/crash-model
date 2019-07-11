
import os
import shutil
import pipeline

TEST_FP = os.path.dirname(os.path.abspath(__file__))


def test_copy_files(tmpdir):

    base_dir = os.path.join(tmpdir, 'base')
    data_dir = os.path.join(tmpdir, 'data')
    print(TEST_FP)
    os.makedirs(base_dir)
    os.makedirs(os.path.join(base_dir, 'processed'))
    os.makedirs(data_dir)
    os.makedirs(os.path.join(data_dir, 'processed'))

    orig_file = os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'single_prediction_viz.geojson')
    print(orig_file)

    shutil.copy(
        os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'single_prediction_viz.geojson'),
        os.path.join(
            data_dir,
            'processed',
            'preds_viz.geojson'
        )
    )
    shutil.copy(
        os.path.join(
            TEST_FP,
            'data',
            'viz_preds_tests',
            'crashes_rollup.geojson'),
        os.path.join(
            data_dir,
            'processed',
            'crashes_rollup.geojson'
        )
    )
    config = {'name': 'cambridge'}
    pipeline.copy_files(
        base_dir,
        data_dir,
        config
    )
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'crashes_rollup.geojson'))
    assert os.path.exists(os.path.join(
        base_dir,
        'src',
        'showcase',
        'data',
        'cambridge',
        'preds_viz.geojson'))
