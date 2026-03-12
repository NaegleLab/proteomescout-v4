function TrackViewer(structure_viewer, svg_container, offset, cls) {
    this.baseline = offset;
    this.structure_viewer = structure_viewer;
    this.selector = ".{0}".format(cls);
    this.viewer =
            svg_container
                .append('g')
                    .attr('class', cls)
                    .attr('transform', 'translate(0,{0})scale(1,1)'.format(this.baseline));
    this.axis = d3.scaleLinear().domain(structure_viewer.axis.domain()).range(structure_viewer.axis.range());

    this.tracks = [];
};

TrackViewer.prototype.animate_position = function(t, npos, timedelay) {
    this.baseline=npos;

    t = t.transition().delay(timedelay);

    var ntransform = 'translate(0,{0})scale(1,1)'.format(this.baseline);
    t.select(this.selector)
        .attrTween('transform', function() { return d3.interpolateString(ntransform)});
};

TrackViewer.prototype.set_position = function(npos) {
    this.baseline=npos;
    this.viewer.attr('transform', 'translate(0,{0})scale(1,1)'.format(this.baseline));
};

TrackViewer.prototype.get_height = function() {
    var h = 0;
    for(var i in this.tracks){
        var tr = this.tracks[i];
        if(tr.visible) {
            h += tr.height;
        }
    }
    return h;
};

TrackViewer.prototype.hide = function() {
    this.viewer.style('opacity', '0');
};

TrackViewer.prototype.show = function() {
    this.viewer.style('opacity', '1');
};

TrackViewer.prototype.view_residues = function(residue, width) {
    this.axis.domain([residue, residue+width]);

    for(var i in this.tracks) {
        this.tracks[i].update_display(this.axis, this.structure_viewer.width);
    }
};

TrackViewer.prototype.add_track = function(track) {
    this.tracks.push(track);
    pos = this.get_track_position(track.name);

    track.g.attr('transform', 'translate(0,{0})'.format(pos));
}

TrackViewer.prototype.get_track_position = function(track_name) {
    var npos = 0;
    for(var i in this.tracks){
        if(this.tracks[i].name == track_name){
            return npos;
        }else if(this.tracks[i].visible){
            npos += this.tracks[i].height;
        }
    }
}

TrackViewer.prototype.get_track = function(track_name) {
    for(var i in this.tracks){
        if(this.tracks[i].name == track_name){
            return this.tracks[i];
        }
    }
}

TrackViewer.prototype.toggle_track = function(t, track_name, mode) {
    var track = this.get_track(track_name);
    var track_pos = this.get_track_position(track_name);
    var ntransform;
    var ctransform;
    var npos = 0;
    var offscreen_pos = (this.structure_viewer.protein_data.seq.length / 50) * this.structure_viewer.width;

    track.visible = mode;

    // Filter Tracks: adding track to graph
    if(mode){
        track_pos = undefined;

        for(var i in this.tracks){
            var hpos = 0;

            if(this.tracks[i].name == track_name){
                hpos = offscreen_pos;
                track_pos = npos;
            }   

            if(this.tracks[i].visible){
                ntransform = 'translate({0}, {1})'.format(hpos, npos);
                console.log('add track transform ' + ntransform)
                t.select(this.tracks[i].selector)
                    .attr('transform', ntransform);
                npos += this.tracks[i].height;
            }
        }

        t = t.transition().delay(250);
        
        ntransform = 'translate(0, {0})'.format(track_pos);
        console.log('add track transform ' + ntransform)
        t.select(track.selector)
            .attr('transform', ntransform);

        t = t.transition().delay(500);
        t.select(track.selector)
            .style('opacity', 1);

    //Filter Tracks: removing a track
    } else {
        ctransform = track.g.attr('transform');
        ntransform = 'translate({0},{1})'.format(offscreen_pos, track_pos);

        t.select(track.selector)
                .style('opacity', 0);

        t = t.transition().delay(250);
        console.log('remove track transform ' + ntransform)
        t.select(track.selector)
            .attr('transform', ntransform);

        t = t.transition().delay(500);
        npos = 0;
        for(var i in this.tracks){
            if(this.tracks[i].visible && this.tracks[i].name != track_name){
                ntransform = 'translate(0, {0})'.format(npos);
                console.log('remove track transform ' + ntransform)
                t.select(this.tracks[i].selector)
                    .attr('transform', ntransform);
                npos += this.tracks[i].height;
            }
        }
    }
}

function StructureViewer(protein_data) {
    console.log(protein_data)

    this.protein_data = protein_data;
    this.show_residues_size_limit = 100;
    this.macro_viewer_position = 0;

    this.transition_duration = 250;

    this.last_zoom_residue = 0;
    this.last_zoom_width = 50;

    this.width = 900;
    this.svg = d3.select('.protein_viewer .viewer').append("svg")
      .attr("width", this.width)
      .attr("height", 0)
    // this.svg.append("circle")
    //   .attr("cx", 140).attr("cy", 70).attr("r", 40).style("fill", "red");

    // this.svg =
    // d3.select('.protein_viewer .viewer')
    //             .append("svg")
    //                 // .attr('version', "1.1")
    //                 // .attr('xmlns', "http://www.w3.org/2000/svg")
    //                 .attr('width', this.width)
    //                 .attr('height', 0);

    this.svg_container =
                this.svg.append('g')
                    .attr('class', 'viewer_svg')
                    .style('font-family', "helvetica,arial,verdana")
                    .style('font-size', "12pt");
    
    // this.svg_container.append("circle")
    //     .attr("cx", 170).attr("cy", 70).attr("r", 40).style("fill", "blue");

    




    this.axis = d3.scaleLinear().domain([0, protein_data.seq.length]).range([0, this.width]);
    
    this.domain_colors = d3.scaleOrdinal(d3.schemeSet2); //was schemeCategory20
    this.region_colors =  d3.scaleOrdinal(d3.schemePaired); //was schemeCategory20b
    this.residue_colors = create_amino_acid_colors();

    var macro_residues = this.protein_data.seq.length <= this.show_residues_size_limit;
    this.macro_viewer = new TrackViewer(this, this.svg_container, this.macro_viewer_position, 'macro_track_viewer', macro_residues);
    this.create_empty_track(this.macro_viewer);
    this.create_ptm_track(this.macro_viewer);
    this.create_residue_track(this.macro_viewer, this.show_residues_size_limit >= this.protein_data.seq.length);

    this.create_mutation_track(this.macro_viewer, macro_residues);
    this.create_scansite_track(this.macro_viewer, macro_residues);

    this.create_activation_loop_track(this.macro_viewer);
    this.create_uniprot_domain_track(this.macro_viewer);
//    this.create_ncbi_domain_track(this.macro_viewer);
    this.create_domain_track(this.macro_viewer);

    this.create_region_track(this.macro_viewer, "Uniprot Structure", "uniprot_structure")
    this.create_region_track(this.macro_viewer, "Uniprot Binding Sites", "uniprot_sites")
    this.create_region_track(this.macro_viewer, "Uniprot Macrostructure", "uniprot_macro")
    this.create_region_track(this.macro_viewer, "Uniprot Topology", "uniprot_topological")

    this.macro_viewer.view_residues(0, protein_data.seq.length);

    this.zoom_viewer = new TrackViewer(this, this.svg_container, 0, 'zoom_track_viewer', true);
    this.zoom_viewer.view_residues(this.last_zoom_residue, this.last_zoom_width);

    this.create_empty_track(this.zoom_viewer);
    this.create_ptm_track(this.zoom_viewer);
    this.create_residue_track(this.zoom_viewer, true);

    this.create_mutation_track(this.zoom_viewer, true);
    this.create_scansite_track(this.zoom_viewer, true);
    
    this.create_activation_loop_track(this.zoom_viewer);
    this.create_uniprot_domain_track(this.zoom_viewer);
//    this.create_ncbi_domain_track(this.zoom_viewer);
    this.create_domain_track(this.zoom_viewer);

    this.create_region_track(this.zoom_viewer, "Uniprot Structure", "uniprot_structure")
    this.create_region_track(this.zoom_viewer, "Uniprot Binding Sites", "uniprot_sites")
    this.create_region_track(this.zoom_viewer, "Uniprot Macrostructure", "uniprot_macro")
    this.create_region_track(this.zoom_viewer, "Uniprot Topology", "uniprot_topological")

    this.zoom_viewer.hide();
    this.zoom_enabled = false;

    this.set_viewer_height(this.get_current_height(), function() {}, 0);

    var viewer = this;
    function drag_start() {
        viewer.zx = null;
    }
    function drag_over() {
        viewer.ox = d3.event.x;

        if(viewer.zx == null){
            viewer.zx = d3.event.x;

            viewer.zoom_drag = viewer.svg_container.append('rect')
                .attr('x', viewer.zx)
                .attr('y', 0)
                .attr('width', 1)
                .attr('height', viewer.macro_viewer.get_height())
                .style('fill', '#00ff00')
                .style('opacity', '0.3');

        }
        else{
            if(viewer.ox < viewer.zx){
                viewer.zoom_drag
                            .attr('x', viewer.ox)
                            .attr('width', viewer.zx - viewer.ox);
            }else{
                viewer.zoom_drag
                            .attr('x', viewer.zx)
                            .attr('width', viewer.ox - viewer.zx);
            }
        }
    }
    function drag_end() {
        if(viewer.zx != null) {

            if(viewer.ox < viewer.zx){
                var tmp = viewer.ox;
                viewer.ox = viewer.zx;
                viewer.zx = tmp;
            }

            var npos = viewer.axis.invert(viewer.zx);
            var nwidth = viewer.axis.invert(viewer.ox) - npos;
            if(nwidth < 50){
                npos -= (50 - nwidth) / 2
                nwidth = 50;
            }
            if(npos < 0){
                npos = 0;
            }

            if(npos + nwidth > viewer.protein_data.seq.length){
                npos = viewer.protein_data.seq.length - nwidth;
            }

            viewer.last_zoom_residue = npos;
            viewer.last_zoom_width = nwidth;
            viewer.zoom_viewer.view_residues(viewer.last_zoom_residue, viewer.last_zoom_width);

            if(!viewer.zoom_enabled)
                viewer.zoom_on();
            else
                viewer.zoom_window.update_window(viewer.last_zoom_residue, viewer.last_zoom_width, viewer.axis);

            viewer.zoom_drag.remove();
        }
    }

    drag_behavior =
        d3.drag()
            .on("start", drag_start)
            .on("drag", drag_over)
            .on("end", drag_end);

    this.svg.call(drag_behavior);
};

StructureViewer.prototype.get_current_height = function() {
    var height = this.macro_viewer.get_height();
    if(this.zoom_enabled){
        height += this.zoom_viewer.get_height();
    }
    return height;
};

StructureViewer.prototype.create_ptm_track = function(track_viewer) {
    console.log("in StructureViewer creating PTMTrack")
    ptm_track = new PTMTrack('PTMs', track_viewer.viewer, this.protein_data);
    ptm_track.create(track_viewer.axis, this.width, this.residue_colors);
    track_viewer.add_track(ptm_track);
};

StructureViewer.prototype.create_mutation_track = function(track_viewer, show_residues) {
    
    mutation_track = new MutationTrack('Mutations', track_viewer.viewer, this.protein_data);
    mutation_track.create(track_viewer.axis, this.width, show_residues);
    track_viewer.add_track(mutation_track);
};

StructureViewer.prototype.create_scansite_track = function(track_viewer, show_residues) {
    scansite_track = new ScansiteTrack('Scansite', track_viewer.viewer, this.protein_data);
    scansite_track.create(track_viewer.axis, this.width, show_residues);
    track_viewer.add_track(scansite_track);
};

StructureViewer.prototype.create_residue_track = function(track_viewer, show_residues) {
    residue_track = new ResidueTrack('Residues', track_viewer.viewer, this.protein_data);
    residue_track.create(track_viewer.axis, this.width, show_residues);
    track_viewer.add_track(residue_track);
};

StructureViewer.prototype.create_activation_loop_track = function(track_viewer) {
    region_track = new RegionTrack('Activation Loops', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'activation_loops');
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_uniprot_domain_track = function(track_viewer) {
    region_track = new RegionTrack('Uniprot Domains', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'uniprot_domains');
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_ncbi_domain_track = function(track_viewer) {
    region_track = new RegionTrack('Entrez Domains', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'ncbi_domains');
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_region_track = function(track_viewer, name, region_name) {
    region_track = new RegionTrack(name, track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, region_name);
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_domain_track = function(track_viewer) {
    domain_track = new DomainTrack('PFam Domains', track_viewer.viewer, this.protein_data);
    domain_track.create(track_viewer.axis, this.width, this.domain_colors);
    track_viewer.add_track(domain_track);
};

StructureViewer.prototype.create_empty_track = function(track_viewer) {
    empty_track = new EmptyTrack('None', track_viewer.viewer, this.protein_data);
    track_viewer.add_track(empty_track);
};



StructureViewer.prototype.set_viewer_height = function(nheight, callback, delay) {
    console.log('setting height' + nheight )
    $('.protein_viewer svg').delay(delay).animate({ height: nheight }, 250, callback);
    d3.selectAll('.protein_viewer svg').transition()
        .duration(delay)
}

StructureViewer.prototype.zoom_off = function(){
    if(this.zoom_enabled){
        this.zoom_enabled=false;

        this.last_zoom_residue = this.zoom_window.residue;
        this.last_zoom_width = this.zoom_window.width;

        var viewer = this;


        this.set_viewer_height(this.get_current_height(),
                    function() {
                        viewer.zoom_window.remove();
                        viewer.zoom_viewer.hide();
                      }, 0
                );
    }
}

StructureViewer.prototype.export_svg = function() {
   var chart = d3.select('.protein_viewer .viewer')
   var id = "#" + chart.attr('id');

   if($(id + " svg style").size() == 0){
       css_url = $("#protein_viewer_css_export_url").text()

       $.get(css_url,
           function(data) {
               $(id + " svg").append("<style>" + data + "</style>");
               displaySVG(id);
           }
       ).error(function() {
           alert("Request ERROR: unable to load stylesheet. Please try again.")
       });

   } else {
       displaySVG(id);
   }
};

StructureViewer.prototype.zoom_on = function() {
    if(!this.zoom_enabled){
        this.zoom_enabled=true;

        var mp = this.macro_viewer.get_height();
        this.zoom_window = new ZoomWindow(this, this.svg_container, this.last_zoom_residue, this.last_zoom_width, mp);
        this.zoom_viewer.set_position(mp);
        this.zoom_viewer.show();

        this.set_viewer_height(this.get_current_height(), function() { }, 0);
    }
};

StructureViewer.prototype.toggle_ptm = function(ptm_name, mode) {
    track = this.macro_viewer.get_track('PTMs');
    track.toggle_ptm(ptm_name, mode);

    track = this.zoom_viewer.get_track('PTMs');
    track.toggle_ptm(ptm_name, mode);

    this.macro_viewer.get_track('PTMs').update_values( this.transition_duration );
    this.zoom_viewer.get_track('PTMs').update_values( this.transition_duration );
}

StructureViewer.prototype.toggle_exp = function(exp_id, mode){
    track = this.macro_viewer.get_track('PTMs');
    track.toggle_exp(exp_id, mode);

    track = this.zoom_viewer.get_track('PTMs');
    track.toggle_exp(exp_id, mode);

    this.macro_viewer.get_track('PTMs').update_values( this.transition_duration );
    this.zoom_viewer.get_track('PTMs').update_values( this.transition_duration );
}

StructureViewer.prototype.toggle_track = function(track_name, mode){
    t = this.svg_container.transition()
              .duration(this.transition_duration);

    var track_height = this.macro_viewer.get_track(track_name).height;

    this.macro_viewer.toggle_track(t, track_name, mode);
    this.zoom_viewer.toggle_track(t, track_name, mode);

    var mvh = this.macro_viewer.get_height();
    var cvh = this.get_current_height();
    if(mode){
        this.zoom_viewer.animate_position(t, mvh, 0);
        this.set_viewer_height(cvh, function(){}, 0);

        if(this.zoom_enabled){
            this.zoom_window.animate_height(t, mvh, 0);
        }
    } else {
        this.zoom_viewer.animate_position(t, mvh, 500);
        this.set_viewer_height(cvh, function(){}, 500);
        if(this.zoom_enabled){
            this.zoom_window.animate_height(t, mvh, 500);
        }
    }
};

$(function(){
    $('.zoomout-tool').button({ icons: { primary: 'ui-icon-zoomout' }, text:false })
                      .click(function(){
                         window.structure_viewer.zoom_off();
                       });

    // $('.ptm-tool').button()
    //               .click(function(){
    //                 $('.mods').dialog()
    //               });
    // $('.exp-tool').button()
    //               .click(function(){
    //                 $('.exps').dialog()
    //               });
    // $('.track-tool').button()
    //               .click(function(){
    //                 $('.tracks').dialog()
    //               });

    $('.svg-tool').button()
                    .click(function(){
                        window.structure_viewer.export_svg();
                    });

    $('.help-tool').button({ icons: { primary: 'ui-icon-help' }, text:false });

    // $('.mods').toggle();
    // $('.exps').toggle();
    // $('.tracks').toggle();

    
    $('.tracks input').change( function() {
        track = $(this).attr('id');
        $("#test").text(track);
        mode = $(this).is(':checked');
        window.structure_viewer.toggle_track(track, mode);
    });

    $('.mods input.modtoggle').change(
        function(){
            $(this).text('changed');
            mode = $(this).is(':checked');
            ptm = $(this).attr('id').replace("_"," ");
            window.structure_viewer.toggle_ptm(ptm, mode);
        });

    $('.exps input.exptoggle').change(
        function(){
            mode = $(this).is(':checked');
            exp = $(this).attr('id').substring(1);
            window.structure_viewer.toggle_exp( parseInt(exp), mode );
        });

    // ptm modal select all
    $('.mods button.all').click(
        function(){
            $(".mods input.modtoggle").each(
                function(){
                    if(! $(this).is(':checked')) $(this).click();
                });
        });
    // ptm modal hide all
    $('.mods button.none').click(
        function(){
            $(".mods input.modtoggle").each(
                function(){
                    if($(this).is(':checked')) $(this).click();
                });
        });

    // experiment modal select all
    $('.exps button.all').click(
        function(){
            $(".exps input.exptoggle").each(
                function(){
                    if(! $(this).is(':checked')) $(this).click();
                });
        });
    // experiment modal hide all
    $('.exps button.none').click(
        function(){
            $(".exps input.exptoggle").each(
                function(){
                    if($(this).is(':checked')) $(this).click();
                });
        });

    // track modal select all
    $('.tracks button.all').click(
        function(){
            $(".tracks input.tracktoggle").each(
                function(){
                    if(! $(this).is(':checked')) $(this).click();
                });
        });

    // track modal hide all 
    $('.tracks button.none').click(
        function(){
            $(".tracks input.tracktoggle").each(
                function(){
                    if($(this).is(':checked')) $(this).click();
                });
        });

    $('.protein_viewer').each( function() {
        
        data = document.querySelector('#structure_data')
        json_data = JSON.parse( data.dataset.structure );

        window.structure_viewer = new StructureViewer( json_data );
        if(json_data.experiment != null && json_data.experiment != undefined){
            $('.exps input.exptoggle').each(
                function(){
                    exp = parseInt($(this).attr('id').substring(1));
                    if(exp != json_data.experiment)
                        $(this).click();
                });
        }
    });
});
