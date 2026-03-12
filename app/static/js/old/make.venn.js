function firstWord(str){
    str = str.split(' ')[0];
    str = str.replace(':','');
    str = str.replace('-','');
    return str;
}

$(document).ready(function() {
	var num = 1;
	
	d3.selectAll(".data_chart_venn_legend")
		.each(function() {
			json_base64 = 
				d3.select(this)
					.select(".data")
					.text();
			
			var data = JSON.parse(Base64.decode(json_base64));
			var div = d3.select(this)
							.append('div')
								.style('display', "inline-block")
								.style('position', "relative");
			var span = div.append('span');

            for(var i in data.sets){
                data.sets[i].label = firstWord(data.sets[i].label)
            }

            var sets = venn.venn(data.sets, data.overlaps);

            venn.drawD3Diagram(span, sets, 450, 400);
			addExportSVG(span, div);
			num+=1;
		});
});
