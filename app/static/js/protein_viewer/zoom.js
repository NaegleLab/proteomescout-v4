function ZoomWindow(structure_viewer, svg_container, residue, width, height) {
    this.parent_viewer = structure_viewer;
    this.residue = residue;
    this.width = width;

    this.height = height-100;
    this.minwidth = 50;

    var axis = structure_viewer.axis;
    var zoomer = this;

    this.winselector = "rect.zoom.window";
    this.expselector = "path.expander";
    this.zoom_window =
        svg_container
                .insert('rect', ":first-child")
                    .attr('class', "zoom window")
                    .attr('x', axis(this.residue))
                    .attr('width', axis(width))
                    .attr('y', 0)
                    .attr('height', this.height+50)
                    .style('fill', "#666666")
                    .style('opacity', "0.3");

    this.polygon_vertices = 
            [{"x":axis(this.residue),"y":50},
             {"x":axis(this.residue+width),"y":50},
             {"x":structure_viewer.width,"y":150},
             {"x":0,"y":150},
            ];

    this.line =
		d3.line()
			.x(function(d) { return d.x } )
			.y(function(d) { return d.y } )

    var gradient = svg_container.append("defs")
          .append("linearGradient")
              .attr("id", "zoomgrad")
              .attr("x1", "0%")
              .attr("y1", "0%")
              .attr("x2", "0%")
              .attr("y2", "100%")
              .attr("spreadMethod", "pad");

    gradient.append("stop")
            .attr("offset", "0%")
            .attr("stop-color", "#666")
            .attr("stop-opacity", 1.0);

    gradient.append("stop")
            .attr("offset", "100%")
            .attr("stop-color", "#666")
                .attr("stop-opacity", 0);

    this.gradient = gradient;
    this.expand_gradient =
        svg_container.selectAll('path.expander')
                .data([this.polygon_vertices])
            .enter().insert('path', ":first-child")
                .attr('class', "expander")
                .attr('transform', 'translate(0,{0})'.format(this.height))
                .attr('d', this.line)
                .style("opacity", '0.3')
                .style("fill", "url(#zoomgrad)");
};

ZoomWindow.prototype.animate_height = function(t, nheight, timedelay) {
    this.height=nheight-100;

    t = t.transition().delay(timedelay);

    t.select(this.winselector)
                .attrTween('height', d3.tween(this.height + 50, d3.interpolate));

    var ntransform = 'translate(0,{0})'.format(this.height)
    t.select(this.expselector)
                .attrTween('transform', d3.tween(ntransform, d3.interpolateTransform));
};

ZoomWindow.prototype.remove = function() {
    this.zoom_window.remove();
    this.gradient.remove();
    this.expand_gradient.remove();
}

ZoomWindow.prototype.update_window = function(residue, width, axis){
    this.residue = residue;
    this.width = width;

    nx = axis(this.residue);
    nw = axis(this.width);

    this.polygon_vertices[0].x = nx;
    this.polygon_vertices[1].x = nx+nw;

    this.expand_gradient.attr('d', this.line(this.polygon_vertices));
    this.zoom_window
        .attr('x', nx)
        .attr('width', nw);
}
