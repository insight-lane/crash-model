var segments = [];
var segmentsHash;

d3.json("preds_final.json", function(data) {

	for (var segment in data.features) {
		segments.push(data.features[segment].properties);
	}

	segments.sort(function(a, b) {
		return d3.descending(a.prediction, b.prediction);
	})

	segmentsHash = d3.map(segments.slice(10), function(d) { return d.segment_id; });

	d3.select("#highest_risk_list")
		.selectAll("li")
		.data(segments.slice(0, 10))
		.enter()
		.append("li")
		.attr("class", "highRiskSegment")
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

function populateSegmentInfo(segmentID) {
	var segmentData = segmentsHash.get(segmentID);

	d3.select('#segment_details .segment_name')
		.html(function() { if(segmentData.segment.display_name.indexOf("between") > -1)
							{ var nameObj = splitSegmentName(segmentData.segment.display_name);
							  return nameObj["name"] + "<br><span class='between'>" + nameObj["between"] + "</span>"; }
							else {
								return segmentData.segment.display_name;
							}
		});
	d3.select('#segment_details #prediction').text(segmentData.prediction);
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
