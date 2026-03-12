function format_text(name, width, size) {
    var max_width = width / size;
    if(name.length > max_width){
        return name.substring(0, max_width) + "...";
    }
    return name;
}

function addLegend(graph, legendEntries, xpos, ypos, width, marker) {
	var h = 20;
	
	var height = legendEntries.length * h;
	
    var actualWidth = 0;
    for(var i in legendEntries){
        var entry = legendEntries[i];
        var eWidth = entry.name.length * 9 + 30
        if(eWidth > actualWidth) {
            actualWidth = eWidth;
        }
    }

    var dx = 0;
    if(actualWidth < width){
        dx = width - actualWidth;
        width = actualWidth;
    }
	var legend = graph.append("g")
				.attr("class", "legend")
				.attr("transform", "translate({0},{1})".format( dx + xpos, ypos ));

	legend.append("rect")
		.attr("class", "bg")
		.attr("x", 0)
		.attr("y", 0)
		.attr("width", width - 5)
		.attr("height", height)
        .style("fill", "none")
        .style("stroke", "black")
        .style("stroke-width", "1px");
	
	legend.selectAll("text.entry")
			.data(legendEntries)
		.enter().append("text")
			.attr("class", "entry")
			.attr("x", 30)
			.attr("y", function(d,i) { return (i+1) * h - 6 })
            .style("fill","black")
            .style("font-size", "9pt")
            .style("text-anchor", "left")
			.text(function(d) { return format_text(d.name, width - 30, 8) });
	
	if(marker == "line"){
		legend.selectAll("line.marker")
				.data(legendEntries)
			.enter().append("line")
				.attr("class", "marker")
				.attr("x1", 5)
				.attr("x2", 25)
				.attr("y1", function(d,i) {return (i+1) * h - h/2; })
				.attr("y2", function(d,i) {return (i+1) * h - h/2; })
				.attr("stroke", function(d){ return d.color });
		
		legend.selectAll("circle.marker")
				.data(legendEntries)
			.enter().append("circle")
				.attr("class", "marker")
				.attr("r", 2)
				.attr("cx", 15)
				.attr("cy", function(d,i) {return (i+1) * h - h/2; })
                .style("fill", "none")
                .style("stroke-width", "1px")
				.style("stroke", function(d,i) { return d.color } );
	}
	
	if(marker == "square"){
		legend.selectAll("rect.marker")
			.data(legendEntries)
		.enter().append("rect")
			.attr("class", "marker")
			.attr("x", 10)
			.attr("width", 15)
			.attr("y", function(d,i) {return i * h+5; })
			.attr("height", function(d,i) {return h-10; })
			.attr("fill", function(d){ return d.color })
            .style("stroke", "lightgray")
            .style("stroke-width", "1px");	
	}
}

function addTimeSeries(graph, name, pts, xaxis, yaxis, color) {
	var line = 
		d3.svg.line()
			.x(function(d) { return xaxis( d.x ) } )
			.y(function(d) { return yaxis( d.y ) } )

    var non_null = [];
    var consecutive_runs = [];
    var crun = [];
    for(var i in pts){
        if(!isNaN(pts[i].y)){
            crun.push(pts[i]);
            non_null.push(pts[i]);
        }else if(crun.length > 0){
            consecutive_runs.push(crun);
            crun = [];
        }
    }

    if(crun.length > 0)
        consecutive_runs.push(crun);

    var clsname = name.replace(":","").replace(",","");
	graph.selectAll('circle.'+clsname)
		.data(non_null)
	.enter().append('circle')
		.attr("class", "point "+clsname)
		.attr("r", 2)
		.attr("cx", function(d) { return xaxis( parseFloat(d.x) ) })
		.attr("cy", function(d) { return yaxis( parseFloat(d.y) ) })
		.style("stroke", color)
		.style("fill", "none")
		.style("stroke-width", "1px");
	
	graph.selectAll('path.'+clsname)
		.data(consecutive_runs)
	.enter().append("path")
		.attr("class", "series "+clsname)
    	.attr("d", line)
    	.style("stroke", color)
        .style("fill","none")
        .style("stroke-width","2px")
        .style("opacity","0.8");
}

function addBarSeries(graph, name, pts, xaxis, yaxis, color, i, num) {
	if(typeof(i) === 'undefined')
		i = 1;
	if(typeof(num) === 'undefined')
		num = 1;

    var non_null = [];
    for(var p in pts){
        if(!isNaN(pts[p].y)){
            non_null.push(pts[p]);
        }
    }
	
	var xsize = Array.max(xaxis.range()) - Array.min(xaxis.range());
	var barw = xsize / (2 * xaxis.domain().length) - 5;
	
	var offset = i * 2 * barw / num;

	var clsname = name.replace(":","").replace(",","");
	graph.selectAll('rect.'+clsname)
			.data(non_null)
		.enter().append('rect')
			.attr("class", "bar "+clsname)
			.attr("x", function(d) { return xaxis(d.x) - barw + offset })
			.attr("y", function(d) { return yaxis(d.y) })
			.attr("width", function(d) { return 2 * (barw / num) })
			.attr("height", function(d) { return yaxis(0) - yaxis(d.y) })
			.style("fill", color);
}

function addErrorBars(graph, name, errorbars, xaxis, yaxis, color, i, num) {
	if(typeof(i) === 'undefined')
		i = 0;
	if(typeof(num) === 'undefined')
		num = 1;
	
	var offset = 0;
	
	if(num > 1){
		var xsize = Array.max(xaxis.range()) - Array.min(xaxis.range());
		var barw = xsize / (2 * xaxis.domain().length) - 5;
		offset = i * 2 * barw / num + barw / num - barw;
	}
	
	var clsname = name.replace(":","").replace(",","");
	var ebar = 
		graph.selectAll('g.'+clsname)
				.data(errorbars)
			.enter().append("g")
				.attr("class", "errorbar "+clsname)
				.attr("transform", function(d) { return "translate({0},{1})".format(xaxis( d.x ), yaxis( d.y )) });
	
	ebar.append("line")
		.attr("class", "bar")
		.attr("x1", offset)
		.attr("x2", offset)
		.attr("y1", function(d){ return yaxis(d.y + d.s) - yaxis(d.y) })
		.attr("y2", function(d){ return yaxis(d.y - d.s) - yaxis(d.y) })
		.style("stroke", color)
        .style("stroke-width", "2px");
		
	ebar.append("line")
		.attr("class", "end")
		.attr("x1", -5 + offset)
		.attr("x2", 5 + offset)
		.attr("y1", function(d){ return yaxis(d.y + d.s) - yaxis(d.y) })
		.attr("y2", function(d){ return yaxis(d.y + d.s) - yaxis(d.y) })
		.style("stroke", color)
        .style("stroke-width", "2px");
	
	ebar.append("line")
		.attr("class", "end")
		.attr("x1", -5 + offset)
		.attr("x2", 5 + offset)
		.attr("y1", function(d){ return yaxis(d.y - d.s) - yaxis(d.y) })
		.attr("y2", function(d){ return yaxis(d.y - d.s) - yaxis(d.y) })
		.style("stroke", color)
        .style("stroke-width", "2px");
	
}

function addAxes(graph, title, xlabels, ylabels, xaxis, yaxis, rotate) {
	
	var xrange = xaxis.range()
	var yrange = yaxis.range()
	
	graph.append('svg:line')
		.attr('class', 'axis')
		.attr('y1', Array.min(yrange) )
		.attr('y2', Array.max(yrange) )
		.attr('x1', Array.min(xrange) )
		.attr('x2', Array.min(xrange) )
	    .style('fill', "black")
	    .style('stroke', "black")
	    .style('stroke-width', "1px");

	graph.append('svg:line')
		.attr('class', 'axis')
		.attr('y1', Array.max(yrange) )
		.attr('y2', Array.max(yrange) )
		.attr('x1', Array.min(xrange) )
		.attr('x2', Array.max(xrange) )
	    .style('fill', "black")
	    .style('stroke', "black")
	    .style('stroke-width', "1px");
	

	var ticks = 
		graph.selectAll('.ytick')
			.data(ylabels)
		.enter().append('svg:g')
			.attr('transform', function(d) { return "translate("+xaxis(0)+", "+yaxis(d)+")" })
			.attr('class', 'tick');

	ticks.append('svg:line')
		.attr('y1', 0)
		.attr('y2', 0)
		.attr('x1', 0)
		.attr('x2', 5)
	    .style('fill', "black")
	    .style('stroke', "black");

	ticks.append('svg:text')
		.text(function(d) { return d; })
		.attr('text-anchor', 'end')
		.attr('y', 2)
		.attr('x', -4)
	    .style('font-size', "9pt");
	
	ticks = 
		graph.selectAll('.xtick')
			.data(xlabels)
		.enter().append('svg:g')
			.attr('transform', function(d) { return "translate("+xaxis(d)+", "+yaxis(0)+")" })
			.attr('class', 'tick');
	
	ticks.append('svg:line')
		.attr('y1', -5)
		.attr('y2', 0)
		.attr('x1', 0)
		.attr('x2', 0)
	    .style('fill', "black")
	    .style('stroke', "black");
	
	var titleoffset = 30;
	
	if(rotate){
		ticks.append('svg:g')
			.attr("transform", "rotate(90)")
			.append('svg:text')
				.text(function(d) { return d; })
				.attr('text-anchor', 'start')
				.attr('y', 4)
				.attr('x', 4);
		
		titleoffset = 60;
	}
	else{
		ticks.append('svg:text')
			.text(function(d) { return d; })
			.attr('text-anchor', 'end')
			.attr('y', 12)
			.attr('x', 4)
            .style('font-size', "9pt");
	}
	
	var xm = ( Array.max(xrange) + Array.min(xrange) ) / 2
	graph.append('svg:text')
		.text(title)
		.attr('class', "label")
		.attr('x', xm)
		.attr('y', yaxis(0) + titleoffset + 6 )
	    .style("fill","black")
	    .style("font-size","12pt")
	    .style("text-anchor","middle");
}

function createGraph(parent, title, w, h, margin) {
	var graph = 
		parent 
			.append("svg")
			.attr("class", "graph")
            .style('font-family', "helvetica,arial,verdana")
			.attr("width", w)
			.attr("height", h);

	graph.append('svg:text')
		.text(title)
		.attr('class', "title")
		.attr('x', w/2)
		.attr('y', margin/2)
	    .style("fill","black")
	    .style("font-size","14pt")
	    .style("text-anchor","middle");
	
	return graph;
}
