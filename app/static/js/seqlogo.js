function createSeqlogo(node, data, w, h){
	
	if(data.frequencies.length == 0)
		return;
	
	container = 
		node.append('div')
			.style('position', "relative")
			.style('display', "inline-block");
	
	chartContainer =
		container.append('span');
	
	chart =
		chartContainer.append("svg")
			.attr("class", "seqlogo")
			.attr("width", w)
			.attr("height", h+20)
            .style("font-family", "\"Lucida Console\", Monaco, monospace");
	
	total = data.total;
	total_columns = data.frequencies.length;
	cw = w / total_columns;
	ch = (h - 20) / 12;
	
	colors = create_amino_acid_colors();
	

	columns = 
		chart.selectAll("g.column")
			.data(data.frequencies)
		.enter().append("g")
			.attr("class", "column")
			.attr("transform", function(d, i) { return "translate("+ parseFloat(i) * cw +",0)" })
			// .attr("transform", function(d, i) { return "translate("+ i * cw +",0)" })
			// .attr("transform", function(d, i) { return "translate({0},0)".format(parseInt(i) * cw) })

	
	entry = 
		columns.selectAll("g.residue")
				.data(function(d){ return d.f; })
			.enter().append("g")
				.attr("class", "residue")
				.attr("transform", function(d, i) { return "translate(0,"+ ((d[2] / total * h) + 10 )   +")scale(1.0,"+d[1] / total * h / ch +")" })
				// .attr("transform", function(d, i) { return "translate(0, {0})scale(1.0,{1})".format( (d[2] / total * h) + 10 , d[1] / total * h / ch) });

    entry.append("text")
	    .attr("text-anchor", "middle")
	    .attr("x", cw/2)
	    .attr("y", ch - (ch/50))
        .style("font-family", "\"Arial\", Helvetica, sans-serif")
	    .style("font-size", 13.5 * (ch / 10) + "px")
	    .style("fill", function(d, i) { return colors(d[0]) })
	    .text(function(d) { return d[0] });
    
    // addExportSVG(chartContainer, container);
}
