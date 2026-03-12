
$(document).ready(function() {

    var scan_data = document.querySelector('#scansite-data');

    var bind_data = JSON.parse(scan_data.dataset.bind);
    var kinase_data = JSON.parse(scan_data.dataset.kinase);

    bind_treedata = {children: bind_data}
    kinase_treedata = {children: kinase_data}

    var bind_chart = d3.select("[id='barchart-Scansite Bind']")
    var kinase_chart = d3.select("[id='barchart-Scansite Kinase']")

    var bind_treemap = d3.select("[id='treemap-Scansite Bind']")

    var kinase_treemap = d3.select("[id='treemap-Scansite Kinase']")

    var height = 500
    var width = 500
    barChart(bind_chart, bind_data.slice(0,10),'name', 'value', width,height);
    barChart(kinase_chart, kinase_data.slice(0,10),'name', 'value', width,height);

    treemap(bind_treemap, bind_treedata,'name', 'value',width, height);
    treemap(kinase_treemap, kinase_treedata,'name', 'value',width, height);
    
    $("[id='Scansite Kinase']").DataTable({
        "order":[[2,'desc']]
    });
    
    $("[id='Scansite Bind']").DataTable(({
        "order":[[2,'desc']]
    }));

} );