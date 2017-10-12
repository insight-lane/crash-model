// update map and bar graph when input range changes
d3.select('#week_selector').on("input", function() {
	update_map(+this.value);
	highlight_bar(this.value);
});

function update_map(week) {
	// update week number displayed next to slider
	d3.select('#week_num').text(week);
	d3.select('#week_selector').property('value', week);
	
	//update data displayed on map based on week selected

	//clear map of layers
	map.removeLayer(crashes);
	map.removeLayer(car_preds);

	//create new layers with updated data
  	crashes = new L.geoJson(crashdata, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === week;
	  	},
	  	pointToLayer: function(feature, latlng) {
	  		return L.circleMarker(latlng, geojsonMarkerOptions);
	  	}
  	})

	car_preds = new L.geoJson(cardata, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === week;
	  	},
	  	style: color_preds,
	  	onEachFeature: onEachFeature
  	})

  	// add layers to map
	map.addLayer(crashes);
	map.addLayer(car_preds); 

	// add pop up
	function onEachFeature(feature, layer) {
		if (feature.properties.st_name) {
			layer.bindPopup(feature.properties.st_name + "<br /> Predicted Probability for Week " + feature.properties.week + ": " + feature.properties.pred);
		}
		else {
			layer.bindPopup("Predicted Probability for Week " + feature.properties.week + ": " + feature.properties.pred);
		}
	}
}

function highlight_bar(week) {
	barPlot.selectAll(".crashbar")
		.data(weeklydata)
		.style("fill", "#7f7f7f")
		.filter(function(d) { return d.week === week ; })
		.style("fill", "#d32f2f");
}