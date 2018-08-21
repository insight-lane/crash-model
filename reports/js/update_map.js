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

d3.json("preds_final.json", function(data) {
	// console.log(data.features[0].properties);
	var segments = [];

	for (var segment in data.features) {
		segments.push(data.features[segment].properties);
	}

	segments.sort(function(a, b) {
		return d3.descending(a.prediction, b.prediction);
	})

	// console.log(segments);

	d3.select("#highest_risk_list")
		.selectAll("li")
		.data(segments.slice(0, 10))
		.enter()
		.append("li")
		.attr("class", "highRiskSegment")
		.text(function(d) { return d.segment_display_name; });
})