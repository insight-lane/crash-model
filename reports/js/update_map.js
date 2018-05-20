// update map when week changes and highlight new bar
d3.select('#week_selector').on("input", function() {

	// update week number displayed next to slider
	d3.select('#week_num').text(+this.value);
	d3.select('#week_selector').property('value', +this.value);

	update_map(+this.value, beforeMap);

	highlight_bar(+this.value);
});

function update_map(week, map) {
	//update data displayed on map based on week selected
	var new_filter = ['all', ['==', 'week', week]];

	map.setFilter('crashes', new_filter);
}

// highlight crash bar of the week selected
function highlight_bar(week) {
	d3.select("#weekly_barplot")
	  .selectAll(".crashbar")
		.style("fill", "#b2b2b2")
		.filter(function(d) { return d.week === week ; })
		.style("fill", "#d500f9");
}
