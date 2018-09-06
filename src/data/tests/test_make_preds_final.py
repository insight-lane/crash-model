import geojson
import os
import subprocess
import shutil
import pandas as pd
import filecmp
from .. import make_preds_final

def test_make_preds_final_boston(tmpdir):
    """
    Confirm that predictions & segments are combined as expected.
    """

    # load the test predictions & segments
    preds_test = pd.read_json(os.path.dirname(
        os.path.abspath(__file__)) + "/data/final_preds_tests/single_prediction.json", 
        orient="index", typ="series", dtype=False)
    
    segs_test = pd.read_json(os.path.dirname(
        os.path.abspath(__file__)) + "/data/final_preds_tests/single_segment.geojson")["features"]
    
    # combine the two
    preds_combined_test = make_preds_final.combine_predictions_and_segments(preds_test, segs_test)
    
    # write to file
    tmpdir_test_path = os.path.join(tmpdir.strpath, "preds_final.geojson")
    make_preds_final.write_preds_as_geojson(preds_combined_test, tmpdir_test_path)
    
    # compare the new file's contents to test data
    tmpdir_preds_final = pd.read_json(os.path.join(tmpdir.strpath, "preds_final.geojson"))
    preds_final_test = pd.read_json(os.path.dirname(os.path.abspath(__file__)) + "/data/final_preds_tests/single_prediction_final.geojson")
    
    assert (tmpdir_preds_final.equals( preds_final_test))
