var weeklydata;

var w = 800,
	h = 150,
	padding = 40;

// set up scales
var xscale = d3.scale.linear()
	.domain([1, 53]);

var yscale = d3.scale.linear()
	.rangeRound([h, 0]);

// set up axes
var xAxis = d3.svg.axis()
	.scale(xscale)
	.orient("bottom")
	.ticks(10);

var yAxis = d3.svg.axis()
	.scale(yscale)
	.orient("left");

// set up chart
var barPlot = d3.select("#barplot")
	.append("svg")
		.attr("width", w + padding*2)
		.attr("height", h + padding*2)
	.append("g")
		.attr("transform", "translate(" + padding + "," + padding + ")");

d3.csv("weekly_crashes.csv", function(d) {

	return {
		week: d.week,
		crashes: + d.crash
	};

}, function(error, data) {

	weeklydata = data;

	//console.log(data);
	xscale.range([w / data.length / 2, w - w / data.length / 2]);
	yscale.domain([0, d3.max(data, function(d) { return d.crashes; })]);

	// draw axes
	barPlot.append("g")
      	.attr("class", "x axis")
      	.attr("transform", "translate(0," + h + ")")
      	.call(xAxis)
      .append("text")
      	.attr("transform", "translate(" + w/2 + ", 30)")
      	.style("text-anchor", "middle")
      	.text("Week");

	barPlot.append("g")
        .attr("class", "y axis")
        .call(yAxis);

	var bars = barPlot.selectAll("crashbar")
		.data(data)
		.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return (xscale(d.week) - w / data.length / 2) + 1; })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("width", (w / data.length) - 1)
		.attr("height", function(d) { return h - yscale(d.crashes); })
		.style("fill", "#7f7f7f")
		.filter(function(d) { return d.week === "1"; })
		.style("fill", "#d32f2f");
})