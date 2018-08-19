import geojson
import os
import subprocess
import shutil
from .. import make_preds_final

def test_make_preds_final_boston(tmpdir):
    """
    Confirm that final predictions generated conform to the schema
    """
    
    # Copy test data into temp directory in appropriate place
    test_data_path = os.path.dirname(
        os.path.abspath(__file__)) + "/data/boston_final_preds"

    tmpdir_data_path = tmpdir.strpath + "/data"
    shutil.copytree(test_data_path, tmpdir_data_path)

    # Call make_preds_final
    subprocess.check_call([
        "python",
        "-m",
        "data.make_preds_final",
        "-f",
        tmpdir_data_path
    ])

    with open(tmpdir_data_path + "/processed/preds_final.json") as f:
        test_preds_final = geojson.load(f)

    # verify the predictions are valid geojson
    assert (test_preds_final.is_valid)
