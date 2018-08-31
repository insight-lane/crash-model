var DECIMALFMT = d3.format(".2f");

var segments = [];
var segmentsHash;

var xScale = d3.scaleLinear().domain([0, 1]);
var riskColor = d3.scaleLinear()
	.domain([0.2, 0.4, 0.6, 0.8])
	.range(["#ffe0b2", "#ffb74d", "#ff9800", "#f57c00"]);

var bostonMedian = 0.20;

d3.json("preds_final.geojson", function(data) {

	for (var segment in data.features) {
		segments.push(data.features[segment].properties);
	}

	segments.sort(function(a, b) {
		return d3.descending(a.prediction, b.prediction);
	})
	// console.log(segments.length);
	segmentsHash = d3.map(segments, function(d) { return d.segment_id; });

	d3.select("#highest_risk_list")
		.selectAll("li")
		.data(segments.slice(0, 10))
		.enter()
		.append("li")
		.attr("class", "highRiskSegment")
		.html(function(d) { var nameObj = splitSegmentName(d.segment.display_name);
							return nameObj["name"] + "<br><span class='secondary'>" + nameObj["secondary"] + "</span>"; })
		.on("click", function(d) { populateSegmentInfo(d.segment_id); });

	makeBarChart(0, bostonMedian);
})

function splitSegmentName(segmentName) {
	var i = segmentName.length;

	if(segmentName.indexOf(" between ") > -1) {
		i = segmentName.indexOf(" between ");
	}
	else if(segmentName.indexOf(" from ") > -1) {
		i = segmentName.indexOf(" from ");
	}
	else if(segmentName.indexOf(" near ") > -1) {
		i = segmentName.indexOf(" near ");
	}

	return {name: segmentName.slice(0, i), secondary: segmentName.slice(i,)};
}

function zoomToSegment(segmentX, segmentY) {
	map.flyTo({center:[segmentX, segmentY], zoom: 18});
}

function populateSegmentInfo(segmentID) {
	console.log(segmentID);
	var segmentData = segmentsHash.get(segmentID);

	d3.select('#segment_details .segment_name')
		.html(function() { var nameObj = splitSegmentName(segmentData.segment.display_name);
						   return nameObj["name"] + "<br><span class='secondary'>" + nameObj["secondary"] + "</span>"; })
		.on("click", function(d) { zoomToSegment(segmentData.segment.center_x, segmentData.segment.center_y); });

	d3.select("#segment_details #prediction").text(DECIMALFMT(segmentData.prediction));
	d3.select("#risk_circle").style("fill", function(d) { return riskColor(segmentData.prediction); });

	// update prediction bar chart gauge
	updateBarChart(segmentData.prediction);

	// hide highest risk panel and slide in segment details panel
	d3.select('#segment_details').classed('slide_right', false);
	d3.select('#segment_details').classed('visible', true);
	d3.select('#highest_risk').classed('visible', false);

	// zoom into clicked-on segment
	zoomToSegment(segmentData.segment.center_x, segmentData.segment.center_y);
}

function makeBarChart(prediction, median) {
	var margin = {top: 11, right: 0, bottom: 48, left: 0},
		width = 200,
		height = 8;

	xScale.rangeRound([0, width]);

	var svg = d3.select("#predChart")
		.append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	svg.append("rect")
		.attr("class", "backgroundBar")
		.attr("x", 0)
		.attr("y", 0)
		.attr("width", width)
		.attr("height", height);

	// mark where the city average is
	svg.append("line")
		.attr("class", "avgLine")
		.attr("x1", xScale(median))
		.attr("y1", 0)
		.attr("x2", xScale(median))
		.attr("y2", height * 2);

	svg.append("text")
		.attr("class", "avgLabel")
		.attr("x", xScale(median))
		.attr("y", height * 3.5)
		.text("City Average:");

	svg.append("text")
		.attr("class", "avgLabel")
		.attr("x", xScale(median))
		.attr("y", height * 5.5)
		.text(DECIMALFMT(median));

	svg.selectAll(".predBar")
		.data([prediction])
		.enter()
		.append("rect")
		.attr("class", "predBar")
		.attr("x", 0)
		.attr("y", 0)
		.attr("width", xScale(prediction))
		.attr("height", height)
		.style("fill", riskColor(prediction));
}

function updateBarChart(prediction) {
	d3.selectAll(".predBar")
		.data([prediction])
		.transition()
		.attr("width", xScale(prediction))
		.style("fill", riskColor(prediction));
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

// get current filter values
function getFilterValues() {
	var filterValues = {};

	filterValues['riskThreshold'] = d3.select('#risk_slider').property('value');
	filterValues['speedlimit'] = d3.select('#speed_slider').property('value');

	return filterValues;
}

function update_map(map) {
	filters = getFilterValues();
	var new_filter;

	if(config.cities[0].id === "boston") {
		new_filter = ['all', ['>=', 'prediction', +filters['riskThreshold']], ['>=', 'SPEEDLIMIT', +filters['speedlimit']]];
	}
	else {
		new_filter = ['all', ['>=', 'prediction', +filters['riskThreshold']], ['>=', 'osm_speed', +filters['speedlimit']]];
	}

	map.setFilter('predictions', new_filter);
}