function setVisibility(value, parent_id){
	if(value == 'stddev' || value == 'data' || value=='numeric' || value=='nominative' || value=='clustering'){
		$('#{0} input.label'.format(parent_id)).show();
    }else if(value == 'hidden'){
		$('.{0}'.format(parent_id)).children().hide();
		$('.{0}'.format(parent_id)).children('.expander').show();
	}else
		$('#{0} input.label'.format(parent_id)).hide();
}


$(document).ready(function(){
	$(".expander")
		.click(function(){
			show_id = $(this).attr('id');
			$('.{0}'.format(show_id)).children().show()
			$(this).hide()
			$('.{0} select'.format(show_id)).val('none')
			$(".{0} select".format(show_id)).change()
		});
	
	$(".coldef select")
		.change(function(){
			value = $(event.target, 'option:selected').val();
			parent_id = $(event.target).parent().attr('id')
			setVisibility(value, parent_id);
		});
	$(".coldef select")
		.each(function(){
			value = $(this, 'option:selected').val();
			parent_id = $(this).parent().attr('id')
			setVisibility(value, parent_id);
		})
});
