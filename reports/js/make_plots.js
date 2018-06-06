var weekly_crashes;

var w = 800,
	h = 150,
	padding = 40;


var barWidth = Math.floor(w / 52 - 1);

// set up scales
var xscale = d3.scale.linear()
	.domain([1, 53])
	.range([barWidth / 2, w - barWidth / 2]);

var yscale = d3.scale.linear()
	.range([h, 0]);

var xAxis = d3.svg.axis()
	.scale(xscale)
	.orient("bottom");

var yAxis = d3.svg.axis()
	.scale(yscale)
	.orient("left");


// set up charts
var weeklyPlot = d3.select("#weekly_barplot")
	.append("svg")
		.attr("width", w + padding*2)
		.attr("height", h + padding*2)
	.append("g")
		.attr("transform", "translate(" + padding + "," + padding + ")");


// draw weekly bar graph
d3.csv("weekly_crashes.csv", function(d) {

	return {
		city: d.city,
		year: +d.year,
		week: +d.week,
		crashes: +d.counts
	};

}, function(error, data) {

	weekly_crashes = data;

	data = data.filter(function(d) { return d.city === config.cities[0].id; });

	yscale.domain([0, d3.max(data, function(d) { return d.crashes; })])


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


	var bars = weeklyPlot.selectAll(".crashbar")
		.data(data, function(d) { return d.week; })
		.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return xscale(d.week) - barWidth/2; })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("width", barWidth)
		.attr("height", function(d) { return h - yscale(d.crashes); })
		.style("fill", "#b2b2b2")
		.style("fill", "#b2b2b2")
		.filter(function(d) { return d.week === 1; })
		.style("fill", "#d500f9");

	// draw_weekly_bars(weekly_crashes, "Boston");

})

function draw_weekly_bars(dataset, city) {

    data = dataset.filter(function(d) { return d.city === city; });

	yscale.domain([0, d3.max(data, function(d) { return d.crashes; })]);

	// set up axes
	weeklyPlot.select(".y.axis").call(yAxis);

	// update bars
	var bars = weeklyPlot.selectAll(".crashbar")
		.data(data, function(d) { return d.week; })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("height", function(d) { return h - yscale(d.crashes); });

	bars.enter()
	  .append("rect")
		.attr("class", "crashbar")
		.attr("x", function(d) { return xscale(d.week) - barWidth/2; })
		.attr("y", function(d) { return yscale(d.crashes); })
		.attr("width", barWidth)
		.attr("height", function(d) { return h - yscale(d.crashes); })
		.style("fill", "#b2b2b2");

	bars.exit().remove();
}




// var weekly_crashes;
//, dow_crashes, hourly_crashes;

// var w = 800,
// 	h = 150,
// 	padding = 40;

// var formatPercent = d3.format(".0%");

// // functions to make axes
// function make_xaxis(scale) {
// 	var xAxis = d3.svg.axis()
// 		.scale(scale)
// 		.orient("bottom");

// 	return xAxis;
// }

// function make_yaxis(scale) {
// 	var yAxis = d3.svg.axis()
// 		.scale(scale)
// 		.orient("left")

// 	return yAxis;
// }


// // set up charts
// var weeklyPlot = d3.select("#weekly_barplot")
// 	.append("svg")
// 		.attr("width", w + padding*2)
// 		.attr("height", h + padding*2)
// 	.append("g")
// 		.attr("transform", "translate(" + padding + "," + padding + ")");

// var dowPlot = d3.select("#dow_barplot")
// 	.append("svg")
// 		.attr("width", w/2 + padding*2)
// 		.attr("height", h + padding*2)
// 	.append("g")
// 		.attr("transform", "translate(" + padding + "," + padding + ")");

// var hourlyPlot = d3.select("#hourly_barplot")
// 	.append("svg")
// 		.attr("width", w/2 + padding*2)
// 		.attr("height", h + padding*2)
// 	.append("g")
// 		.attr("transform", "translate(" + padding + "," + padding + ")");


// // draw weekly bar graph
// d3.csv("weekly_crashes.csv", function(d) {

// 	return {
// 		city: d.city,
// 		year: +d.year,
// 		week: +d.week,
// 		crashes: + d.counts
// 	};

// }, function(error, data) {

// 	weekly_crashes = data;

// 	data = data.filter(function(d) { return d.city === "Boston"; });

// 	var barWidth = Math.floor(w / 52 - 1);

// 	// set up scales
// 	var xscale = d3.scale.linear()
// 		.domain([1, 53])
// 		.range([barWidth / 2, w - barWidth / 2]);

// 	var yscale = d3.scale.linear()
// 		.domain([0, d3.max(data, function(d) { return d.crashes; })])
// 		.range([h, 0]);

// 	// set up axes
// 	var xAxis = make_xaxis(xscale);
// 	var yAxis = make_yaxis(yscale);

// 	// draw axes
// 	weeklyPlot.append("g")
//       	.attr("class", "x axis")
//       	.attr("transform", "translate(0," + h + ")")
//       	.call(xAxis)
//       .append("text")
//       	.attr("transform", "translate(" + w/2 + ", 30)")
//       	.style("text-anchor", "middle")
//       	.text("Week");

// 	weeklyPlot.append("g")
//         .attr("class", "y axis")
//         .call(yAxis);


// 	var bars = weeklyPlot.selectAll(".crashbar")
// 		.data(data)
// 		.enter()
// 	  .append("rect")
// 		.attr("class", "crashbar")
// 		.attr("x", function(d) { return xscale(d.week) - barWidth/2; })
// 		.attr("y", function(d) { return yscale(d.crashes); })
// 		.attr("width", barWidth)
// 		.attr("height", function(d) { return h - yscale(d.crashes); })
// 		.style("fill", "#b2b2b2");

// 	// draw_weekly_bars(weekly_crashes, "Boston");

// })


// var cityselect = d3.select("#city_selector")
// 	.on("change", update_bars);

// function update_bars() {
// 	selectedCity = d3.select("#city_selector").property("value");
// 	draw_weekly_bars(weekly_crashes, selectedCity);
// }

// function draw_weekly_bars(dataset, city) {

//     data = dataset.filter(function(d) { return d.city === city; });

// 	var barWidth = Math.floor(w / 52 - 1);

// 	// set up scales
// 	var xscale = d3.scale.linear()
// 		.domain([1, 53]);

// 	var yscale = d3.scale.linear()
// 		.domain([0, d3.max(data, function(d) { return d.crashes; })]);

// 	// set up axes
// 	var xAxis = make_xaxis(xscale);
// 	var yAxis = make_yaxis(yscale);

// 	// update bars
// 	var bars = weeklyPlot.selectAll(".crashbar")
// 		.data(data)
// 		.attr("y", function(d) { return yscale(d.crashes); })
// 		.attr("height", function(d) { return h - yscale(d.crashes); });

// 	bars.enter()
// 	  .append("rect")
// 		.attr("class", "crashbar")
// 		.attr("x", function(d) { return xscale(d.week) - barWidth/2; })
// 		.attr("y", function(d) { return yscale(d.crashes); })
// 		.attr("width", barWidth)
// 		.attr("height", function(d) { return h - yscale(d.crashes); })
// 		.style("fill", "#b2b2b2");

// 	bars.exit().remove();
// }

// // draw day of week bar graph
// d3.csv("dow_crashes.csv", function(d) {

// 	return {
// 		city: d.city,
// 		year: d.year,
// 		dow: +d.dow,
// 		dow_name: d.dow_name,
// 		crashes: + d.counts
// 	};

// }, function(error, data) {

// 	var xscale = d3.scale.ordinal()
// 		.domain(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
// 		.rangeRoundBands([0, w/2], 0.1);

// 	var yscale = d3.scale.linear()
// 		.domain([0, d3.max(data, function(d) { return d.crashes; })])
// 		.rangeRound([h, 0]);

// 	var xAxis = make_xaxis(xscale);

// 	var yAxis = make_yaxis(yscale);

// 	// draw axes
// 	dowPlot.append("g")
//       	.attr("class", "x axis")
//       	.attr("transform", "translate(0," + h + ")")
//       	.call(xAxis);

// 	dowPlot.append("g")
//         .attr("class", "y axis")
//         .call(yAxis);

// 	var bars = dowPlot.selectAll("crashbar")
// 		.data(data)
// 		.enter()
// 	  .append("rect")
// 		.attr("class", "crashbar")
// 		.attr("x", function(d) { return xscale(d.dow_name); })
// 		.attr("y", function(d) { return yscale(d.crashes); })
// 		.attr("width", xscale.rangeBand())
// 		.attr("height", function(d) { return h - yscale(d.crashes); })
// 		.style("fill", "#b2b2b2");
// })

// // draw hourly bar graph
// d3.csv("hourly_crashes.csv", function(d) {

// 	return {
// 		city: d.city,
// 		year: d.year,
// 		weekend: +d.weekend,
// 		hour: +d.hour,
// 		crashes: +d.counts,
// 		pct_crash: +d.pct_crash,
// 		weekend_lbl: d.weekend_lbl
// 	};

// }, function(error, data) {

// 	var barWidth = Math.floor(w / data.length) - 1;

// 	//separate dataset into weekeday and weekends
// 	weekday_crashes = [];
// 	weekend_crashes = [];
// 	data.forEach(function(d) {
// 		if (d.weekend_lbl === 'Weekday') {
// 			weekday_crashes.push(d);
// 		}
// 		else {
// 			weekend_crashes.push(d);
// 		}
// 	})

// 	var xscale = d3.scale.linear()
// 		.domain([0, 23])
// 		.range([barWidth / 2, w/2 - barWidth / 2]);

// 	var yscale = d3.scale.linear()
// 		.domain([0, d3.max(data, function(d) { return d.pct_crash; })])
// 		.rangeRound([h, 0]);

// 	var xAxis = make_xaxis(xscale);

// 	var yAxis = make_yaxis(yscale);
// 	yAxis.tickFormat(formatPercent);

// 	// draw axes
// 	hourlyPlot.append("g")
//       	.attr("class", "x axis")
//       	.attr("transform", "translate(0," + h + ")")
//       	.call(xAxis)
//       .append("text")
//       	.attr("transform", "translate(" + w/4 + ", 30)")
//       	.style("text-anchor", "middle")
//       	.text("Hour");

// 	hourlyPlot.append("g")
//         .attr("class", "y axis")
//         .call(yAxis);

// 	var bars = hourlyPlot.selectAll("crashbar")
// 		.data(weekday_crashes)
// 		.enter()
// 	  .append("rect")
// 		.attr("class", "crashbar")
// 		.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
// 		.attr("y", function(d) { return yscale(d.pct_crash); })
// 		.attr("width", barWidth)
// 		.attr("height", function(d) { return h - yscale(d.pct_crash); })
// 		.style("fill", "#b2b2b2");


// 	d3.selectAll("input[name='daytype']").on("change", function() {

// 		if (this.value==="Weekend"){
// 			bars.data(weekend_crashes)
// 				.transition(1000)
// 				.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
// 				.attr("y", function(d) { return yscale(d.pct_crash); })
// 				.attr("width", barWidth)
// 				.attr("height", function(d) { return h - yscale(d.pct_crash); })
// 		}
// 		else {
// 			bars.data(weekday_crashes)
// 				.transition(1000)
// 				.attr("x", function(d) { return xscale(d.hour) - barWidth/2; })
// 				.attr("y", function(d) { return yscale(d.pct_crash); })
// 				.attr("width", barWidth)
// 				.attr("height", function(d) { return h - yscale(d.pct_crash); })
// 		}
// 	});
// })