var DECIMALFMT = d3.format(".2f");

var segments = [];
var segmentsHash;

var xScale = d3.scaleLinear().domain([0, 1]);
var riskColor = d3.scaleLinear()
	.domain([0.2, 0.4, 0.6, 0.8])
	.range(["#ffe0b2", "#ffb74d", "#ff9800", "#f57c00"]);


d3.json("preds_final.geojson", function(data) {

	for (var segment in data.features) {
		segments.push(data.features[segment].properties);
	}

	segments.sort(function(a, b) {
		return d3.descending(a.prediction, b.prediction);
	})

	var midpoint = Math.floor(segments.length/2);
	var median = segments[midpoint].prediction;

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

	makeBarChart(0, median);

	// populateFeatureImportancesTbl(data);

	// add crash layer to map so user can view if they choose
	d3.json("crashes.json", function(data) {
		// load in standardized crash json and gets total number of crashes by location
		var summedData = totalCrashesByLocation(data);
		var maxCrashes = d3.max(summedData, function(d) { return d.value;});

		// then convert the aggregated json into a geojson so it can be displayed on map
		var crashGeojson = buildGeojson(summedData);

		// on intiial load, do not display crashes
		map.addLayer({
			id: 'crashes',
			type: 'circle',
			source: {
				type: 'geojson',
				data: crashGeojson
			},
			layout: {
				visibility: 'none'
			},
			paint: {
				'circle-radius': {
					property: 'total_crashes',
					type: 'exponential',
					stops: [
						[1, 3],
						[maxCrashes, 20]
					]
				},
				'circle-color': '#fff',
				'circle-stroke-color': '#fff',
				'circle-opacity': 0.5
			},
		}, 'admin-2-boundaries-dispute');

		map.on('click', 'crashes', function(e) {
			var coordinates = e.features[0].geometry.coordinates.slice();
			var crashes = e.features[0].properties.total_crashes;

			new mapboxgl.Popup()
				.setLngLat(coordinates)
				.setText(crashes > 1 ? crashes + " crashes" : "1 crash")
				.addTo(map);
		});

		map.on('mouseenter', 'crashes', function() {
			map.getCanvas().style.cursor = 'pointer';
		});

		map.on('mouseleave', 'crashes', function() {
			map.getCanvas().style.cursor = '';
		});
	})
})

function totalCrashesByLocation(json) {
	json.forEach(function(crash) {
		crash.key = crash.location.longitude + "|" + crash.location.latitude;
		crash.n = 1;
	})

	var data = d3.nest()
		.key(function(d) { return d.key; })
		.rollup(function(d) { return d3.sum(d, function(g) { return g.n; }); })
		.entries(json);

	return data;
}

function buildGeojson(json) {
	var features = [];
	json.forEach(function(crash) {
		var crashObj = {};
		crashObj.type = "Feature";
		crashObj.geometry = {"type": "Point", "coordinates": [ crash.key.split("|")[0], crash.key.split("|")[1]]};
		crashObj.properties = {"total_crashes": crash.value};
		features.push(crashObj);
	});

	var crashGeojson = {}
	crashGeojson.type = "FeatureCollection";
	crashGeojson.features = features;

	return(crashGeojson);
}

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
	var segmentData = segmentsHash.get(segmentID);
	// console.log(segmentData);

	d3.select('#segment_details .segment_name')
		.html(function() { var nameObj = splitSegmentName(segmentData.segment.display_name);
						   return nameObj["name"] + "<br><span class='secondary'>" + nameObj["secondary"] + "</span>"; })
		.on("click", function(d) { zoomToSegment(segmentData.segment.center_x, segmentData.segment.center_y); });

	d3.select("#segment_details #prediction").text(DECIMALFMT(segmentData.prediction));
	d3.select("#risk_circle").style("fill", function(d) { return riskColor(segmentData.prediction); });

	// update prediction bar chart gauge
	updateBarChart(segmentData.prediction);

	// update feature importances based on segment's attributes
	// updateFeatureImportances(segmentData);

	// hide highest risk panel and slide in segment details panel
	d3.select('#segment_details').classed('slide_right', false);
	d3.select('#segment_details').classed('visible', true);
	d3.select('#highest_risk').classed('visible', false);

	// zoom into clicked-on segment
	zoomToSegment(segmentData.segment.center_x, segmentData.segment.center_y);
}

function makeBarChart(prediction, median) {

	var margin = {top: 0, right: 10, bottom: 48, left: 10},
		width = 250,
		height = 10;

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

	// adjust text alignment of City Average label if average is particularly low or high
	if(median <= 0.1) {
		d3.selectAll("#predChart .avgLabel").classed("leftAligned", true);
	}
	else if(median >= 0.9) {
		d3.selectAll("#predChart .avgLabel").classed("rightAligned", true);
	}
}

function updateBarChart(prediction) {
	d3.selectAll(".predBar")
		.data([prediction])
		.transition()
		.attr("width", xScale(prediction))
		.style("fill", riskColor(prediction));
}

function updateFeatureImportances(segmentData) {
	d3.selectAll("#featImportancesTbl td").classed("selected", false);

	if(segmentData.AADT >= 10000) {
		d3.select("#featImportancesTbl .feature.first td.yes").classed("selected", true);
	}
	else {
		d3.select("#featImportancesTbl .feature.first td.no").classed("selected", true);
	}

	if(segmentData.AADT <= 1000) {
		d3.select("#featImportancesTbl .feature.second td.yes").classed("selected", true);
	}
	else {
		d3.select("#featImportancesTbl .feature.second td.no").classed("selected", true);
	}

	if(segmentData.intersection === 1) {
		d3.select("#featImportancesTbl .feature.third td.yes").classed("selected", true);
	}
	else {
		d3.select("#featImportancesTbl .feature.third td.no").classed("selected", true);
	}

	if(segmentData.F_F_CLASS <= 3) {
		d3.select("#featImportancesTbl .feature.fourth td.yes").classed("selected", true);
	}
	else {
		d3.select("#featImportancesTbl .feature.fourth td.no").classed("selected", true);
	}

	if(segmentData.SPEEDLIMIT25 === 1) {
		d3.select("#featImportancesTbl .feature.fifth td.yes").classed("selected", true);
	}
	else {
		d3.select("#featImportancesTbl .feature.fifth td.no").classed("selected", true);
	}
}


function populateFeatureImportancesTbl(data) {

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

// event handlers to toggle crashes layer
d3.select("#checkbox_crashes").on("change", function() {
	if(this.checked) {
		map.setLayoutProperty('crashes', 'visibility', 'visible');
	}
	else {
		map.setLayoutProperty('crashes', 'visibility', 'none');
	}
});