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
		// .text(function(d) { return d.segment.display_name; });
		.html(function(d) { if(d.segment.display_name.indexOf("between") > -1)
								{ var nameObj = splitSegmentName(d.segment.display_name);
								  return nameObj["name"] + "<br><span class='between'>" + nameObj["between"] + "</span>"; }
							else {
									return d.segment.display_name;
								}
		});
})

function splitSegmentName(segmentName) {
	var i = segmentName.indexOf("between");
	return {name: segmentName.slice(0, i), between: segmentName.slice(i,)};
}

///////////////////////// UPDATE MAP ///////////////////////////////////////////////////////
// event handlers to update map when filters change
d3.select('#risk_slider').on("input", function() {

	// update values displayed next to slider
	d3.select('#selected_risk').text(+this.value);

	update_map(map);
});

d3.select('#speed_slider').on("input", function() {

	// update values displayed next to slider
	d3.select('#selected_speed').text(this.value + "mph");

	update_map(map);
});

function update_map(map) {
	filters = getFilterValues();
	var new_filter = ['all', ['>=', 'prediction', +filters['riskThreshold']], ['>=', 'SPEEDLIMIT', +filters['speedlimit']]];

	map.setFilter('predictions', new_filter);
}

// get current filter values
function getFilterValues() {
	var filterValues = {};

	filterValues['riskThreshold'] = d3.select('#risk_slider').property('value');
	filterValues['speedlimit'] = d3.select('#speed_slider').property('value');

	return filterValues;
}
