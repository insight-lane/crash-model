from ..risk_map import process_data
import os
import geopandas as gpd

TEST_FP = os.path.dirname(os.path.abspath(__file__))

def test_process_data():
	streets = gpd.read_file(os.path.join(TEST_FP, 'data', 'single_segment.geojson'))
	streets_w_risk = process_data(streets, 
		os.path.join(TEST_FP, 'data', 'test_prediction.csv'),
		'prediction')
	assert streets_w_risk.shape[0] == 1
	assert streets_w_risk['prediction'].mean().round(2) == 0.12