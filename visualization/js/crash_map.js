var crashdata,
	cardata;

//style functions
var geojsonMarkerOptions = {
    radius: 8,
    fillColor: "#d32f2f",
    color: "#9a0007",
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
	crashdata = data;

    // create GeoJSON layer for the first week of data 
  	crashes = new L.geoJson(crashdata, {
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


$.getJSON("car_preds_named.json",function(data){
	cardata = data;

    // create GeoJSON layer for the first week of data 
  	car_preds = new L.geoJson(data, {
	  	filter: function(feature, layer) {
	  		return feature.properties.week === 1;
	  	},
	  	style: color_preds, //color_segments
	  	onEachFeature: onEachFeature
  	})

  	// add layer to map
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
});

// add layer control
//L.control.layers(baseMaps, overlayMaps).addTo(map);