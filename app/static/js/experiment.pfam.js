
$(document).ready(function() {
    $('#pfam_site_table').DataTable();
    $('#pfam_domain_table').DataTable();

    const pfamdata = document.querySelector('#pfam_data');


    site_data = JSON.parse(pfamdata.dataset.sites);
    site_tree = {children: site_data}
    domain_data = JSON.parse(pfamdata.dataset.domains);
    domain_tree = {children: domain_data}

   

    site_tree_chart = d3.select("#site_tree_chart")
    site_bar_chart = d3.select("#site_bar_chart")

    domain_tree_chart = d3.select("#domain_tree_chart")
    domain_bar_chart = d3.select("#domain_bar_chart")


    // $("#pfam-sites").text(JSON.stringify(site_data));
    // $("#pfam-domains").text(domain_data);
    barChart(site_bar_chart, site_data.slice(0,10),'name', 'value', 450,450);
    treemap(site_tree_chart, site_tree,'name', 'value',450,450);

    barChart(domain_bar_chart, domain_data.slice(0,10),'name', 'value',450,450);
    treemap(domain_tree_chart, domain_tree,'name', 'value',450,450);


} );