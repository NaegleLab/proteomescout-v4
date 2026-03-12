function ExperimentEntry(table_element, edata) {
    this.marked = false;
    this.data = edata;
    this.element = $("<tr></tr>", {
                        'class': "entry",
                        'id': "e{0}".format(this.data.id)
                    });

    table_element.append(this.element);
    $(this.element).on('click', null, this, function(e) {
                                e.data.mark_selected();
                            });

    $("<td><input type=\"hidden\" value=\"{0}\" name=\"experiment\" /></td>".format(edata.id)).appendTo(this.element);
    $("<td>{0}</td>".format(edata.id)).appendTo(this.element);
    $("<td>{0}</td>".format(edata.name)).appendTo(this.element);
    $("<td>{0}</td>".format(edata.residues)).appendTo(this.element);
    $( "<td><a href=\"{0}\" target=\"_blank\"><button>View</button></a></td>".format(edata.link) ).appendTo(this.element);

};

ExperimentEntry.prototype.id = function() {
    return this.data.id;
};

ExperimentEntry.prototype.remove = function() {
    this.element.remove();
};

ExperimentEntry.prototype.mark_selected = function() {
    if(!this.marked){
        this.marked = true;
        this.element.addClass('marked');
    }else{
        this.marked = false;
        this.element.removeClass('marked');
    }
};

function ResultPager(search_tool, parent_element){
    var pager_tool = this;
    this.search_tool = search_tool;
    this.parent_element = parent_element;

    this.left_button = $("<button>&lt;&lt;</button>");
    this.number_container = $("<span />");
    this.right_button = $("<button>&gt;&gt;</button>");

    this.left_button
            .addClass('longtask')
            .on( 'click', function() {
                pager_tool.go_left();
             });

    this.right_button
            .addClass('longtask')
            .on( 'click', function() {
                pager_tool.go_right();
             });

    this.count = 0;
    this.limit = 0;
    this.offset = 0;
    this.left_button.hide();
    this.right_button.hide();
    this.parent_element.hide();

    this.left_button.appendTo(this.parent_element);
    this.number_container.appendTo(this.parent_element);
    this.right_button.appendTo(this.parent_element);
}

ResultPager.prototype.set_values = function(count, limit, offset) {
    this.count = count;
    this.limit = limit;
    this.offset = offset + 1;

    this.parent_element.show();
    if(offset > 1)
        this.left_button.show();
    else
        this.left_button.hide();

    if(offset + limit < count)
        this.right_button.show();
    else
        this.right_button.hide();

    var upperlimit = offset+limit;
    if(upperlimit > count){
        upperlimit = count;
    }

    this.number_container.text("Showing {0} - {1} of {2} results".format(this.offset, upperlimit, count));
};

ResultPager.prototype.go_left = function() {
    this.offset = this.offset - this.limit
    if(this.offset < 1)
        this.offset = 1;

    this.search_tool.set_offset(this.offset-1);
    this.search_tool.submit_search();
};

ResultPager.prototype.go_right = function() {
    if(this.offset + this.limit < this.count){
        this.offset = this.offset + this.limit 
        this.search_tool.set_offset(this.offset-1);
        this.search_tool.submit_search();
    }
};

function ConditionField(list_element){
    var field = this;
    this.list_element = list_element;
    this.item = $("<div></div>")

    $("<span>Condition Type:</span>").appendTo(this.item);

    this.value_field = $("<input type=\"text\" width=\"50\" />");
    this.type_field = $("<select />");

    $("<option value=\"\"></option>").appendTo(this.type_field);
    $("<option value=\"cell\">Cell Type</option>").appendTo(this.type_field);
    $("<option value=\"tissue\">Tissue Type</option>").appendTo(this.type_field);
    $("<option value=\"drug\">Drug</option>").appendTo(this.type_field);
    $("<option value=\"stimulus\">Stimulus</option>").appendTo(this.type_field);
    $("<option value=\"environment\">Environmental</option>").appendTo(this.type_field);

    this.type_field.change(function(){
        var v = $(this).val();
        if(v != '')
            get_auto_completions(v, field.value_field);
    });
    this.type_field.appendTo(this.item);

    $("<span>Value:</span>").appendTo(this.item);
    this.value_field.appendTo(this.item);

    this.item.appendTo(this.list_element);
};

ConditionField.prototype.type = function() {
    return this.type_field.val();
};

ConditionField.prototype.value = function() {
    return this.value_field.val();
};

function ExperimentSearch(finder_element, list_element, service_url){
    var search_form = this;

    this.service_url = service_url;
    this.finder = finder_element;
    this.list = list_element;
    this.results = this.finder.find("#result_list");

    this.added_list = this.list.find(".experiment_list > tbody");
    this.result_list = this.finder.find("#result_list > table > tbody");
    this.condition_list = this.finder.find("#condition_list");
    this.text_search = this.finder.find("#text_search");

    this.submit_button = this.finder.find("#submit_query");
    this.submit_button.on( 'click', function() {
        search_form.submit_search();
        this.offset = 0;
    });

    this.add_conditions = this.finder.find("#add_conditions");
    this.add_conditions.on( 'click', function() {
        search_form.add_condition_field();
    });

    this.clear_conditions = this.finder.find("#clear_conditions")
    this.clear_conditions.on( 'click', function() {
        search_form.clear_condition_fields();
    });

    this.add_button = this.finder.find("#add_selected");
    this.add_button.on( 'click', function() {
        search_form.add_selection();
    });
    this.clear_button = this.finder.find("#clear_selection");
    this.clear_button.on( 'click', function() {
        search_form.clear_selection();
    });
    this.close_button = this.finder.find("#close");
    this.close_button.on( 'click', function() {
        search_form.close();
    });


    this.pager = new ResultPager(this, this.finder.find("#result_pager"));
    this.offset = 0;

    this.search_results = [];
    this.added_results = [];
    this.condition_fields = [];
};

ExperimentSearch.prototype.close = function() {
    this.finder.dialog("close");
};

ExperimentSearch.prototype.add_condition_field = function() {
    this.condition_fields.push( new ConditionField( this.condition_list ) );
};

ExperimentSearch.prototype.clear_condition_fields = function() {
    this.condition_list.empty();
    this.condition_fields = [];
};

ExperimentSearch.prototype.parse_conditions = function() {
    var conditions = [];
    for(var i in this.condition_fields) {
        var k = this.condition_fields[i].type();
        var v = this.condition_fields[i].value();
        conditions.push("{0}:{1}".format(k,v));
    }
    return conditions.join(",");
};

ExperimentSearch.prototype.set_offset = function(offset){
    this.offset = offset;
}

ExperimentSearch.prototype.submit_search = function() {
    var search_form = this;
    var search_value = this.text_search.val();

    var conditions_value = this.parse_conditions();
    var url_args = { 'search_term': search_value, 'conditions': conditions_value, 'offset': this.offset };

    search_form.result_list.find(".entry").remove();
    this.search_results = [];

    $.ajax({
          dataType: "json",
          url: "{0}/{1}".format(this.service_url, "experiments"),
          data: url_args,
          success: function(data) {
              search_form.pager.set_values(data.count, data.limit, data.offset);

              for(var i in data.experiments) {
                  search_form.search_results.push(new ExperimentEntry(search_form.result_list, data.experiments[i]));
              }

              if(search_form.search_results.length > 0)
                  search_form.results.show();
              else
                  search_form.results.hide();

            done_waiting();
          }
    });
};

ExperimentSearch.prototype.add_result = function(data) {
    found = false;
    for(var i in this.added_results){
        if(this.added_results[i].id() == data.id){
            found = true;
            break;
        }
    }
    if(!found)
        this.added_results.push(new ExperimentEntry(this.added_list, data));
};

ExperimentSearch.prototype.add_selection = function() {
    var results = this.search_results;

    for(var i in results){
        if(results[i].marked)
            this.add_result(results[i].data);
    }

    if(this.added_results.length > 0){
        this.list.show();
    }
};

ExperimentSearch.prototype.clear_selection = function() { 
    var results = this.search_results;

    for(var i in results){
        if(results[i].marked)
            results[i].mark_selected();
    }
};

ExperimentSearch.prototype.remove_selection = function() {
    var nlist = [];
    for(var i in this.added_results){
        if(this.added_results[i].marked){
            this.added_results[i].remove();
        }
        else
            nlist.push(this.added_results[i]);
    }
    this.added_results = nlist;
    if(this.added_results.length == 0){
        this.list.hide();
    }
};

ExperimentSearch.prototype.show = function() {
    var esearch = this;
    this.finder.dialog({
                width: 800,
                });
};

$(function() {
    $("#chosen_list").hide();
    $("#result_list").hide();
    var web_url = $("#webservice_url").text();

    var esearch = new ExperimentSearch($("#experiment_search"), $("#chosen_list"), web_url);

    $("#choose_experiments").click(function(){
        esearch.show();
    });
    $("#remove_selected").click(function(){
        esearch.remove_selection();
    });
});
