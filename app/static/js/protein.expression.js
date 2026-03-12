$(document).ready( function (){
    const data_loc = document.querySelector('#expdata')
    all_data = data_loc.dataset.all


    genCharts(all_data);
    $("#expression_probeid").change(function() { genCharts(all_data); })
    $("#expression_collection").change(function() { genCharts(all_data); })
});

function selectData(probe, collection, data){
    var selected = [];
    for(i in data){
        row = data[i];
        if(row.probeset == probe && (collection == 'all' || row.collection == collection)){
            // selected.push({'name':row['tissue'], 'value':row['value']});
            selected.push(row)
		}
    }
    return selected;
}

function genCharts(data) {
    var probeId = $("#expression_probeid option:selected").text();
    var collection = $("#expression_collection option:selected").text();
    data = selectData(probeId, collection, JSON.parse(data));
    var count = data.length
    container = d3.select("#expression_chart")
    width = document.getElementById("expression_chart").offsetWidth
    // obarChart(container,  data, 'tissue','value',500, 500, 'horizkkontal', 'hellow')
    hbarChart(container, data, 'tissue','value',width, count*20)

}