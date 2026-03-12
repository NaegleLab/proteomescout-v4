function barChart(container,  dataset, name, value, width, height){

    var margin = {top: 40, right: 30, bottom: 30, left: 50};
    
    var width = width - margin.left - margin.right,
        height = height - margin.top - margin.bottom;

    var svg = container.append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", 
                "translate(" + margin.left + "," + margin.top + ")");

    // X Axis
    var x = d3.scaleBand()
        .range([0, width])
            .padding(0.4);
    

    var xAxis = d3.axisBottom(x).tickSize([]).tickPadding(10);
    
    x.domain(dataset.map( d => { return d[name]; }));

    var gXAxis = svg.append("g")
		.attr("class", "x axis")
		.call(xAxis);
	gXAxis.selectAll("text")
		.style("text-anchor", "end")
		.attr("dx", "-.8em")
		.attr("dy", ".15em")
		.attr("transform", "rotate(-65)");

	// Find the maxLabel height, adjust the height accordingly and transform the x axis.
    var maxWidth = 0;
    
	gXAxis.selectAll("text").each(function () {
		var boxWidth = this.getBBox().width;
		if (boxWidth > maxWidth) maxWidth = boxWidth;
	});
	height = height - maxWidth;

	gXAxis.attr("transform", "translate(0," + height + ")");
    
    // Y Axis
    var y = d3.scaleLinear()
        .range([height, 0]);
    var yAxis = d3.axisLeft(y).tickSize([]);
    y.domain([0, d3.max(dataset, function(d) { return d[value]; })]);
    
    var gYAxis = svg.append("g")
        .attr("class","y axis")
        .call(yAxis);

    
    // Add Bars to Bar Chart
    svg.selectAll(".bar")
        .data(dataset)
        .enter().append("rect")
        
        .attr("class", "bar")
        .style("display", d => { return d[value] === null ? "none" : null; })
        .style("fill","steelblue")
        .attr("x",  d => { return x(d[name]); })
        .attr("width", x.bandwidth())
            .attr("y",  d => { return height; })
            .attr("height", 0)
                .transition()
                // .duration(750)
        .attr("y",  d => { return y(d[value]); })
        .attr("height",  d => { return height - y(d[value]); });
}




function hbarChart(container, data, name, value, width, height){

    var maxNameLength = 0;
    var maxSize = 0;
    data.forEach(d=>{
        if(d[name].length>maxNameLength)
            maxNameLength =d[name].length
        if(d[value].toString().length >maxSize )
            maxSize =d[value].toString().length
    });
    



    var margin = {top: 20, right: 30 + 10*maxSize, bottom: 30 + 10*maxSize, left: 100 + maxNameLength*5},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    container.selectAll("*").remove();
    
    var svg = container
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");

    // Add X axis
    var x = d3.scaleLinear()
        .domain([0, d3.max(data, function(d) { return d[value]; })])
        .range([ 0, width]);
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
            .attr("transform", "translate(-10,0)rotate(-45)")
            .style("text-anchor", "end");
    
    // Y axis
    var y = d3.scaleBand()
        .range([ 0, height ])
        .domain(data.map(function(d) { return d[name]; }))
        .padding(.1);
    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y))

    //Bars
    bars = svg.selectAll(".bar")
        .data(data)
        .enter()
        .append("g")

    bars.append("rect")
        .attr("x", x(0) )
        .attr("y", function(d) { return y(d[name]); })
        .attr("width", function(d) { return x(d[value]); })
        .attr("height", y.bandwidth() )
        .attr("fill", "#008c96")
    
    //add a value label to the right of each bar
    bars.append("text")
        .attr("class", "clabel")
        //y position of the label is halfway down the bar
        .attr("y", function (d) {
            return y(d[name]) + y.bandwidth() / 2 + 4;
        })
        //x position is 3 pixels to the right of the bar
        .attr("x", function (d) {
            return x(d[value]) + 3;
        })
        .text(function (d) {
            return d[value];
        });



            


}



function  obarChart(container,  dataset, name, value, width, height, orientation='vertical', title=''){

    var svg,
    canvasHeight = 400,
    canvasWidth = 800,
    chartData = [],
    gPrimary,
    gXAxis,
    gYAxis;

    var config = {
        axes: {
            x: null,
            y: null
        },
        chartOrientation: 'vertical',
        // colorScale: d3.scaleOrdinal().range(d3.schemeCategory20),
        margins: {
            top: 30,
            right: 30,
            bottom: 30,
            left: 75
        },
        maxBarWidth: 40,
        metrics: {
            x: name,
            y: value
        },
        scales: {
            x: null,
            y: null
        },
        transitionDurations: {
            bars: 750,
            axes: 500
        }
    };

    if(orientation == 'horizontal') {
        config.margins.left = 125;
        config.metrics.x = value;
        config.metrics.y = name;
    } else {
        config.margins.left = 75;
        config.metrics.y = value;
        config.metrics.x = name;
    }
    canvasHeight = height,
    canvasWidth = width,
    chartData = dataset;

    initChart(container);
    setScales();
    handleBars();
    callAxes();

    setScales();
	callAxes();
	handleBars();

    gPrimary.append('text')
				.attr('x', function() {
					return (canvasWidth - config.margins.left - config.margins.right)/2;
				})
				.attr('y', function() {
					return config.margins.top * .5;
				})
				.style('font-size', '12px')
				.style('font-weight', 'bold')
				.style('text-anchor', 'middle')
                .text(title);
    


    
    /**
     * @function
     * @description Initialize chart components
     */
    function initChart(container) {
        container.selectAll("*").remove();
        svg = container
            .append('svg')
            .attr('width', canvasWidth)
            .attr('height', canvasHeight);

        gPrimary = svg.append('svg:g');

        gXAxis = svg.append('svg:g')
            .attr('class', 'axis')
            .attr('transform', function() {
                var x = config.margins.left, y = canvasHeight - config.margins.bottom;
                return 'translate(' + x + ',' + y + ')';
            });

        gYAxis = svg.append('svg:g')
            .attr('class', 'axis')
            .attr('transform', function() {
                var x = config.margins.left, y = 0;
                return 'translate(' + x + ',' + y + ')';
            });
    }

    function handleBars() {

        gPrimary.attr('transform', function() {
            var x = config.margins.left, y = 0;
            return 'translate(' + x + ',' + y + ')';
        });

        //////////////////////////////
        // rectangles - JRAT
        // (join, remove, append, transition)
        //////////////////////////////
        var rectSelection = gPrimary.selectAll('rect')
            .data(chartData);

        rectSelection.exit().remove();

        rectSelection.enter()
            .append('rect')
            .style('opacity', .8)
            .style('stroke', 'black')
            .style('stroke-width', 1)
            .attr('rx', 3)
            .attr('ry', 3)
            .on('mouseover', function(d, i) {
                d3.select(this).style('opacity', 1);
                gPrimary.selectAll('rect').filter(function(e, j) {
                    return i != j;
                }).style('opacity', .2);
            })
            .on('mouseout', function(d, i) {
                gPrimary.selectAll('rect').style('opacity', .8);
            });

        if(config.chartOrientation == 'horizontal') {
            rectSelection.transition()
                .duration(config.transitionDurations.bars)
                .attr('x', function(d) {
                    return 0;
                })
                .attr('y', function(d) {
                    return config.scales.y(d[config.metrics.y]);
                })
                .attr('width', function(d) {
                    return config.scales.x(d[config.metrics.x]);
                })
                .attr('height', function(d) {
                    return Math.min(config.scales.y.bandwidth(), config.maxBarWidth);
                })
                .attr('transform', function(d, i) {
                    var x = 0, y = 0;
                    if(config.maxBarWidth < config.scales.y.bandwidth()) {
                        y = (config.scales.y.bandwidth() - config.maxBarWidth)/2;
                    }
                    return 'translate(' + x + ',' + y + ')';
                })
                .style('fill', 'steelblue');
        } else {
            rectSelection.transition()
                .duration(config.transitionDurations.bars)
                .attr('x', function(d) {
                    return config.scales.x(d[config.metrics.x]);
                })
                .attr('y', function(d) {
                    return config.margins.top + config.scales.y(d[config.metrics.y]);
                })
                .attr('width', function(d) {
                    return Math.min(config.maxBarWidth, config.scales.x.bandwidth());
                })
                .attr('height', function(d) {
                    return canvasHeight - config.margins.bottom - (config.margins.top + config.scales.y(d[config.metrics.y]));
                })
                .attr('transform', function() {
                    if(config.maxBarWidth < config.scales.x.bandwidth()) {
                        var t = (config.scales.x.bandwidth() - config.maxBarWidth)/2;
                        return 'translate(' + t + ',0)';
                    }
                })
                .style('fill', 'steelblue');
        }
    }


    /**
     * @function
     * @description Wrapper function for setting V/H scales
     */
    function setScales() {
        if(config.chartOrientation == 'horizontal') {
            setHorizontalScales();
        } else {
            setVerticalScales();
        }
    }

    /** 
     * @function
     * @description Set horizontal scales...x=linear, y=ordinal
     */
    function setHorizontalScales() {

        // x scale (linear)
        config.scales.x = d3.scaleLinear()
            .domain([0, d3.max(chartData, function(d) { return d[config.metrics.x]; })])
            .range([0, canvasWidth - config.margins.left - config.margins.right])
            .nice();

        // x axis
        config.axes.x = d3.axisBottom(config.scales.x).tickSize([]).tickPadding(3);

        config.scales.y = d3.scaleBand()
            .rangeRound([config.margins.top, canvasHeight - config.margins.bottom])
            .padding(0.1);

        // y axis
        config.axes.y = d3.axisLeft(config.scales.y).tickSize([]).tickPadding(3);
    }

    /**
     * @function 
     * @description Set vertical scales...x=ordinal, y = linear
     */
    function setVerticalScales() {

        // x scale (ordinal)
        config.scales.x = d3.scaleBand()
            .rangeRound([0, canvasWidth - config.margins.left - config.margins.right])
            .padding(0.1)
        
        // d3.scaleOrdinal()
        //     .domain(chartData.map(function(m) {
        //         return m[config.metrics.x];
        //     }))
        //     .rangeRoundBands([0, canvasWidth - config.margins.left - config.margins.right], 0.08, 0.1);

        // x axis
        config.axes.x = d3.axisBottom(config.scales.x).tickSize([]).tickPadding(3);
        // config.axes.x = d3.svg.axis()
        //     .scale(config.scales.x)
        //     .tickSize(3)
        //     .tickPadding(3)
        //     .orient('bottom');

        // y scale (linear)
        config.scales.y = d3.scaleLinear()
            .domain([
                d3.max(chartData, function(d) { return d[config.metrics.y]; }),
                0
            ])
            .range([
                config.margins.top, canvasHeight - config.margins.bottom
            ])
            .nice();

        // y axis
        config.axes.y = d3.axisLeft(config.scales.y).tickSize([]).tickPadding(3);
        // config.axes.y = d3.svg.axis()
        //     .scale(config.scales.y)
        //     .tickSize(3)
        //     .tickPadding(3)
        //     .orient('left');
    }

    /**
     * @function
     * @description Call axis handlers
     */
    function callAxes() {
        gXAxis.transition()
            .duration(config.transitionDurations.axes)
            .attr('transform', function() {
                var x = config.margins.left, y = canvasHeight - config.margins.bottom;
                return 'translate(' + x + ',' + y + ')';
            })
            .call(config.axes.x);
                
        gYAxis.transition()
            .duration(config.transitionDurations.axes)
            .attr('transform', function() {
                var x = config.margins.left, y = 0;
                return 'translate(' + x + ',' + y + ')';
            })
            .call(config.axes.y);
    }



    

}






