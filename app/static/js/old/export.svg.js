function displayStringData(mimetype, data) {
    var b64 = Base64.encode(data);
    window.open("data:{0};base64,\n{1}".format(mimetype, b64));
}

function displaySVG(id) {
	var svgml = $(id).html();
    svgml = svgml.replace(/#zoomgrad/g, "url(#zoomgrad)");
    svgml = svgml.replace(/<br>/g, " ")
    displayStringData("image/svg+xml", svgml);
}

function exportSVG(chart){
	var id = "#" + chart.attr('id');
	
	if($(id + " svg style").size() == 0){
		
		css_url = $("#graph_css_export_url").text()
		
		$.get(css_url,
			function(data) {
				$(id + " svg").append("<style>" + data + "</style>");
				displaySVG(id);
			}
		).error(function() {
			alert("Request ERROR: unable to load stylesheet. Please try again.")
		});
		
	} else {
		displaySVG(id);
	}
}

function processRunData(run, experiment_data, data_columns, data_map) {
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

    for(var i in points){
        data_columns["{0}".format(points[i].label)] = 0;
    }

    var isTime = true;
    for(var i in points){
        isTime = isTime && isNumber( points[i].label );
    }

    var metadata = {'name':name, 'isTime':isTime, 'axis': units};
	data_map[peptides] = {'points':points, 'stddev':stddev};

    return metadata;
}

function convertChartDataToTSV(data_columns, data_map, data_metadata){
    var column_headers = [];
    for(var c in data_columns){
        if(data_metadata.isTime)
            c = parseFloat(c);
        column_headers.push(c);
    }
    column_headers.sort(function (a, b) { return a-b; });
    
    var pre_header="";
    var post_header="";
    for(var i in column_headers){
        var header = column_headers[i];
        pre_header += "\t{0}".format(header);
        post_header += "\t{0}_stddev".format(header);
    }

    var TSV_data = pre_header + post_header + "\n"
    for(var label in data_map){
        TSV_data += "{0}".format(label);

        var points = data_map[label].points;
        var stddev = data_map[label].stddev;

        var pre_data="";
        var post_data="";

        for(var i in column_headers){
            var x_label = column_headers[i];
            var point_val="";
            var stddev_val="";

            for(var j in points){
                if(points[j].label == x_label) point_val = points[j].y;
            }
            for(var j in stddev){
                if(stddev[j].label == x_label) stddev_val = stddev[j].dev;
            }
            if(point_val == "None")
                point_val = "";
            if(stddev_val == "None")
                stddev_val = "";
            pre_data += "\t{0}".format(point_val);
            post_data += "\t{0}".format(stddev_val);
        }

        TSV_data += pre_data + post_data + "\n";
    }

    displayStringData("text/tab-separated-values", TSV_data);
}

function exportChartData(experiment_data) {
    var data_columns = {};
    var data_map = {};
    var data_metadata = {};

	d3.select(experiment_data)
		.selectAll(".run")
		.each(function() { data_metadata = processRunData(this, experiment_data, data_columns, data_map); });

    convertChartDataToTSV(data_columns, data_map, data_metadata);
}

function addExportChartData(experiment_data, container) {
 	container
        .select("div.absolute-lr")
        .append('button')
            .text("Export Data")
            .style("margin-left", "10px")
            .on('click', function() { exportChartData(experiment_data) });
}

var export_num = 0;

function addExportSVG(parent, container) {
	var svg = 
		parent.select('svg')
			.attr('version', "1.1")
			.attr('xmlns', "http://www.w3.org/2000/svg");
	
	parent.attr('id', "chart" + export_num);
	export_num++;
	
	container
		.style('text-align', "right")
		.append('div')
			.attr('class', 'absolute-lr')
            .style('z-index', "999")
			.append('button')
				.text("Export SVG")
				.on('click', function() { exportSVG(parent) });
}
