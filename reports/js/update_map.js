// update beforeMap when week changes
d3.select('#week_selector').on("input", function() {

	// update week number displayed next to slider
	d3.select('#week_num').text(+this.value);
	d3.select('#week_selector').property('value', +this.value);

	update_map(+this.value, beforeMap);
});

function update_map(week, map) {
	//update data displayed on map based on week selected
	var new_filter = ['all', ['==', 'week', week]];

	map.setFilter('crashes', new_filter);
}