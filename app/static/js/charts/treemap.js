function treemap(container,  data, name, value, width, height){
    var margin = {top: 10, right: 10, bottom: 10, left: 10},
        width = width - margin.left - margin.right,
        height = height - margin.top - margin.bottom;
    
        var maxNameLength = 0;
        data.children.forEach(d=>{
            if(d[name].length>maxNameLength)
                maxNameLength =d[name].length
        });

    // var fader = function(color) { return d3.interpolateRgb(color, "#fff")(0.2); },
    //     color = d3.scaleOrdinal(d3.schemeCategory20.map(fader)),
    //     format = d3.format(",d");
    color = d3.scaleOrdinal(d3.schemeCategory10)
    
    // append the svg object to the body of the page
    var svg = container
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");
    
    var tooltip = d3.select('body')
        .append("div")
        .attr('class', 'd3-tip')
        .style('width', maxNameLength*10 + 'px')
        // .style("position", "absolute")
        // .style("z-index", "10")
        // .style("visibility", "hidden")
    
    
    
        
            
                
    tooltip.append('div')
        .attr('id', 'name');
    
    tooltip.append('div')
        .attr('id', 'value');
    
    // Give the data to this cluster layout:
  var root = d3.hierarchy(data).sum(function(d){ return d[value]}) // Here the size of each leave is given in the 'value' field in input data

  // Then d3.treemap computes the position of each element of the hierarchy
  d3.treemap()
    .size([width, height])
    .padding(2)
    (root)

  // use this information to add rectangles:
  svg
    .selectAll("rect")
    .data(root.leaves())
    .enter()
    .append("rect")
      .attr('x', function (d) { return d.x0; })
      .attr('y', function (d) { return d.y0; })
      .attr('width', function (d) { return d.x1 - d.x0; })
      .attr('height', function (d) { return d.y1 - d.y0; })
      .style("stroke", "black")
    //   .style("fill", "steelblue")
      .attr("fill", d => { while (d.depth > 1) d = d.parent; return color(d.data.name); })
      .attr("fill-opacity", 0.6)
    // .style("background", (d) => color(d.parent.data[name]))
    //   .on("mousemove", function (d) {
    //     tool.style("left", d3.event.pageX + 10 + "px")
    //     tool.style("top", d3.event.pageY - 20 + "px")
    //     tool.style("display", "inline-block");
    //     tool.html(d[name]+ "<br>" + d[value]);
    // }).on("mouseout", function (d) {
    //     tool.style("display", "none");
    // });
      .on("mouseover", function(d){
            
        tooltip.style("visibility", "visible");
        tooltip.style('display', 'block');
        tooltip.select('#name').text(d.data[name]);
        tooltip.select('#value').text(d.data[value]);
    })
    .on("mousemove", function(){return tooltip.style("top", (d3.event.pageY-10)+"px").style("left",(d3.event.pageX+10)+"px");})
    
    // .on("mousemove", function(){return tooltip.style("top", d + "px").style("left",d+"px");})
    .on("mouseout", function(){return tooltip.style("visibility", "hidden");});

  // and to add the text labels
  svg
    .selectAll("text")
    .data(root.leaves())
    .enter()
    .append("text")
      .attr("x", function(d){ return d.x0+5})    // +10 to adjust position (more right)
      .attr("y", function(d){ return d.y0+20})    // +20 to adjust position (lower)
      .text(function(d){ return d.data[name] })
      .attr("font-size", "15px")
      .attr("fill", "white")
    //   .style('opacity', function(d) {
    //       var bbox = this.getBBox();
    //       if ( d.dx <= bbox.width  || d.dy <= bbox.height  ) {
    //         return 0;
    //       }
    //       return 1;
    //   }
    //   )
    svg.selectAll('text')
      .style('opacity', function(d) {
        var bbox = this.getBBox();
        if ( d.dx <= bbox.width + 10  || d.dy <= bbox.height + 11  ) {
          return 0;
        }
        return 0;
    }
    )
    // selection.selectAll('text')
    //   .transition(t)


}