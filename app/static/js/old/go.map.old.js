function compileNode(name, data){
	val = 0;
	for(i = 0; i < data.length; i++){
		val+=data[i].value;
	}
	return {'GO':name, 'term':"", 'value':val, 'children':data};
}

function getNodeTitle(d){
    subtitle = d.term == '' ? '' : ": " + d.term;
    if (d.GO != '') return d.GO + subtitle;
}

function createGOMap(json_data, container){
	var w = 940,
	    h = 800,
	    r = 720,
	    x = d3.scale.linear().range([0, r]),
	    y = d3.scale.linear().range([0, r]),
	    node,
	    root;
	
	var foreground_color = "#000";
	var background_color = "#BBB";
	
	var view_limit = 60;
	var id_size = 36;
	var term_size = 28;
    var fudge_factor = 0.1
	
	var pack = d3.layout.pack()
	    .size([r, r])
	    .value(function(d) { return d.value; })
	
	var vis = container.append("svg:svg")
		.attr("class", "GO")
	    .attr("width", w)
	    .attr("height", h)
        .style("background", "white")
	  .append("svg:g")
	    .attr("transform", "translate(" + (w - r) / 2 + "," + (h - r) / 2 + ")");
	

	F_node = compileNode("Molecular Function", json_data.F);
	P_node = compileNode("Biological Process", json_data.P);
	C_node = compileNode("Cellular Component", json_data.C);
	
	root = {'GO':"", 'term':"", 'value':json_data.total, 'children':[F_node, P_node, C_node]};
	
	node = root;

	var nodes = pack.nodes(root);

	
	var isNodeVisible = function(d, k) {
		if(k===undefined)
			k = 1;
		return d.children.length != 1 && k * d.r > (view_limit - fudge_factor) && k * d.r <= ( r / 2 + fudge_factor );
	};
	
	var isNodeForeground = function(d, parent){
		return d == parent || $.inArray(d, root.children) > -1;
	};
	
	vis.selectAll("circle")
    		.data(nodes)
    	.enter().append("svg:circle")
    		.attr("class", function(d) { return d.children ? "parent" : "child"; })
    		.attr("cx", function(d) { return d.x; })
    		.attr("cy", function(d) { return d.y; })
    		.attr("r", function(d) { return d.r; })
            .attr("title", function(d) { return getNodeTitle(d); })
            .style("fill", function(d) { return d.children ? "#1f77b4" : "#ccc"; })
            .style("stroke", function(d) { return d.children ? "steelblue" : "#999"; })
            .style("fill-opacity", function(d) { return d.children ? .2 : 1.0; })
    		.on("click", function(d) { return zoom(node == d ? root : d); });

	var getScaledSize = function(d, size, scale) {
		if(scale == undefined)
			return 2 * d.r / r * size;
		return (2 * (scale(d.y + d.r) - scale(d.y)) / r * size);
	};
	
	nodes = nodes.reverse()
	
	vis.selectAll("g.label")
    		.data(nodes)
    	.enter().append("g")
    		.attr("class", "label")
    		.each(function(d){
    			nodeclass = (d.children ? "parent" : "child");
    			textcolor = isNodeForeground(d) ? foreground_color : background_color;
    			textopacity = isNodeVisible(d) ? 1 : 0;
    			
    			d3.select(this)
	    			.append("svg:text")
			    		.attr("class", "id " + nodeclass )
			    	    .attr("x", d.x)
			    	    .attr("y", d.y)
			    		.attr("text-anchor", "middle")
			    		.style("fill", textcolor)
			    		.style("opacity", textopacity)
			    		.style("font-size", getScaledSize(d, id_size) + "px")
                        .style("font-weight", "bold")
			    		.text(d.GO);
    			
    			d3.select(this)
	    			.append("svg:text")
						.attr("class", "term " + nodeclass)
						.attr("x", d.x)
			    	    .attr("y", d.y)
			    		.attr("dy", getScaledSize(d, id_size))
			    		.attr("text-anchor", "middle")
			    		.style("fill", textcolor)
			    		.style("opacity", textopacity)
			    		.style("font-size", getScaledSize(d, term_size) + "px")
                        .style("font-weight", "bold")
			    		.text(d.term);
    		});

    d3.select("body").on("click", function() { zoom(root); });
	
	function zoom(d, i) {
	  var k = r / d.r / 2;
	  x.domain([d.x - d.r, d.x + d.r]);
	  y.domain([d.y - d.r, d.y + d.r]);
	  var parent = d;
	  var t = vis.transition()
	      .duration(d3.event.altKey ? 7500 : 750);
	
	  t.selectAll("circle")
	      .attr("cx", function(d) { return x(d.x); })
	      .attr("cy", function(d) { return y(d.y); })
	      .attr("r", function(d) { return k * d.r; });
	  
	  t.selectAll("text.id")
	      .attr("x", function(d) { return x(d.x); })
	      .attr("y", function(d) { return y(d.y); })
	      .style("fill", function(d) { return isNodeForeground(d, parent) ? foreground_color : background_color})
	      .style("opacity", function(d) { return isNodeVisible(d, k) ? 1 : 0; })
	      .style("font-size", function(d) { return getScaledSize(d, id_size, y) + "px" });
	  
	  t.selectAll("text.term")
	      .attr("x", function(d) { return x(d.x); })
	      .attr("y", function(d) { return y(d.y); })
	      .attr("dy", function(d) { return getScaledSize(d, id_size, y); })
	      .style("fill", function(d) { return isNodeForeground(d, parent) ? foreground_color : background_color})
	      .style("opacity", function(d) { return isNodeVisible(d, k) ? 1 : 0; })
	      .style("font-size", function(d) { return getScaledSize(d, term_size, y) + "px" });

	  
	  node = d;
	  d3.event.stopPropagation();
	}
}
	    
