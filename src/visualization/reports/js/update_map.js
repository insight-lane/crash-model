// update beforeMap when week changes
d3.select('#week_selector').on("input", function() {
	// update week number displayed next to slider
	d3.select('#week_num').text(+this.value);
	d3.select('#week_selector').property('value', +this.value);

	// get city currently being viewed
	selectedCity = d3.select('#city_selector').property('value');

	update_map(+this.value, selectedCity, beforeMap);

	// highlight_bar(this.value);
});

// update afterMap when week changes
d3.select('#compare_week_selector').on('input', function() {

	// update week number displayed next to slider
	d3.select('#compare_week').text(+this.value);
	d3.select('#compare_week_selector').property('value', +this.value);

	// get city currently being viewed
	selectedCity = d3.select('#city_selector').property('value');

	update_map(+this.value, selectedCity, afterMap);
})

// update plots when city changes
d3.select("#city_selector").on("change", function() {

	// grab inputs
	selectedCity = d3.select('#city_selector').property('value');
	selectedWeek = d3.select('#week_selector').property('value');
	selectedCompareWeek = d3.select('#compare_week_selector').property('value');

	update_map(+selectedWeek, selectedCity, beforeMap);
	update_map(+selectedCompareWeek, selectedCity, afterMap);
	update_bars(selectedCity);
});

function update_map(week, city, map) {
	//update data displayed on map based on week selected
	var new_filter = ['all', ['==', 'week', week], ['==', 'city', city]];
	
	map.setFilter('crashes', new_filter);
	map.setFilter('predictions', new_filter);
}

function update_bars(city) {
	draw_weekly_bars(weekly_crashes, selectedCity);
	//draw_dow_bars(dow_crashes, selectedCity);
}


/*function highlight_bar(week) {
	d3.select("#weekly_barplot")
	  .selectAll(".crashbar")
		.style("fill", "#b2b2b2")
		.filter(function(d) { return d.week === week ; })
		.style("fill", "#d500f9");
}
*/
