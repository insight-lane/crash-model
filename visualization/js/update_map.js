//style function for coloring the segments
function color_segments(feature) {
		if (feature.properties.crash === 1.0) {	return {color: "#f39c12"}; }
		else if (feature.properties.crash === 2.0) { return {color: "#e67e22"};	}
		else { return {color: "#e74c3c"}; }
}
	  	
// load GeoJSON from an external file
$.getJSON("historical_crashes.json",function(data){

	var week = 1;

    // create GeoJSON layer for the first week of data 
  	crashes = new L.geoJson(data, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === week;
	  	},
	  	style: color_segments
  	})

  	// add layer to map
	map.addLayer(crashes);

	// update map when input range changes
	d3.select('#week_selector').on("input", function() {
		update_map(+this.value);
	})

	function update_map(week) {
		// update week number displayed next to slider
		d3.select('#week_num').text(week);
		d3.select('#week_selector').property('value', week);

		console.log(week);
		
		//update data displayed on map based on week selected

		//clear map of layers
		map.removeLayer(crashes);

		//create new layer with updated data
		crashes = new L.geoJson(data, {
			filter: function(feature, layer) {
				return feature.properties.week === week;
			},
			style: color_segments
		})

		map.addLayer(crashes);
	}
});