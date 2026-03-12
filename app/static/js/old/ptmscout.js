
function create_amino_acid_colors(){
    var colors = d3.scale.ordinal();

    colors.domain([
                    'E','D',
                    'R','H','K',
                    'G','A',
                    'T','S','C',
                    'V','L','I','M','P', 
                    'Y','F','W',
                    'Q','N',
                    '-'
                ]);

    var acidic = "#d62728";
    var basic = "#6b6ecf";
    var small = "#7f7f7f";
    var nucleophilic = "#ff7f0e";
    var hydrophobic = "#292929";
    var aromatic = "#c49c94";
    var amide = "#ce6dbd";
    var other = "#000000";
    colors.range([
                    acidic, acidic,
                    basic, basic, basic,
                    small, small,
                    nucleophilic, nucleophilic, nucleophilic,
                    hydrophobic, hydrophobic, hydrophobic, hydrophobic, hydrophobic,
                    aromatic, aromatic, aromatic,
                    amide, amide,
                    other
            ]);

    return colors;
}

(function( $ ) {
    $.widget( "ui.combobox", {
        _create: function() {
          var input,
            that = this,
            wasOpen = false,
            select = this.element.hide(),
            selected = select.children( ":selected" ),
            value = selected.val() ? selected.text() : "",
            wrapper = this.wrapper = $( "<span>" )
              .addClass( "ui-combobox" )
              .insertAfter( select );
   
          function removeIfInvalid( element ) {
            var value = $( element ).val(),
              matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( value ) + "$", "i" ),
              valid = false;
            select.children( "option" ).each(function() {
              if ( $( this ).text().match( matcher ) ) {
                this.selected = valid = true;
                return false;
              }
            });
   
            if ( !valid ) {
              // remove invalid value, as it didn't match anything
              $( element )
                .val( "" )
                .attr( "title", value + " didn't match any item" )
                .tooltip( "open" );
              select.val( "" );
              setTimeout(function() {
                input.tooltip( "close" ).attr( "title", "" );
              }, 2500 );
              input.data( "ui-autocomplete" ).term = "";
            }
          }
   
          input = $( "<input>" )
            .appendTo( wrapper )
            .val( value )
            .attr( "title", "" )
            .addClass( "ui-state-default ui-combobox-input" )
            .autocomplete({
              delay: 0,
              minLength: 0,
              source: function( request, response ) {
                var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
                response( select.children( "option" ).map(function() {
                  var text = $( this ).text();
                  if ( this.value && ( !request.term || matcher.test(text) ) )
                    return {
                      label: text.replace(
                        new RegExp(
                          "(?![^&;]+;)(?!<[^<>]*)(" +
                          $.ui.autocomplete.escapeRegex(request.term) +
                          ")(?![^<>]*>)(?![^&;]+;)", "gi"
                        ), "<strong>$1</strong>" ),
                      value: text,
                      option: this
                    };
                }) );
              },
              select: function( event, ui ) {
                ui.item.option.selected = true;
                that._trigger( "selected", event, {
                  item: ui.item.option
                });
              },
              change: function( event, ui ) {
                if ( !ui.item ) {
                  removeIfInvalid( this );
                }
              }
            })
            .addClass( "ui-widget ui-widget-content ui-corner-left" );
   
          input.data( "ui-autocomplete" )._renderItem = function( ul, item ) {
            return $( "<li>" )
              .append( "<a>" + item.label + "</a>" )
              .appendTo( ul );
          };
   
          $( "<a>" )
            .attr( "tabIndex", -1 )
            .attr( "title", "Show All Items" )
            .tooltip()
            .appendTo( wrapper )
            .button({
              icons: {
                primary: "ui-icon-triangle-1-s"
              },
              text: false
            })
            .removeClass( "ui-corner-all" )
            .addClass( "ui-corner-right ui-combobox-toggle" )
            .mousedown(function() {
              wasOpen = input.autocomplete( "widget" ).is( ":visible" );
            })
            .click(function() {
              input.focus();
   
              // close if already visible
              if ( wasOpen ) {
                return;
              }
   
              // pass empty string as value to search for, displaying all results
              input.autocomplete( "search", "" );
            });
   
          input.tooltip({
            tooltipClass: "ui-state-highlight"
          });
        },
   
        _destroy: function() {
          this.wrapper.remove();
          this.element.show();
        }
      });
  })( jQuery );

Array.max = function( array ){
    return Math.max.apply( Math, array );
};
Array.min = function( array ){
    return Math.min.apply( Math, array );
};

Array.unique = function( array ){
	return array.filter(function(itm,i,a){
			return i==a.indexOf(itm);
		});
};

String.prototype.format = function() {
	  var args = arguments;
	  return this.replace(/{(\d+)}/g, function(match, number) { 
	    return typeof args[number] != 'undefined'
	      ? args[number]
	      : match
	    ;
	  });
	};

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

String.prototype.startsWith = function(str) {
    return this.indexOf(str) == 0;
};

function done_waiting(){
    $(".waiting-modal").hide();
}

function getUniqueId(){
	return "ptmscout{0}".format(window.uniqueId++);
}

$(function(){
    $( document ).tooltip({
                track: true
            });

    $(".longtask")
        .on('click', function(e) {
            $(".waiting-modal").show();
        });

    $("div.progress").each(function(){
            var val = $(this).text();
            $(this).text("");
            var items = val.split(" / ");
            var n = parseInt(items[0]);
            var d = parseInt(items[1]);
            
            if(n == 0){
                $(this).progressbar({ value: false });
            }else{
                $(this).progressbar({ value: n, max: d});
            }
        });

    window.uniqueId = 0;

    $(".autocomplete").each(function(){
        var values = $(this).attr('data-values').split(',');
        $(this).autocomplete({ source: values });
    });
});


$(function(){
  $('#nav .link_menu a, #subnav .link_menu a, #menu .link_menu a').each( function(index, link) { if ( $(link).attr('href') == window.location.href ) { $(link).addClass('nav_active'); } } );
});