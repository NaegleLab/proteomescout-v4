
function get_auto_completions(field_type, target_field, value) {
	if(window.autocompletions[field_type] == undefined){
		$.get(window.autocomplete_url + field_type, function(data){
			values = data[field_type];
			window.autocompletions[field_type] = values;
			$(target_field).autocomplete({ source: window.autocompletions[field_type] });
		}, 'json');
	}else{
		$(target_field).autocomplete({ source: window.autocompletions[field_type] });
	}
}

$(document).ready(function(){
	window.autocompletions = {}
	window.autocomplete_url = $("#webservice_url").text() + "/autocomplete/"
	
	$("#add_condition").click(function(){
		$(".condition.hidden").first().removeClass("hidden")
	});
	
	$(".cond_type")
		.change(function(){
			var v = $(this).val();
			var target = $(this).siblings(".cond_value");
			if(v != '')
				get_auto_completions(v, target);
			
		}).each(function(){
			var v = $(this).val();
			var target = $(this).siblings(".cond_value");
			if(v != '')
				get_auto_completions(v, target);
		});
	
	$(".remove_condition").click(function(){
		var parent = $(this).parent()
		parent.children('select').val('')
		parent.children('input[type="text"]').val('')
		parent.remove()
	});
});
