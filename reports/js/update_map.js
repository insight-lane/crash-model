// update beforeMap when input range changes
d3.select('#week_selector').on("input", function() {
	// update week number displayed next to slider
	d3.select('#week_num').text(+this.value);
	d3.select('#week_selector').property('value', +this.value);

	update_map(+this.value, beforeMap);

	// highlight_bar(this.value);
});

// update afterMap when selected option changes
d3.select('#compare_week_selector').on('input', function() {

	d3.select('#compare_week').text(+this.value);
	d3.select('#compare_week_selector').property('value', +this.value);

	update_map(+this.value, afterMap);
})

function update_map(week, map) {
	//update data displayed on map based on week selected
	map.setFilter('crashes', ['==', 'week', week]);
	map.setFilter('predictions', ['==', 'week', week]);
}

/*function highlight_bar(week) {
	d3.select("#weekly_barplot")
	  .selectAll(".crashbar")
		.style("fill", "#b2b2b2")
		.filter(function(d) { return d.week === week ; })
		.style("fill", "#d500f9");
}
*/
