$(document).ready( function() {
	d3.selectAll(".experiment_data")
		.each(function() { processRuns(this); });
});

function processDataPoint(dp, points, stddev) {
	var csv = d3.select(dp).text();
	var columns = csv.split(",");
	
	var x = columns[0];
	var y = columns[1];
	var type = columns[2];
	
	if(type == "stddev"){
		var ypos = -1;
		
		for(var j = 0; j < points.length; j++) {
			if(points[j].label == x)
				ypos = points[j].y
		}
		if(ypos == -1 && console != undefined)
			console.log("Warning: data point for sigma at {0} not found".format(x));
	    if(ypos != -1 && y != "None"){
    		stddev.push({'label':x, 'y':ypos, 'dev':y});
        }

	} else {
		points.push({'label':x,'y':y})
	}
}

function isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
}

function processRun(run, experiment_data, run_map) {
	var name = d3.select(run).select(".name").text();
	
	var points = [];
	var stddev = [];
	
	var peptides =
		d3.select(run)
			.select(".peptides")
			.text();
	
	var units =
		d3.select(run)
			.select(".units")
			.text();
	
	d3.select(run)
		.selectAll(".datapoint")
		.each(function() { processDataPoint(this, points, stddev); });

    var isTime = true;
    for(var i in points){
        isTime = isTime && isNumber( points[i].label );
    }
	
	if (! (name in run_map)){
		run_map[name] = {'name':name, 'series':[], 'isTime': isTime, 'axis': units};
	}
	
	run_map[name].series.push({'peps':peptides, 'points':points, 'stddev':stddev});
}

function processRuns(experiment_data){
	var run_map = {}
	
	d3.select(experiment_data)
		.selectAll(".run")
		.each(function() { processRun(this, experiment_data, run_map); });
	
	createGraphs(experiment_data, run_map);
}

function createGraphs(experiment_data, run_map) {
	for(var r in run_map) {
		var run = run_map[r]
		if(run.isTime)
			createTimeSeriesGraph(experiment_data, run);
		else
			createBarGraph(experiment_data, run);
	}
}

function getMaxValue(run, property) {
	var mval = -10000.0;
	for(var i = 0; i < run.series.length; i++) {
		for(var j = 0; j < run.series[i].points.length; j++) {
			var val = parseFloat(run.series[i].points[j][property]);
			if(val > mval) {
				mval = val;
			}
		}
	}
	return mval;
}

function createTimeSeriesGraph(experiment_data, run) {
	var w = 475;
	var h = 400;
	var margin = 40;
	var rmargin = 130;
	var ceiling = 1.15;
	var lwidth = 125;
	var colors = d3.scale.category20();
	
	var container = d3.select(experiment_data)
						.select(".chart")
							.append("div")
								.style('display', "inline-block")
								.style('position', "relative");
	
	var parent = container.append("span");
	var graph = createGraph(parent, run.name, w, h, margin);
	
	var xmax = getMaxValue(run, "label");
	var ymax = getMaxValue(run, "y") * ceiling;
	
	var xaxis = d3.scale.linear().domain([0, xmax]).range([margin, w-rmargin]);
	var yaxis = d3.scale.linear().domain([0, ymax]).range([h-margin, margin]);
	
	var legendEntries = [];
	
	var xticks = []
	for(i = 0; i < run.series.length; i++){
		var pts = []
		var stddev = []
		for(j = 0; j < run.series[i].points.length; j++){
			var pt = run.series[i].points[j];
			
			xticks.push( parseFloat(pt.label) );
			pts.push( { 'x':parseFloat(pt.label), 'y':parseFloat(pt.y) } );
		}
		
		for(j = 0; j < run.series[i].stddev.length; j++){
			var pt = run.series[i].stddev[j]
			
			stddev.push( {'x': parseFloat(pt.label), 'y': parseFloat(pt.y), 's': parseFloat(pt.dev)} )
		}
		var name = run.series[i].peps
		
		addTimeSeries(graph, name, pts, xaxis, yaxis, colors(i));
		addErrorBars(graph, name, stddev, xaxis, yaxis, colors(i));
		
		legendEntries.push({'name':name, 'color':colors(i)});
	}
	
	addAxes(graph, run.axis, Array.unique(xticks), yaxis.ticks(7), xaxis, yaxis, false);
	addLegend(graph, legendEntries, w-lwidth, margin, lwidth, "line");
	addExportSVG(parent, container);
	addExportChartData(experiment_data, container);
}

function getArray(run, property) {
	rval = [];
	for(i = 0; i < run.series.length; i++) {
		for(j = 0; j < run.series[i].points.length; j++) {
			rval.push(run.series[i].points[j][property]);
		}
	}
	return rval;
}

function createBarGraph(experiment_data, run) {
	var h = 440;
	var margin = 40;
	var rmargin = 130;
	var bmargin = 80;
	var ceiling = 1.15;
	var lwidth = 125;
	var colors = d3.scale.category20();

	var xvals = Array.unique(getArray(run, "label"));
	xvals.unshift("");
	xvals.push(" ");
	
	var defaultBarWidth = 30;
	
	var w = margin + rmargin + defaultBarWidth * run.series.length * xvals.length;
	
	if(w > 750)
		w = 750;
	
	var container = d3.select(experiment_data)
						.select(".chart")
							.append("div")
								.style('display', "inline-block")
								.style('position', "relative");
	
	var parent = container.append("span");
	var graph = createGraph(parent, run.name, w, h, margin);
	
	
	var ymax = getMaxValue(run, "y") * ceiling;
	
	var xaxis = d3.scale.ordinal().domain(xvals).rangePoints([margin, w-rmargin]);
	var yaxis = d3.scale.linear().domain([0, ymax]).range([h-bmargin, margin]);
	
	var legendEntries = [];
	
	var xticks = []
	for(var i = 0; i < run.series.length; i++){
		var pts = [];
		var stddev = [];
		
		for(var j = 0; j < run.series[i].points.length; j++){
			var pt = run.series[i].points[j];
			xticks.push( parseFloat(pt.label) );
			pts.push( { 'x':pt.label, 'y':parseFloat(pt.y) } );
		}
		
		for(var j = 0; j < run.series[i].stddev.length; j++){
			var pt = run.series[i].stddev[j];
			stddev.push( {'x':pt.label, 'y': parseFloat(pt.y), 's': parseFloat(pt.dev)} );
		}
		var name = run.series[i].peps

		addBarSeries(graph, name, pts, xaxis, yaxis, colors(i), i, run.series.length);
		addErrorBars(graph, name, stddev, xaxis, yaxis, "#000", i, run.series.length);
		
		legendEntries.push({'name':name, 'color':colors(i)});
	}
	
	addAxes(graph, run.axis, xvals, yaxis.ticks(7), xaxis, yaxis, true);
	addLegend(graph, legendEntries, w-lwidth, margin, lwidth, "square");
	addExportSVG(parent, container);
	addExportChartData(experiment_data, container);
}
