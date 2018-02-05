var w = 800,
	h = 150,
	padding = 40;

var formatPercent = d3.format(".0%");

// functions to make axes
function make_xaxis(scale) {
	var xAxis = d3.svg.axis()
		.scale(scale)
		.orient("bottom");

	return xAxis;
}

function make_yaxis(scale) {
	var yAxis = d3.svg.axis()
		.scale(scale)
		.orient("left")

	return yAxis;
}

// set up charts
var weeklyPlot = d3.select("#weekly_barplot")
	.append("svg")
		.attr("width", w + padding*2)
		.attr("height", h + padding*2)
	.append("g")
		.attr("transform", "translate(" + padding + "," + padding + ")");

var dowPlot = d3.select("#dow_barplot")
	.append("svg")
		.attr("width", w/2 + padding*2)
		.attr("height", h + padding*2)
	.append("g")
		.attr("transform", "translate(" + padding + "," + padding + ")");

var hourlyPlot = d3.select("#hourly_barplot")
	.append("svg")
		.attr("width", w/2 + padding*2)
		.attr("height", h + padding*2)
	.append("g")
		.attr("transform", "translate(" + padding + "," + padding + ")");

// draw weekly bar graph
d3.csv("weekly_crashes.csv", function(d) {

	return {
		week: d.week,
		crashes: + d.crash
	};

}, function(error, data) {

	var barWidth = Math.floor(w / data.length - 1);

	// set up scales
	var xscale = d3.scale.linear()
		.domain([1, 53])
		.range([barWidth / 2, w - barWidth / 2]);

	var yscale = d3.scale.linear()
		.domain([0, d3.max(data, function(d) { return d.crashes; })])
		.range([h, 0]);

	// set up axes
	var xAxis = make_xaxis(xscale);

	var yAxis = make_yaxis(yscale);

	// draw axes
	weeklyPlot.append("g")
      	.attr("class", "x axis")
      	.attr("transform", "translate(0," + h + ")")
      	.call(xAxis)
      .append("text")
      	.attr("transform", "translate(" + w/2 + ", 30)")
      	.style("text-anchor", "middle")
      	.text("Week");

	weeklyPlot.append("g")
        .attr("class", "y axis")
        .call(yAxis);

	var bars = weeklyPlot.selectAll("crashbar")
		.data(data)
		.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return xscale(d.week) - barWidth/2; })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("width", barWidth)
		.attr("height", function(d) { return h - yscale(d.crashes); })
		.style("fill", "#b2b2b2");
		// .filter(function(d) { return d.week === "1"; })
		// .style("fill", "#d500f9");
})


// draw day of week bar graph
d3.csv("dow_crashes.csv", function(d) {

	return {
		dow: +d.dow,
		dow_name: d.dow_name,
		crashes: + d.N_EVENTS
	};

}, function(error, data) {

	var xscale = d3.scale.ordinal()
		.domain(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
		.rangeRoundBands([0, w/2], 0.1);

	var yscale = d3.scale.linear()
		.domain([0, d3.max(data, function(d) { return d.crashes; })])
		.rangeRound([h, 0]);

	var xAxis = make_xaxis(xscale);

	var yAxis = make_yaxis(yscale);

	// draw axes
	dowPlot.append("g")
      	.attr("class", "x axis")
      	.attr("transform", "translate(0," + h + ")")
      	.call(xAxis);

	dowPlot.append("g")
        .attr("class", "y axis")
        .call(yAxis);

	var bars = dowPlot.selectAll("crashbar")
		.data(data)
		.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return xscale(d.dow_name); })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("width", xscale.rangeBand())
		.attr("height", function(d) { return h - yscale(d.crashes); })
		.style("fill", "#b2b2b2");
})

// draw hourly bar graph
d3.csv("hourly_crashes.csv", function(d) {

	return {
		weekend: +d.weekend,
		hour: +d.hour,
		crashes: +d.N_EVENTS,
		pct_crash: +d.pct_crash,
		weekend_lbl: d.weekend_lbl
	};

}, function(error, data) {

	var barWidth = Math.floor(w / data.length) - 1;

	//separate dataset into weekeday and weekends
	weekday_crashes = [];
	weekend_crashes = [];
	data.forEach(function(d) {
		if (d.weekend_lbl === 'Weekday') {
			weekday_crashes.push(d);
		}
		else {
			weekend_crashes.push(d);
		}
	})

	var xscale = d3.scale.linear()
		.domain([0, 23])
		.range([barWidth / 2, w/2 - barWidth / 2]);

	var yscale = d3.scale.linear()
		.domain([0, d3.max(data, function(d) { return d.pct_crash; })])
		.rangeRound([h, 0]);

	var xAxis = make_xaxis(xscale);

	var yAxis = make_yaxis(yscale);
	yAxis.tickFormat(formatPercent);

	// draw axes
	hourlyPlot.append("g")
      	.attr("class", "x axis")
      	.attr("transform", "translate(0," + h + ")")
      	.call(xAxis)
      .append("text")
      	.attr("transform", "translate(" + w/4 + ", 30)")
      	.style("text-anchor", "middle")
      	.text("Hour");

	hourlyPlot.append("g")
        .attr("class", "y axis")
        .call(yAxis);

	var bars = hourlyPlot.selectAll("crashbar")
		.data(weekday_crashes)
		.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
		.attr("y", function(d) { return yscale(d.pct_crash); })
		.attr("width", barWidth)
		.attr("height", function(d) { return h - yscale(d.pct_crash); })
		.style("fill", "#b2b2b2");


	d3.selectAll("input[name='daytype']").on("change", function() {
		
		if (this.value==="Weekend"){
			bars.data(weekend_crashes)
				.transition(1000)
				.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
				.attr("y", function(d) { return yscale(d.pct_crash); })
				.attr("width", barWidth)
				.attr("height", function(d) { return h - yscale(d.pct_crash); })
		}
		else {
			bars.data(weekday_crashes)
				.transition(1000)
				.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
				.attr("y", function(d) { return yscale(d.pct_crash); })
				.attr("width", barWidth)
				.attr("height", function(d) { return h - yscale(d.pct_crash); })
		}
	});
})