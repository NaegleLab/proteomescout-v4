$(function(){
   $("div.compare_result").each(function(){
        if($(this).hasClass('experiment_result')){
            var result_table=$(this).find("table.protein_list");
            $(this).find("button.show_results")
                    .on('click', function(){
                       if(result_table.hasClass('hidden')){
                           result_table.removeClass('hidden');
                           result_table.show();
                           $(this).text("Hide")
                       } else {
                           result_table.addClass('hidden');
                           $(this).text("Show")
                           result_table.hide();
                       }
                    });
        }
   });
});
