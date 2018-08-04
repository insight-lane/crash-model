// update map when risk score filter changes
d3.select('#risk_slider').on("input", function() {

	// update week number displayed next to slider
	d3.select('#selected_risk').text(+this.value);
	d3.select('#risk_slider').property('value', +this.value);

	update_map(+this.value, map);
});

function update_map(riskThreshold, map) {
	//update data displayed on map based on week selected
	var new_filter = ['all', ['>=', 'prediction', riskThreshold]];

	map.setFilter('predictions', new_filter);
}
