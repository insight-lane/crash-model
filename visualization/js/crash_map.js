//////////////////////// CODE FOR MAP ////////////////////////////////////////////
var crashdata,
	cardata;

//style function for coloring the segments
/*
function color_segments(feature) {
		if (feature.properties.crash === 1.0) {	return {color: "#f39c12"}; }
		else if (feature.properties.crash === 2.0) { return {color: "#e67e22"};	}
		else { return {color: "#e74c3c"}; }
}
*/

var geojsonMarkerOptions = {
    radius: 5,
    fillColor: "#f39c12",
    color: "#d8890b",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8
};

function color_preds(feature) {
	var color = d3.scale.linear()
		.domain([0.02, 0.05])
		.range(["yellow", "red"]);

	return { color: color(feature.properties.pred) };
}

// load GeoJSON from an external file
$.getJSON("cad.geojson",function(data){

	geodata = data;

    // create GeoJSON layer for the first week of data 
  	crashes = new L.geoJson(data, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === 1;
	  	},
	  	pointToLayer: function(feature, latlng) {
	  		return L.circleMarker(latlng, geojsonMarkerOptions);
	  	}
  	})

  	// add layer to map
	map.addLayer(crashes);
});


$.getJSON("car_preds.json",function(data){

	cardata = data;

    // create GeoJSON layer for the first week of data 
  	car_preds = new L.geoJson(data, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === 1;
	  	},
	  	style: color_preds //color_segments
  	})

  	// add layer to map
	map.addLayer(car_preds);
});

