
$(document).ready(function() {
    $('#molfunc_table').DataTable();
    $('#cell_table').DataTable();
    $('#bioprocess_table').DataTable();

    const treedata = document.querySelector('#go_map_data');
	json_data = JSON.parse(treedata.dataset.gotree);
	
	container = d3.select("#GO_map")
				.append("div")
					.style('display', "inline-block")
					.style('position', "relative");
	
	span = container.append('span');

	createGOMap(json_data, span)


} );
