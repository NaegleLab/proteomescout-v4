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










function createGOMap(json_data, blank){
    var r = 720,
	    node,
        root;
    var foreground_color = "#000";
    var background_color = "#BBB";
    
    var view_limit = 60;
    var id_size = 36;
    var term_size = 28;
    var fudge_factor = 0.1

    // var isNodeVisible = function(d, k) {
	// 	if(k===undefined)
	// 		k = 1;
	// 	return d.data.children.length != 0 && k * d.r > (view_limit - fudge_factor) && k * d.r <= ( r / 2 + fudge_factor );
    // };

    
    var isNodeVisible = function(d, k) {
		if(k===undefined)
			k = 1;
		return d.data.children.length != 1 && k * d.r > (view_limit - fudge_factor) && k * d.r <= ( r / 2 + fudge_factor );
	};
	
	var isNodeForeground = function(d, parent){
		return d == parent || $.inArray(d, root.children) > -1;
	};

    ////////////////////////////////////////////////////////////// 
    //////////////////Load the Data into JSON ////////////////////
    ////////////////////////////////////////////////////////////// 
    F_node = compileNode("Molecular Function", json_data.F);
	P_node = compileNode("Biological Process", json_data.P);
    C_node = compileNode("Cellular Component", json_data.C);
    data = {'GO':"", 'term':"GO Terms", 'value':json_data.total, 'children':[F_node, P_node, C_node]};

    ////////////////////////////////////////////////////////////// 
    ////////////////// Create GO MAP packing ////////////////////
    ////////////////////////////////////////////////////////////// 
    var svg = d3.select("#go_map_chart"),
        margin = 20,
        diameter = +svg.attr("width"),
        g = svg.append("g").attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

    var color = d3.scaleLinear()
        .domain([-1, 5])
        .range(["hsl(180,60%,100%)", "hsl(200,60%,40%)"])
        .interpolate(d3.interpolateHcl);

    var pack = d3.pack()
        .size([diameter - margin, diameter - margin])
        .padding(2);

    var tooltip = d3.select("#GO_map")
        .append("div")
        .attr('class', 'd3-tip')
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden")

    
        
    tooltip.append('div')
        .attr('id', 'go_id');
    
    tooltip.append('div')
        .attr('id', 'go_term');

    


    root = d3.hierarchy(data)
        .sum(function(d) { return d.value; })
        .sort(function(a, b) { return b.value - a.value; });

    var focus = root,
        nodes = pack(root).descendants(),
        view;

    
    ////////////////////////////////////////////////////////////// 
    //////////////////Add Circles for Go Terms////////////////////
    ////////////////////////////////////////////////////////////// 
    var circle = g.selectAll("circle")
        .data(nodes)
        .enter().append("circle")
        .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
        // .style("fill", function(d) { return d.children ? color(d.depth) : color(d.depth); })
        .attr("title", function(d) { return getNodeTitle(d.data); })
        .style("fill", function(d) { return d.children ? "#1f77b4" : "#1f77b4"; })
        .style("stroke", function(d) { return d.children ? "steelblue" : "steelblue"; })
        .style("fill-opacity", function(d) { return d.children ? .2 : .60; })
        .on("click", function(d) { if (focus !== d) zoom(d), d3.event.stopPropagation(); })
        .on("mouseover", function(d){
            
            tooltip.style("visibility", "visible");
            tooltip.style('display', 'block');
            tooltip.select('#go_id').text(d.data.GO);
            tooltip.select('#go_term').text(d.data.term);
        })
	    .on("mousemove", function(){return tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px");})
	    .on("mouseout", function(){return tooltip.style("visibility", "hidden");});
        ;

    ////////////////////////////////////////////////////////////// 
    //////////////////Add Text to GO Circles ////////////////////
    ////////////////////////////////////////////////////////////// 
    var go_text = g.selectAll("text")
        .data(nodes)
        .enter().append("text")
        .attr("class", "label")
        // .style("fill", function(d){ return isNodeForeground(d.data) ? foreground_color : background_color})
        .style("fill", function(d){ return d.parent === focus ? foreground_color : background_color})
        // .style("fill-opacity", function(d) { return visibleNodeText(d) ? 0 : 0; })
        .style("display", function(d) { return d.parent === root ? "inline" : "inline"; })
        .style("font-weight", "bold")
        .append("tspan")
            .attr("dy", -10)
            .attr("x", 0)
            .style("fill-opacity", function(d) { return isNodeVisible(d) ? 1 : 0; })
            .style("fill", function(d){ return isNodeForeground(d) ? foreground_color : background_color})
            .text(function(d) { return d.data.GO; })
        .append("tspan")
            .attr("dy", 10)
            .attr("x", 0)
            .style("fill-opacity", function(d) { return isNodeVisible(d) ? 1 : 0; })
            .style("fill", function(d){ return isNodeForeground(d) ? foreground_color : background_color})
            .text(function(d) { return d.data.term; })
        ;


    var node = g.selectAll("circle,text");

    svg
        // .style("background", color(-1))
        .on("click", function() { zoom(root); });


    zoomTo([root.x, root.y, root.r * 2 + margin]);

    function zoom(d) {
        var focus0 = focus; focus = d;

        var transition = d3.transition()
            .duration(d3.event.altKey ? 7500 : 750)
            .tween("zoom", function(d) {
            var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin]);
            return function(t) { zoomTo(i(t)); };
            });

        transition.selectAll("text")
        .filter(function(d) { return d.parent === focus || this.style.display === "inline"; })
            .style("fill-opacity", function(d) { return d.parent === focus ? 1 : 0; })
            .on("start", function(d) { if (d.parent === focus) this.style.display = "inline"; })
            .on("end", function(d) { if (d.parent !== focus) this.style.display = "none"; });
    }

    function zoomTo(v) {
        var k = diameter / v[2]; view = v;
        node.attr("transform", function(d) { return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")"; });
        circle.attr("r", function(d) { return d.r * k; });
    }


    
    

} 

