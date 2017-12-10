// update beforeMap and bar graph when input range changes
d3.select('#week_selector').on("input", function() {
	update_map(+this.value);
	highlight_bar(this.value);
});

function update_map(week) {
	// update week number displayed next to slider
	d3.select('#week_num').text(week);
	d3.select('#week_selector').property('value', week);
	
	//update data displayed on map based on week selected
	beforeMap.setFilter('crashes', ['==', 'week', week]);
	beforeMap.setFilter('predictions', ['==', 'week', week]);

}

function highlight_bar(week) {
	d3.select("#weekly_barplot")
	  .selectAll(".crashbar")
		.style("fill", "#b2b2b2")
		.filter(function(d) { return d.week === week ; })
		.style("fill", "#d500f9");
}

// update afterMap when selected option changes
d3.select('#after_week_selector').on('change', function() {
	var selected_week = d3.select('#after_week_selector').property('value');
	afterMap.setFilter('crashes', ['==', 'week', +selected_week]);
})