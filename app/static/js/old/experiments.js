function hideAll(element) {
	var experiment_id = element.attr('id');
    element.hide();
    element.find('button.expand').text("+");
    $("tr.experiment[parent=\"{0}\"]".format(experiment_id)).each(function(){
        hideAll($(this));
    });
}
function toggleVisible(element) {
	var experiment_id = element.attr('id');
    var selector = "tr.experiment[parent=\"{0}\"]".format(experiment_id);
    var exp_mode = element.find('button.expand').text();

	if(exp_mode === "+"){
		element.find('button.expand').text("-");
        $(selector).show();
    }
	else{
		element.find('button.expand').text("+");
        $(selector).each(function(){
            hideAll($(this));
        });
    }
}

function timedRefresh(timeoutPeriod) {
    setTimeout("location.reload(true);",timeoutPeriod);
}

$(document).ready(
	function(){
		$("button.expand").click(
				function(){
					toggleVisible($(this).closest('tr'));
					return false;
				});
		$("tr.experiment[parent]").hide();
		
        if( $("div.progress").length > 0 ){
            timedRefresh(10000);
        }
	});
