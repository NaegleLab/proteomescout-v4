$(document).ready( function (){
	
	data = JSON.parse($(".seqdata").text());
	
	$(".seqdata").text("");
	createSeqlogo(d3.select(".seqchart"), data, 400, 325);

	
});
