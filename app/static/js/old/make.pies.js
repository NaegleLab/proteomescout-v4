$(document).ready(function() {
	var num = 1;
	
	d3.selectAll(".data_table")
		.each(function(){
			makeTableCollapsable(d3.select(this), 3, 10);
		});
	
	d3.selectAll(".data_chart")
		.each(function() {
			json_base64 = 
				d3.select(this)
					.select(".data")
					.text();
			
			data = JSON.parse(Base64.decode(json_base64));
			
			ndata = []
			for(i = 0; i < data.length && i < 10; i++){
				elem = data[i];
				data[i] = {};
				data[i].label = elem[0];
				data[i].x = elem[1];
				ndata.push(data[i])
			}
			
			var div = d3.select(this)
							.append('div')
								.style('display', "inline-block")
								.style('position', "relative");
			var span = div.append('span');
			
			createPieChart(span, ndata, 450, 400);
			addExportSVG(span, div);
			num+=1;
		});

	d3.selectAll(".data_chart_pie_legend")
		.each(function() {
			json_base64 = 
				d3.select(this)
					.select(".data")
					.text();
			
			data = JSON.parse(Base64.decode(json_base64));
			
			ndata = []
			for(i = 0; i < data.length && i < 10; i++){
				elem = data[i];
				data[i] = {};
				data[i].label = elem[0];
				data[i].x = elem[1];
				ndata.push(data[i])
			}
			
			var div = d3.select(this)
							.append('div')
								.style('display', "inline-block")
								.style('position', "relative");
			var span = div.append('span');
			
			createPieChartWithLegend(span, ndata, 425, 400);
			addExportSVG(span, div);
			num+=1;
		});

});
