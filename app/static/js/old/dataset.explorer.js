
function PValueCorrectedTable(parentElement, tableBody, tableData, byCategory, numTests){
	var widget = this;
	this.tableBody = tableBody;
    this.byCategory = byCategory;
    this.numTests = numTests;

	var div = $('<div />').appendTo(parentElement);
	$('<span>Mark as significant with p-value less than: </span>').appendTo(div);
	
	var last_val = "0.01";
	this.pvalueCutoff = $('<input />', {'value':last_val, 'type':"text",'length':"7"}).appendTo(div);
	this.pvalueCutoff.on('change', function(){
		var val = $(this).val();
		
		if(isNaN(parseFloat(val)) || !isFinite(val)){
			$(this).val(last_val);
		} else {
			last_val = val;
		}
	});
	
	this.setOptions = $('<button>Go</button>').appendTo(div);
	this.setOptions.on('click',function(){
		var cutoff_val = parseFloat(widget.pvalueCutoff.val());
		var correction = 'none'
		if(widget.bonferroniOption.is(":checked")){
			correction = 'bonferroni'
		}else if(widget.fdrOption.is(":checked")){
			correction = 'fdr'
		}
		
		widget.filter(cutoff_val, correction);
	});

	var field_name = "{0}-test-correction".format( getUniqueId() );
	
	div = $('<div />').appendTo(parentElement);
	this.noCorrectionOption = $('<input />', {'type':"radio", 'name':field_name, 'value':"none", 'checked':"checked"}).appendTo(div);
	$('<span />', {'text':"No test correction"}).appendTo(div);
	
	div = $('<div />').appendTo(parentElement);
	this.bonferroniOption = $('<input />', {'type':"radio", 'name':field_name, 'value':"bonferoni"}).appendTo(div);
	$('<span />', {'text':"Bonferroni correction"}).appendTo(div);
	
	div = $('<div />').appendTo(parentElement);
	this.fdrOption = $('<input />', {'type':"radio", 'name':field_name, 'value':"fdr"}).appendTo(div);
	$('<span />', {'text':"False Discovery Rate correction"}).appendTo(div);
	
	this.filter(parseFloat(last_val), 'none');
};

PValueCorrectedTable.prototype.calculateFDRCutoff = function(cutoff, rows, numTests){
	var i = 0;
	rows.each(function(){
		var pval_td = $(this).find(".pvalue");
		var pval = parseFloat(pval_td.attr('value'));
		
		if(cutoff * i / numTests >= pval){
			cutoff = pval;
		}
		
		i++;
	});
	
	return cutoff;
};

PValueCorrectedTable.prototype.applyCorrection = function(correction, cutoff, rows, numTests) {
    var corrected_cutoff = cutoff;
    if(correction == 'fdr')
        corrected_cutoff = this.calculateFDRCutoff(cutoff, rows, numTests);

	rows.each(function() {
		var pval_td = $(this).find(".pvalue");
		var val = pval_td.attr('value');
		var cval = val;
		
		if(correction == 'bonferroni'){
			cval = val * numTests;
			if(cval > 1.0){
				cval = 1.0;
			}
		}
		
		pval_td.text(parseFloat(parseFloat(cval).toPrecision(3)).toExponential());
		
		if(cval <= corrected_cutoff)
			$(this).addClass('significant');
		else
			$(this).removeClass('significant');
		
		if(val > cutoff)
			$(this).addClass('notsignificant');
		else
			$(this).removeClass('notsignificant');
	});
};

PValueCorrectedTable.prototype.filter = function(cutoff, correction) {
	var widget = this;
	
    if(widget.byCategory) {
        var rowClasses = {};

        this.tableBody.find('tr').each(function() {
            var clsName = $(this).attr('value');
            rowClasses[clsName] = 0;
        });

        for(var clsName in rowClasses){
            var rows = this.tableBody.find('tr[value="{0}"]'.format(clsName));
            this.applyCorrection(correction, cutoff, rows, rows.length);
        }

    }else{
        var rows = this.tableBody.find('tr');
        this.applyCorrection(correction, cutoff, rows, this.numTests);
    }
};

function EnrichmentTable(parentElement, tableData){
	var widget = this;

	this.tableElement = $('<table />', {'class':"enrichment-table"});
	$('<thead><tr><th>Category</th><th>Term</th><th width="50px">P-Value</th></tr></thead>').appendTo(this.tableElement);
	this.tbody = $('<tbody />').appendTo(this.tableElement);

	for(var i in tableData){
		var value = tableData[i][2];
		var formatted_value = parseFloat(value.toPrecision(3)).toExponential()
		var row_cls = tableData[i][0];
		
		var row = $("<tr />", {'value': row_cls}).appendTo(this.tbody);
		$("<td />",{'text': tableData[i][0]}).appendTo(row);
		$("<td />",{'text': tableData[i][1]}).appendTo(row);
		$("<td />",{'value':value, 'text': formatted_value, 'class':"numeric pvalue"}).appendTo(row);
	}
	
	this.corrector = new PValueCorrectedTable(parentElement, this.tbody, tableData, true, 0);
	this.tableElement.appendTo(parentElement);
};

function MotifTable(parentElement, tableData, numTests){
	var widget = this;
	this.data = tableData;
	
	this.tableElement = $('<table />', {'class':"motif-table"});
	$('<thead><tr><th>Motif</th><th>In Foreground</th><th>In Background</th><th>P-Value</th></tr></thead>').appendTo(this.tableElement);
	this.tbody = $('<tbody />').appendTo(this.tableElement);
	
	for(var i in tableData){
		var value = tableData[i][3];
		var formatted_value = parseFloat(value.toPrecision(3)).toExponential()
		
		var ratio_foreground = "{0} / {1}".format( tableData[i][1][0], tableData[i][1][1] )
		var ratio_background = "{0} / {1}".format( tableData[i][2][0], tableData[i][2][1] )
		
		var row = $("<tr />", {'value':"motif"}).appendTo(this.tbody);
		$("<td />",{'text': tableData[i][0], 'class':"peptide"}).appendTo(row);
		$("<td />",{'text': ratio_foreground, 'class':"numeric"}).appendTo(row);
		$("<td />",{'text': ratio_background, 'class':"numeric"}).appendTo(row);
		$("<td />",{'value':value, 'text': formatted_value, 'class':"numeric pvalue"}).appendTo(row);
	}
	
	for(var i = tableData.length; i < numTests; i++){
		var row = $("<tr />", {'value':"motif"}).appendTo(this.tbody);
		$("<td />",{'text': ""}).appendTo(row);
		$("<td />",{'text': ""}).appendTo(row);
		$("<td />",{'text': ""}).appendTo(row);
		$("<td />",{'value': 1000.0, 'class':"pvalue"}).appendTo(row);
	}
	
	this.corrector = new PValueCorrectedTable(parentElement, this.tbody, tableData, false, numTests);
	this.tableElement.appendTo(parentElement);
};



function format_op_arg(arg){
	var oper_values = {'in':"IN", 'nin':"NOT IN", 'eq':"=", 'neq':"\u2260", 'gt':">", 'geq':"\u2265", 'lt':"<", 'leq':"\u2264", 'add':"+", 'sub':"-", 'mul':"x", 'div':"/"};

	if(arg in oper_values){
		return $('<span class="condition-op">{0}</span>'.format(oper_values[arg]));
	}
	return $('<span class="condition-arg">{0}</span>'.format(arg));
}

function format_query(query){
	if(query == 'experiment')
		return $('<div class="query-clause"><span class="condition-boolean">-</span><span class="condition-title">Entire Experiment</span></div>')
	
	var complete_query = $('<div></div>');
	
	for(var i in query){
		var bop = query[i][0];
		if(bop == 'nop'){
			bop = '-';
		}
		
		var condition = query[i][1];
		var title = condition[0];
		
		var qclause = $('<div class="query-clause"/>').appendTo(complete_query);
		
		$('<span class="condition-boolean">{0}</span>'.format(bop.toUpperCase())).appendTo(qclause);
		$('<span class="condition-title">{0}:</span>'.format(title.capitalize())).appendTo(qclause);
		
		for(var i = 1; i < condition.length; i++){
			format_op_arg( condition[i] ).appendTo( qclause );
		}
	}
	
	return complete_query;
}

function SubsetTab(tabId, name, selectionEngine) {
	var tabTemplate = "<li><a href='#{0}'>{1}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>";
	this.tabId = "tabs-" + tabId;
	
	var subsetTab = this;
	this.subsetId = null;
	this.selectionEngine = selectionEngine;
	
	this.tabElement = $( tabTemplate.format(this.tabId, name) );
	this.contentContainer = $( '<div class="subset-content" id="{0}" />'.format(this.tabId) );
	
	this.filterset = $('<div class="filter-set" />').appendTo(this.contentContainer);
	this.fquery = $('<fieldset class="query"><legend>Foreground Query</legend></fieldset>').appendTo(this.filterset);
	this.bquery = $('<fieldset class="query"><legend>Background Query</legend></fieldset>').appendTo(this.filterset);
	var tmpdiv = $('<div class="formsubmission"></div>').appendTo(this.filterset);
	$('<div />', {'class':"clear"}).appendTo(this.filterset);
	
	$('<span>Subset Name:</span>').appendTo(tmpdiv);
	this.subsetName = $('<input type="text" value="{0}" />'.format(name)).appendTo(tmpdiv);
	this.saveSubset = $('<button></button>', {'class':'longtask', 'text':"Save Subset"}).appendTo(tmpdiv);
	this.saveSubset.on('click', function(){
		var name = subsetTab.subsetName.val();
		subsetTab.selectionEngine.saveSubset(subsetTab, name, subsetTab.response.foreground.query, subsetTab.response.background.query);
	});
	
    doc_url = 'http://www.assembla.com/spaces/proteomescout/wiki';
    images_url = 'https://proteomescout.wustl.edu/static/images';
	this.summary = $('<fieldset class="result-summary"><legend>Results</legend></fieldset>').appendTo(this.contentContainer);
	this.enrichment = $('<fieldset class="enrichment-tables"><legend>Feature Enrichment<a target="_blank" href="'+doc_url+'/Dataset_Analysis"><img width="24" height="24" src="'+images_url+'/helpicon.png" /></a></legend></fieldset>').appendTo(this.contentContainer);
	
	this.frequency = $('<fieldset class="frequency-charts"><legend>Residue Frequency</legend><table><thead><tr><th>Foreground:</th><th>Background:</th></tr></thead><tbody><tr><td class="foreground-seqlogo"></td><td class="background-seqlogo"></td></tr></tbody></table></div>').appendTo(this.contentContainer);
	this.motif = $('<fieldset class="motifs"><legend>Motif Enrichment</legend></div>').appendTo(this.contentContainer);
	
	this.proteins = $('<fieldset><legend>Proteins</legend></fieldset>').appendTo(this.contentContainer);
	this.proteinTable = $('<table class="protein_list"><thead><tr><th>MS id</th><th>Accession</th><th>Gene</th><th>Peptide</th><th>Site</th><th>Modifications</th><th>Annotations</th></tr></thead></table>').appendTo(this.proteins);
	this.proteinEntries = $('<tbody></tbody>').appendTo(this.proteinTable);
	
	this.dataContainer = $('<fieldset><legend>Experiment Data</legend></fieldset>').appendTo(this.contentContainer);
	this.data = $('<div class="experiment_data"></div>').appendTo(this.dataContainer);
};

SubsetTab.prototype.changeName = function(name) {
	this.tabElement.find('a').text(name);
	this.subsetName.val(name);
};

function add_annotations(pepEntry, annotation_td){
    images_url = 'https://proteomescout.wustl.edu/static/images/{0}';
    d = pepEntry[7]
    if(d.mutant)
        $('<img />', {'title': 'This residue has recorded natural variants', 'src': images_url.format('red_flag.jpg')}).appendTo(annotation_td);
    if(d.kinase)
        $('<img />', {'title': 'This residue is in a Pfam kinase domain', 'src': images_url.format('kinase.jpg')}).appendTo(annotation_td);
    if(d.loop == 'K')
        $('<img />', {'title': 'This residue is in a predicted kinase activation loop', 'src': images_url.format('active.jpg')}).appendTo(annotation_td);
    if(d.loop == '?')
        $('<img />', {'title': 'This residue is in a possible kinase activation loop', 'src': images_url.format('question.jpg')}).appendTo(annotation_td);
}

SubsetTab.prototype.formatPeptides = function(peptides) {
	for(var i in peptides){
		var pepEntry = peptides[i];
		var rowClass = 'odd';
		if(i % 2 == 0)
			rowClass = 'even';
		
		var tableRow = $('<tr />', {"class":rowClass}).appendTo(this.proteinEntries);
		$('<td>{0}</td>'.format(pepEntry[0])).appendTo(tableRow);
		$('<td>{0}</td>'.format(pepEntry[1])).appendTo(tableRow);
		var ltd = $('<td></td>').appendTo(tableRow);
		$('<a href="{0}" target="_blank">{1}</a>'.format(pepEntry[3], pepEntry[2])).appendTo(ltd);
		
		$('<td class="peptide">{0}</td>'.format(pepEntry[4])).appendTo(tableRow);
		$('<td class="modsite">{0}</td>'.format(pepEntry[5])).appendTo(tableRow);
		$('<td class="modsite">{0}</td>'.format(pepEntry[6])).appendTo(tableRow);
		annotation_td = $('<td></td>').appendTo(tableRow);
        add_annotations(pepEntry, annotation_td);
	}
};

SubsetTab.prototype.formatData = function(measurement_data){
	for(var i in measurement_data){
		var run_div = $('<div class="run" />').appendTo(this.data);
		var run = measurement_data[i];
		
		$('<div class="name">{0}</div>'.format(run.name)).appendTo(run_div);
		$('<div class="units">{0}</div>'.format(run.units)).appendTo(run_div);
		$('<div class="peptides">{0}</div>'.format(run.label)).appendTo(run_div);
		
		for(var j in run.series){
			var datapt = run.series[j];
			$('<div class="datapoint">{0},{1},{2}</div>'.format(datapt[0],datapt[1],datapt[2])).appendTo(run_div);
		}
	}
	
	$('<div class="chart" />').appendTo(this.data);
	d3.select("#{0}".format(this.tabId)).select(".experiment_data").each(function(){
		processRuns(this);
	});
}

SubsetTab.prototype.setId = function(subsetId){
	this.subsetId = subsetId;
}

SubsetTab.prototype.hasId = function(){
	return this.subsetId != null;
}

SubsetTab.prototype.init = function(query_response) {
	format_query(query_response.foreground.query).appendTo(this.fquery);
	format_query(query_response.background.query).appendTo(this.bquery);
	
	this.response = query_response;

	$("<div>{0} out of {1} proteins selected</div>".format(query_response.foreground.proteins, query_response.background.proteins)).appendTo(this.summary)
	$("<div>{0} out of {1} peptides selected</div>".format(query_response.foreground.peptides, query_response.background.peptides)).appendTo(this.summary)
	$("<div>{0} out of {1} sites selected</div>".format(query_response.foreground.sites, query_response.background.sites)).appendTo(this.summary)

	this.enrichmentTable = new EnrichmentTable(this.enrichment, query_response.enrichment)
	
	createSeqlogo(d3.select("#{0}".format(this.tabId)).select(".foreground-seqlogo".format(this.tabId)), query_response.foreground.seqlogo, 350, 270);
	createSeqlogo(d3.select("#{0}".format(this.tabId)).select(".background-seqlogo".format(this.tabId)), query_response.background.seqlogo, 350, 270);

    if(query_response.motif.queried){
	    this.motifTable = new MotifTable(this.motif, query_response.motif.results, query_response.motif.tests)
    }else{
        $("<div>Motif information was not collected for this subset</div>").appendTo(this.motif);
    }
	this.formatPeptides(query_response.peptides);
	this.formatData(query_response.measurements);
};

function QuantitativeSelector(parent_element, field_values) {
	this.element = $("<span>:</span>");
	this.element.appendTo(parent_element);

	this.field_values = field_values;
	this.compare_values = {'eq':"=", 'neq':"\u2260", 'gt':">", 'geq':"\u2265", 'lt':"<", 'leq':"\u2264"};
	this.oper_values = {'add':"+", 'sub':"-", 'mul':"x", 'div':"/"};
	
	this.selectors = [];
	this.oper_state = 'LHS';
	
	this.addVariable();
};

QuantitativeSelector.prototype.build_query = function(){
	if(!this.checkValid()){
		throw new Error("Invalid expression");
	}
	
	var expression = [];
	expression.push("quantitative");
	
	for(var i in this.selectors){
		if(this.selectors[i].hasClass('operator')) {
			var v = this.selectors[i].val();
			expression.push(v);
		}
		if(this.selectors[i].hasClass('variable')) {
			var v = this.selectors[i].find('select').val();
			var n = this.selectors[i].find('input').val();
			
			if(v == ''){
				throw new Error("Variable cannot be empty");
			}
			
			if(v == 'numeric'){
				if(n == ''){
					throw new Error("Numeric value cannot be empty");
				}
				expression.push(n);
			}else
				expression.push(v);
		}
	}
	
	var state = this.computeOperState(this.selectors.length-1);
	if(state == 'L'){
		throw new Error("Incomplete quantiative comparison");
	}
	
	if(expression[expression.length-1] == ''){
		expression.pop();
	}
	
	if(expression.length == 0){
		throw new Error("Empty Expression");
	}

	console.log(expression);
	return expression;
};

QuantitativeSelector.prototype.computeOperState = function(oper_index) {
	var cstate = ''; 
	for(var i = 1; i <= oper_index; i+=2){
		var oper_val = this.selectors[i].val();

		if(cstate == 'R'){
			cstate = 'D';
		}
		if(cstate == 'M'){
			cstate = 'R';
		}
		if(cstate == 'L'){
			cstate = 'M';
		}
		if(cstate == ''){
			cstate = 'L';
		}
		
		if(oper_val in this.compare_values){
			cstate = 'M';
		}
	}
	return cstate;
};

QuantitativeSelector.prototype.checkValid = function() {
	var last_val = "start";
	for(var i in this.selectors){
		if(this.selectors[i].hasClass('variable')){
			var var_val = this.selectors[i].find('select').val();
			if(last_val == ''){
				return false;
			}
			if(var_val == ''){
				return false;
			}
		}
		if(this.selectors[i].hasClass('operator')){
			var oper_state = this.computeOperState(i);
			var oper_val = this.selectors[i].val();
			
			if(last_val == ''){
				return false;
			}
			if(oper_state == 'D'){
				return false;
			}
			if(oper_state == 'M' && !(oper_val in this.compare_values) && oper_val != ''){
				return false;
			}
			if(oper_state == 'R' && !(oper_val in this.oper_values) && oper_val != ''){
				return false;
			}
			
			last_val = oper_val;
		}
	}
	return true;
};

QuantitativeSelector.prototype.removeAfter = function(i) {
	while(this.selectors.length > i+1){
		var elem = this.selectors.pop();
		elem.remove();
	}
};

QuantitativeSelector.prototype.addOperator = function() {
	var selector = this;
	
	var i = this.selectors.length;

	var oper_select = $("<select />", {'class':"operator"});
	oper_select.on('change', function(){
		var val = $(this).val();
		
		if(!selector.checkValid()){
			selector.removeAfter(i);
		}
		if (i+1 == selector.selectors.length){
			selector.addVariable();
		}
	});
	this.selectors.push(oper_select);
	var oper_state = this.computeOperState(i+1);
	if(oper_state == 'D'){
		this.selectors.pop();
		return;
	}
	
	
	$("<option />").appendTo(oper_select);
	
	if(oper_state != 'M'){
		for(var v in this.oper_values){
			$("<option value=\"{0}\">{1}</option>".format( v, this.oper_values[v] )).appendTo(oper_select);
		}	
	}
	if(oper_state != 'R'){
		for(var v in this.compare_values){
			$("<option value=\"{0}\">{1}</option>".format( v, this.compare_values[v] )).appendTo(oper_select);
		}
	}	
	
	oper_select.appendTo(this.element);
};

QuantitativeSelector.prototype.addVariable = function() {
	var selector = this;
	
	var i = this.selectors.length;
	
	var container = $("<span />", {'class':"variable"}); 
	var variable_select = $("<select />").appendTo(container);
	var numeric_input = $('<input type="text" style="display:none;"/>').appendTo(container);
	var last_val = "";
	
	numeric_input.on('change', function(){
		var val = $(this).val();
		
		if(isNaN(parseFloat(val)) || !isFinite(val)){
			$(this).val(last_val);
		} else {
			last_val = val;
		}
	});
	
	this.selectors.push(container);
	
	variable_select.on('change', function(){
		if($(this).val() == ''){
			selector.removeAfter(i);
		} 
		if($(this).val() == 'numeric'){
			numeric_input.show();
		} else {
			numeric_input.hide();
		}
		if(i+1 == selector.selectors.length && selector.computeOperState(i) != 'D'){
			selector.addOperator();
		}
		
	});
	
	$("<option />").appendTo(variable_select);
	$('<option value="numeric">Numeric</option>').appendTo(variable_select);
	for(var j in this.field_values){
		$("<option value=\"{0}\">{0}</option>".format( this.field_values[j] )).appendTo(variable_select);
	}
	
	container.appendTo(this.element);
};

function SubsetSelector(parent_element, saved_subsets) {
	this.element = $("<span />");
	
	this.element.appendTo(parent_element);
	
	$("<span>MS ID</span>").appendTo(this.element);
	
	this.operation = $("<select />").appendTo(this.element);
	$("<option value=\"in\">in</option>").appendTo(this.operation);
	$("<option value=\"nin\">not in</option>").appendTo(this.operation);
	
	$("<span class=\"field_label\">Subset: </span>").appendTo(this.element);
	this.value = $("<select />").appendTo(this.element);
	
	$("<option />").appendTo(this.value);
	for(var i in saved_subsets){
		$("<option value=\"{0}\">{0}</option>".format(saved_subsets[i])).appendTo(this.value);
	}
};

SubsetSelector.prototype.build_query = function(){
	var op = this.operation.val();
	var subset = this.value.val()
	
	if(subset == '')
		throw new Error("Subset name must be specified");
	
	return ['subset', op, subset];
};

function ScansiteSelector(parent_element, scansite_keys, scansite_fields) {
	var selector = this;
	this.element = $("<span />");
	
	this.field_values = scansite_fields;
	this.element.appendTo(parent_element);
	
	$("<span>Type: </span>").appendTo(this.element);
	this.field = $("<select />").appendTo(this.element);
	
	$('<option />').appendTo(this.field);
	for(var i in scansite_keys){
		var k = scansite_keys[i];
		$('<option value="{0}">{0}</option>'.format(k)).appendTo(this.field);
	}
	this.field.on('change', function(){
		var field_val = selector.field.val();
		selector.value.empty();
		
		if(field_val in selector.field_values){
			$("<option />").appendTo(selector.value);
			for(var i in selector.field_values[field_val]){
				$("<option value=\"{0}\">{0}</option>".format( selector.field_values[field_val][i] )).appendTo(selector.value);
			}
		}
	});
	
	
	this.operation = $("<select />").appendTo(this.element);
	$("<option value=\"eq\">=</option>").appendTo(this.operation);
	$("<option value=\"neq\">\u2260</option>").appendTo(this.operation);
	
	$("<span class=\"field_label\">Term: </span>").appendTo(this.element);
	this.value = $("<select />").appendTo(this.element);
//	this.value.combobox();
	
	$("<span class=\"field_label\">Stringency: </span>").appendTo(this.element);
	this.stringency = $("<select />").appendTo(this.element);
	
	$("<option value=\"5\">Low</option>").appendTo(this.stringency);
	$("<option value=\"1\">Medium</option>").appendTo(this.stringency);
	$("<option value=\"0.2\">High</option>").appendTo(this.stringency);
};

ScansiteSelector.prototype.build_query = function() {
	var f = this.field.val();
	var op = this.operation.val();
	var term = this.value.val();
	var s = this.stringency.val();
	
	if(f == '')
		throw new Error("You must select a type");
	if(term == '')
		throw new Error("You must select a term");
	
	return ['scansite', f, op, term, s];
};

function ProteinSelector(parent_element, field_values) {
	var selector = this;
	
	this.element = $("<span />");
	this.element.appendTo(parent_element);
	$("<span class=\"field_label\">Gene/Protein: </span>").appendTo(this.element);
	this.value = $("<input type=\"text\" width=\"200\" />").appendTo(this.element);
	
	this.value.autocomplete({
	      source: field_values
	    });
	
//	$('<option />').appendTo(this.value);
//	for(var i in field_values){
//		$("<option value=\"{0}\">{0}</option>".format(field_values[i])).appendTo(this.value);
//	}
//	this.value.combobox();
};

ProteinSelector.prototype.build_query = function() {
	var p = this.value.val();
	
	if(p == ''){
		throw new Error("Gene/Protein search field cannot be empty");
	}
	return ['protein', p];
};


function MetadataSelector(parent_element, type, field_name, value_name, field_values, values_by_field) {
	var selector = this;

	this.type = type;
	this.field_values = field_values;
	this.values_by_field = values_by_field;
	
	this.element = $("<span />");
	this.element.appendTo(parent_element);
	$("<span class=\"field_label\">{0}</span>".format(field_name)).appendTo(this.element);
	this.field_name = $("<select />").appendTo(this.element);
	
	$("<option />").appendTo(this.field_name);
	for(var i in field_values){
		$("<option value=\"{0}\">{0}</option>".format( field_values[i] )).appendTo(this.field_name);
	}
	
	this.operation = $("<select />").appendTo(this.element);
	$("<option value=\"eq\">=</option>").appendTo(this.operation);
	$("<option value=\"neq\">\u2260</option>").appendTo(this.operation);
	
	$("<span class=\"field_label\">{0}</span>".format(value_name)).appendTo(this.element);
	this.value = $("<select />").appendTo(this.element);
	
	this.field_name.on('change', function(){
		var field_val = selector.field_name.val();
		selector.value.empty();
		
		if(field_val in selector.values_by_field){
			$("<option />").appendTo(selector.value);
			for(var i in selector.values_by_field[field_val]){
				$("<option value=\"{0}\">{0}</option>".format( selector.values_by_field[field_val][i] )).appendTo(selector.value);
			}
		}
	});
//	this.value.combobox();
};

MetadataSelector.prototype.build_query = function() {
	var f = this.field_name.val();
	var op = this.operation.val();
	var v = this.value.val();
	
	if(f == '')
		throw new Error("You must specify a field");
	if(v == '')
		throw new Error("You must specify a value");
	
	return [this.type, f, op, v]
};

function SequenceSelector(parent_element) {
	this.element = $("<span />");
	this.element.appendTo(parent_element);
	
	$("<span class=\"field_label\">Peptide Sequence: </span>").appendTo(this.element);
	this.value = $("<input type=\"text\" length=\"15\" width=\"15\" />").appendTo(this.element);
};

SequenceSelector.prototype.build_query = function() {
	var v = this.value.val();
	if(v==''){
		throw new Error("You must specify a search string");
	}
	
	return ['sequence', v]
};

function SelectorCondition(parent_element, field_data, show_boolean_op) {
	var condition = this;
	this.field_data = field_data;
	
	this.element = $('<div></div>');
	var boolean_container = $('<span class="condition-boolean"></span>');
	boolean_container.appendTo(this.element);
	
	if(show_boolean_op){
		this.boolean_operator = $('<select><option value="and">and</option><option value="or">or</option></select>').appendTo(boolean_container);
	}else{
		this.boolean_operator = null;
		boolean_container.text("-");
	}
	$("<span class=\"condition-title\">Condition:</span>").appendTo(this.element);
	this.type_select = $("<select />").appendTo(this.element);
	
	$("<option></option>").appendTo(this.type_select);
	$("<option value=\"quantitative\">Quantitative</option>").appendTo(this.type_select);
	$("<option value=\"subset\">Subset</option>").appendTo(this.type_select);
	$("<option value=\"cluster\">Cluster</option>").appendTo(this.type_select);
	$("<option value=\"metadata\">Metadata</option>").appendTo(this.type_select);
	$("<option value=\"protein\">Protein</option>").appendTo(this.type_select);
	$("<option value=\"scansite\">Scansite</option>").appendTo(this.type_select);
	$("<option value=\"sequence\">Sequence</option>").appendTo(this.type_select);
	
	
	this.type_select.on('change', function(){
		condition.changed();
	});
	
	this.selector = null;
	
	this.element.appendTo(parent_element);
};

SelectorCondition.prototype.build_query = function() {
	var expression = [];
	if(this.boolean_operator != null)
		expression.push( this.boolean_operator.val() );
	else
		expression.push( 'nop' );
	
	var value = this.type_select.val();
	if(value == '')
		throw new Error("Empty condition clause");
	
	expression.push( this.selector.build_query() );
	
	return expression;
};

SelectorCondition.prototype.changed = function() {
	var value = this.type_select.val();
	if(this.selector != null){
		this.selector.element.remove();
	}
	if(value == 'quantitative'){
		this.selector = new QuantitativeSelector(this.element, this.field_data.quantitative_fields);
	}
	if(value == 'metadata'){
		this.selector = new MetadataSelector(this.element, 'metadata', ":", "", this.field_data.metadata_keys, this.field_data.metadata_fields);
	}
	if(value == 'subset'){
		this.selector = new SubsetSelector(this.element, this.field_data.subset_labels);
	}
	if(value == 'cluster'){
		this.selector = new MetadataSelector(this.element, 'cluster', ":", "Cluster ID:", this.field_data.clustering_sets, this.field_data.clustering_labels);
	}
	if(value == 'sequence'){
		this.selector = new SequenceSelector(this.element);
	}
	if(value == 'protein'){
		this.selector = new ProteinSelector(this.element, this.field_data.accessions);
	}
	if(value == 'scansite'){
		this.selector = new ScansiteSelector(this.element, this.field_data.scansite_keys, this.field_data.scansite_fields);
	}
};

function SubsetManager(element, selectionEngine) {
	this.tabCounter = 0;
	this.tabs = element.tabs();
	var tabs = this.tabs
	
	this.selectionEngine = selectionEngine;
	
	tabs.delegate( "span.ui-icon-close", "click", function() {
	      var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
	      $( "#" + panelId ).remove();
	      tabs.tabs( "refresh" );
	    });
	 
    tabs.bind( "keyup", function( event ) {
      if ( event.altKey && event.keyCode === $.ui.keyCode.BACKSPACE ) {
        var panelId = tabs.find( ".ui-tabs-active" ).remove().attr( "aria-controls" );
        $( "#" + panelId ).remove();
        tabs.tabs( "refresh" );
      }
    });
}

SubsetManager.prototype.addSubset = function(query_result) {
	var st = new SubsetTab(this.tabCounter, query_result.name, this.selectionEngine)
	
	var numtabs = this.tabs.find( ".ui-tabs-nav > li" ).length;
	this.tabs.find( ".ui-tabs-nav" ).append( st.tabElement );
	this.tabs.find( ".ui-tabs-nav" ).sortable({
	      axis: "x",
	      stop: function() {
	        tabs.tabs( "refresh" );
	      }
	    });
	
    this.tabs.append( st.contentContainer );
    this.tabs.tabs( "refresh" );
    
    st.init(query_result);
    this.tabs.tabs('option', 'active', numtabs);
    
	this.tabCounter++;
	return st;
};

function SubsetSelection(element, webservice_url) {
	var selector = this;
	
	this.element = element;
	
	this.webservice_url = webservice_url;
	this.query_num = 0;
	
	this.subsetPrefix = 'Subset: ';
	this.field_data = JSON.parse( Base64.decode( element.find("#field-data").text() ) );
	this.experiment_id = this.field_data.experiment_id;

	this.failure_dialog = $("<div title=\"Error!\"></div>")
								.dialog( {  autoOpen:false, modal: true, buttons: { "Ok": function(){ $(this).dialog( 'close' ); } } } );
	this.failure_text = $("<span />").appendTo(this.failure_dialog);
	
	this.subsetSelection = $("#saved-subset-select");
	this.backgroundSelection = $("#background-select");
    this.motifLengthSelection = $("#motif-length-select");
	
	for(var i in this.field_data.subset_labels){
		var label = this.field_data.subset_labels[i];
		$('<option />', {'value': label, 'text': label}).appendTo(this.subsetSelection);
		var background_label  = '{0}{1}'.format(this.subsetPrefix, label);
		$('<option />', {'value': background_label, 'text': background_label}).appendTo(this.backgroundSelection);
	}

    this.selectAnnotation = $("#select-annotation");
    this.selectAnnotation.val(""+this.field_data.annotation_set);
	
	this.subsetOpen = $("#open-saved-subset");
	this.subsetOpen.on('click', function(){
		selector.openExistingSubset(selector.subsetSelection.val());
	})
	
	
	this.clusterSelection = $("#cluster-set");
	
	$('<option />').appendTo(this.clusterSelection);
	for(var i in this.field_data.clustering_sets){
		var label = this.field_data.clustering_sets[i];
		$('<option />', {'value': label, 'text': label}).appendTo(this.clusterSelection);
	}
	
	this.clusterOpen = $("#show-clusters").on('click', function(){
		selector.openClusters(selector.clusterSelection.val());
	});
	
	this.conditions = [];
	this.condition_list = $("#filter-conditions");
	this.add_condition = $("#add-condition");
	this.add_condition.on('click', function(){
		selector.addConditionField();
	});
	this.remove_condition = $("#remove-condition");
	this.remove_condition.on('click', function(){
		selector.removeConditionField();
	});
	

	
	this.compute_subset = $("#compute-subset");
	this.compute_subset.on('click',function(){
		selector.submitQuery();
	});
	
	this.clear_form = $("#clear-form");
	this.clear_form.on('click', function(){
		selector.clearConditions();
	});
	
	this.subsetManager = new SubsetManager( element.find('#open-subsets'), this );
};

SubsetSelection.prototype.displayError = function(errorMessage) {
	this.failure_text.text(errorMessage);
	this.failure_dialog.dialog( "open" );
	done_waiting();
};

SubsetSelection.prototype.openExistingSubset = function(name) {
	var app = this;
	
	if(name == ''){
		this.displayError("You must choose a subset");
	}else{
		var query_url = this.webservice_url + '/subsets/fetch';
        var motif_length = this.motifLengthSelection.val()
		var subset_fetch_query = {	'name': name,
									'experiment': this.experiment_id,
                                    'annotation_set_id': this.field_data.annotation_set,
                                    'motif_length': motif_length
				 					}
		
		$.ajax({
			url: query_url,
			type: 'POST',
			contentType:'application/json',
			data: JSON.stringify(subset_fetch_query),
			dataType:'json',
			success: function(data) {
				done_waiting();
				
				if(data.status == 'error'){
					app.displayError(data.message);
				}else if(data.status == 'success'){
					var st = app.subsetManager.addSubset(data);
					st.setId(data.id);
				}
			} ,
			error: function(jqXHR, textStatus, errorThrown) {
				app.displayError("Error in server response, please try again.");
				console.log(textStatus);
				console.log(errorThrown);
			}
		});

	}
}

SubsetSelection.prototype.saveSubset = function(tabElement, name, foreground, background){
	var app = this;
	
	if(tabElement.hasId()){
		this.displayError("This subset has already been saved");
	}else if(name == ''){
		this.displayError("Name cannot be an empty field");
	}else{

		var query_url = this.webservice_url + '/subsets/save';
		var subset_save_query = {'name': name,
								 'experiment': this.experiment_id,
								 'foreground': foreground,
								 'background': background,
                                 'annotation_set_id': this.field_data.annotation_set}		
		
		$.ajax({
			url: query_url,
			type: 'POST',
			contentType:'application/json',
			data: JSON.stringify(subset_save_query),
			dataType:'json',
			success: function(data) {
				done_waiting();
				
				if(data.status == 'error'){
					app.displayError(data.message);
				}else if(data.status == 'success'){
					var label = data.name;
					tabElement.changeName(label);
					tabElement.setId(data.id);

					app.field_data.subset_labels.push(label);
					$('<option />', {'value': label, 'text': label}).appendTo(app.subsetSelection);
					
					var background_label  = 'Subset: {0}'.format(label);
					$('<option />', {'value': background_label, 'text': background_label}).appendTo(app.backgroundSelection);
					
				}
			} ,
			error: function(jqXHR, textStatus, errorThrown) {
				app.displayError("Error in server response, please try again.");
				console.log(textStatus);
				console.log(errorThrown);
			}
		});
		
	}
};

SubsetSelection.prototype.openClusters = function(cluster_set) {
	var app = this;
	var query_url = this.webservice_url + '/subsets/query';
	var error_state = false;
	var returned = 0;
	
	if(cluster_set == ''){
		this.displayError("You must select a cluster set.");
	}else{
		var num_tabs = this.field_data.clustering_labels[cluster_set].length;
		for(var i in this.field_data.clustering_labels[cluster_set]){
			var label = this.field_data.clustering_labels[cluster_set][i];
			
			var expression = [
			                  ['nop',['cluster', cluster_set, 'eq', label]]
			                 ];
			
            var motif_length = this.motifLengthSelection.val()
			var subset_query = {
					'experiment': this.experiment_id,
					'type': 'create',
					'name': '{0}:{1}'.format(cluster_set, label),
					'background': 'experiment',
					'foreground': expression,
                    'annotation_set_id': this.field_data.annotation_set, 
                    'motif_length': motif_length
			};
			
			$.ajax({
				url: query_url,
				type: 'POST',
				contentType:'application/json',
				data: JSON.stringify(subset_query),
				dataType:'json',
				success: function(data) {
					returned += 1;
					
					if(data.status == 'error'){
						app.displayError(data.message);
					}else if(data.status == 'success'){
						app.subsetManager.addSubset(data);
					}
					
					if(returned == num_tabs){
						done_waiting();
					}
				},
				error: function(jqXHR, textStatus, errorThrown) {
					app.displayError("Error in server response, please try again.");
					console.log(textStatus);
					console.log(errorThrown);
				}
			});
		}
	}
};

SubsetSelection.prototype.submitQuery = function() {
	var app = this;
	
	this.query_num += 1;
	if(this.conditions.length == 0){
		this.displayError("You must specify query conditions!");
		return;
	}
	
	var expression = [];
	for(var i in this.conditions){
		try{
			q = this.conditions[i].build_query()
			expression.push(q);
		}catch(err){
			this.displayError("Query error line {0}: {1}".format(parseInt(i)+1, err.message));
			return;
		}
	}
	
	var background = this.backgroundSelection.val();
	if(background.startsWith(this.subsetPrefix)){
		var bg_subset = background.substring(this.subsetPrefix.length);
		background = [ ['nop', ['subset', 'in', bg_subset]] ];
	}

    var motif_length = this.motifLengthSelection.val()
	var subset_query = {
			'experiment': this.experiment_id,
			'type': 'create',
			'name': 'Subset {0}'.format(this.query_num),
			'background': background,
			'foreground': expression,
            'annotation_set_id': this.field_data.annotation_set,
            'motif_length': motif_length
	};
    console.log(subset_query);
	
	var query_url = this.webservice_url + '/subsets/query';
	
	$.ajax({
		url: query_url,
		type: 'POST',
		contentType:'application/json',
		data: JSON.stringify(subset_query),
		dataType:'json',
		success: function(data) {
			done_waiting();
			if(data.status == 'error'){
				app.displayError(data.message);
			}else if(data.status == 'success'){
				app.subsetManager.addSubset(data);
			}
		} ,
		error: function(jqXHR, textStatus, errorThrown) {
			app.displayError("Error in server response, please try again.");
			console.log(textStatus);
			console.log(errorThrown);
		}
	});
}

SubsetSelection.prototype.submitQueryFromString = function(qstring) {
	var app = this;
	this.query_num += 1;

    var foreground = JSON.parse( Base64.decode(qstring) );
    var background = 'experiment';

 	var subset_query = {
			'experiment': this.experiment_id,
			'type': 'create',
			'name': 'Subset {0}'.format(this.query_num),
			'background': background,
			'foreground': foreground,
            'annotation_set_id': this.field_data.annotation_set,
            'motif_length': "None"
	};
	
	var query_url = this.webservice_url + '/subsets/query';

    console.log(subset_query);
	
	$.ajax({
		url: query_url,
		type: 'POST',
		contentType:'application/json',
		data: JSON.stringify(subset_query),
		dataType:'json',
		success: function(data) {
			done_waiting();
			if(data.status == 'error'){
				app.displayError(data.message);
			}else if(data.status == 'success'){
				app.subsetManager.addSubset(data);
			}
		} ,
		error: function(jqXHR, textStatus, errorThrown) {
			app.displayError("Error in server response, please try again.");
			console.log(textStatus);
			console.log(errorThrown);
		}
	});
}

SubsetSelection.prototype.addConditionField = function() {
	var is_first = this.conditions.length == 0;
	var new_field = new SelectorCondition(this.condition_list, this.field_data, !is_first);
	this.conditions.push(new_field);
};

SubsetSelection.prototype.removeConditionField = function() {
	if(this.conditions.length > 0){
		var field = this.conditions.pop();
		field.element.remove();
	}
};

SubsetSelection.prototype.clearConditions = function() {
	for(var i in this.conditions){
		this.conditions[i].remove();
	}
	this.conditions = [];
};

$(function(){
	ss = new SubsetSelection($("#subset-select"), $("#webservice_url").text());

    var querytext = $("#initial-query").text();
    if(querytext != ''){
        $(".waiting-modal").show();
        ss.submitQueryFromString(querytext)
    }
});
