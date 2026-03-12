var probeCol = 0;
var collectionCol = 1;
var tissueCol = 2;
var levelCol = 3;

$(document).ready( function() {
	genCharts();
	
	$("#expression_probeid").change(function() { genCharts(); })
	$("#expression_collection").change(function() { genCharts(); })
} );

function parseLine(d, i) {
	var content = d3.select(this).text();
	ncontent = content.split(",");
	ncontent[levelCol] = parseFloat(ncontent[levelCol]);
	window.data.push(ncontent);
}

function parseData() {
	window.data = [];
	d3.selectAll(".expression_data div").each( parseLine );
}

function selectData(probe, collection) {
	selected = [];

	for(i in window.data){
		row = window.data[i];
		if(row[probeCol] == probe && (collection == 'all' || row[collectionCol] == collection)){
			selected.push([row[levelCol], row[tissueCol]]);
		}
	}
	
	return selected;
}

function maximumPt(selected_data) {
	max = -1000;
	for(i in selected_data){
		row = selected_data[i];
		if(row[0] > max){
			max = row[0];
		}
	}
	return max;
}

function split(array, peices) {
	size = array.length / peices;
					
	if(size * peices < array.length) size += 1;
	
	np = [];
	rval = [];
	
	for(i in array) {
		np.push(array[i]);
		
		if(np.length >= size){
			rval.push(np);
			np = [];
		}
	}
	
	if(np.length > 0){
		rval.push(np);																																																																										
	}
	
	return rval;
}


function genCharts() {
	parseData();
	d3.selectAll(".expression_chart td").remove();
	
	var cols = 2;
	
	var probeId = $("#expression_probeid :selected").attr("value");
	var collection = $("#expression_collection :selected").attr("value");
	
	data = selectData(probeId, collection);
	maxLevel = maximumPt(data);
	
	colData = split(data, cols);
	
	for(i in colData){
		generateExpressionChart(colData[i], maxLevel);
	}
}

function generateExpressionChart(data, maxLevel) {
	var width = 400;
	var height = data.length * 20;
	
	var chart = d3.select(".expression_chart tr").append("td").append("svg")
				.attr("width", width)
				.attr("height", height);
	
	var x = d3.scale.linear()
		.domain([0, maxLevel])
		.range([150, width-50]);
	
	var y = d3.scale.ordinal()
	    .domain(data)
	    .rangeBands([0, height]);
	
	chart.selectAll(".expression_level")
	     .data(data)
	   .enter().append("rect")
	     .attr("class", "expression_level")
	   	 .attr("x", x(0))
	     .attr("y", y)
	     .attr("width", function(d) { return x(d[0]) - x(0); })
	     .attr("height", y.rangeBand());

	chart.selectAll(".expression_float")
		.data(data)
	  .enter().append("text")
	    .attr("class", "expression_float")
	    .attr("x", function(d) { return x(d[0]) + 10; })
	    .attr("y", function(d) { return y(d) + y.rangeBand() / 2;})
	    .attr("dx", -3) // padding-right
	    .attr("dy", ".35em") // vertical-align: middle
	    .text(function(d) { return d[0].toFixed(2); });
	
	chart.selectAll(".expression_tissue")
	     .data(data)
	   .enter().append("text")
	   	 .attr("class", "expression_tissue")
	     .attr("x", x(0))
	     .attr("y", function(d) { return y(d) + y.rangeBand() / 2;})
	     .attr("dx", -3) // padding-right
	     .attr("dy", ".35em") // vertical-align: middle
	     .attr("text-anchor", "end") // text-align: right
	     .text(function(d) { return d[1]; });
	
	chart.append("line")
		 .attr("x1", x(0))
		 .attr("x2", x(0))
	     .attr("y1", 0)
	     .attr("y2", height)
	     .style("stroke", "#000");
}
