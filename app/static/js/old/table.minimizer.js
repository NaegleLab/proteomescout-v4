function makeTableCollapsable(table_container, max_cols, max_rows){
	if( table_container.selectAll("tr")[0].length <= max_rows ){
		return;
	}
	hideExcessRows(table_container.selectAll("tr"), max_rows);
	
	table_container.select("table")
		.append("tr")
		.attr("class", "expander")
			.append("td")
				.attr("colspan", max_cols)
				.append("button")
					.text("Expand Table")
					.on("click", function(){
						button = d3.select(this);
						rows = table_container.selectAll("tr")
						if(button.text() == "Expand Table"){
							expandRows(rows);
							button.text("Collapse Table");
						}
						else{
							hideExcessRows(rows, max_rows);
							button.text("Expand Table");
						}
					});
}

function hideExcessRows(rows, max) {
	var i=0;
	rows.each(function(){
		row = d3.select(this);
		if(i > max && row.attr("class") != "expander")
			row.style("display", "none");
		i+=1;
	});
}

function expandRows(rows) {
	rows.style("display", "table-row")
}