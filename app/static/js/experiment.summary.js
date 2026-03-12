$(document).ready( function (){
	const seq_data = document.querySelector('#seqdata');
	data = JSON.parse(seq_data.dataset.seq);
	// data = JSON.parse($(".seqdata").text());
	
	
	createSeqlogo(d3.select("#seqchart"), data, 400, 325);


	
});
