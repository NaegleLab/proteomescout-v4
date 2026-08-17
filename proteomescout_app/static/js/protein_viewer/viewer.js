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
        this.export_dpi = 300;
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
    // Fixed, colorblind-safe mapping for UniProt secondary structure types.
    this.uniprot_structure_colors = {
        helix: '#0072B2',
        strand: '#E69F00',
        turn: '#CC79A7',
    };
    this.exon_palette = [
        '#4E79A7',
        '#F28E2B',
        '#76B7B2',
        '#E15759',
        '#59A14F',
        '#EDC948',
        '#B07AA1',
        '#FF9DA7',
        '#9C755F',
        '#BAB0AC'
    ];
    this.residue_colors = create_amino_acid_colors();

    var macro_residues = this.protein_data.seq.length <= this.show_residues_size_limit;
    this.macro_viewer = new TrackViewer(this, this.svg_container, this.macro_viewer_position, 'macro_track_viewer', macro_residues);
    this.create_empty_track(this.macro_viewer);
    this.create_ptm_track(this.macro_viewer);
    this.create_residue_track(this.macro_viewer, this.show_residues_size_limit >= this.protein_data.seq.length);
    this.create_spyc_predictions_track(this.macro_viewer);

    this.create_activation_loop_track(this.macro_viewer);
    this.create_uniprot_domain_track(this.macro_viewer);
//    this.create_ncbi_domain_track(this.macro_viewer);
    this.create_domain_track(this.macro_viewer);

    this.create_region_track(this.macro_viewer, "Uniprot Structure", "uniprot_structure")
    this.create_region_track(this.macro_viewer, "Macro Molecular", "macro_molecular")
    this.create_region_track(this.macro_viewer, "Exons", "exons")

    this.macro_viewer.view_residues(0, protein_data.seq.length);

    this.zoom_viewer = new TrackViewer(this, this.svg_container, 0, 'zoom_track_viewer', true);
    this.zoom_viewer.view_residues(this.last_zoom_residue, this.last_zoom_width);

    this.create_empty_track(this.zoom_viewer);
    this.create_ptm_track(this.zoom_viewer);
    this.create_residue_track(this.zoom_viewer, true);
    this.create_spyc_predictions_track(this.zoom_viewer);
    
    this.create_activation_loop_track(this.zoom_viewer);
    this.create_uniprot_domain_track(this.zoom_viewer);
//    this.create_ncbi_domain_track(this.zoom_viewer);
    this.create_domain_track(this.zoom_viewer);

    this.create_region_track(this.zoom_viewer, "Uniprot Structure", "uniprot_structure")
    this.create_region_track(this.zoom_viewer, "Macro Molecular", "macro_molecular")
    this.create_region_track(this.zoom_viewer, "Exons", "exons")

    this.zoom_viewer.hide();
    this.zoom_enabled = false;

    this.autohide_empty_tracks();

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
    ptm_track.has_content = Object.keys(this.protein_data.mods || {}).length > 0;
    track_viewer.add_track(ptm_track);
};

StructureViewer.prototype.create_spyc_predictions_track = function(track_viewer) {
    var size_options = track_viewer === this.zoom_viewer
        ? { min_radius: 4.0, max_radius: 9.0 }
        : { min_radius: 3.0, max_radius: 6.6 };

    var spyc_track = new SpyCPredictionTrack('Spy-C Predictions', track_viewer.viewer, this.protein_data, size_options);
    spyc_track.create(track_viewer.axis, this.width);
    spyc_track.has_content = Object.keys(this.protein_data.spyc_predictions || {}).length > 0;
    track_viewer.add_track(spyc_track);
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
    residue_track.has_content = true;
    track_viewer.add_track(residue_track);
};

StructureViewer.prototype.create_activation_loop_track = function(track_viewer) {
    var loops = (this.protein_data.regions || {}).activation_loops || [];
    region_track = new RegionTrack('Activation Loops', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'activation_loops');
    region_track.has_content = loops.length > 0;
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_uniprot_domain_track = function(track_viewer) {
    region_track = new RegionTrack('Uniprot Domains', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'uniprot_domains');
    region_track.has_content = (((this.protein_data.regions || {}).uniprot_domains) || []).length > 0;
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_ncbi_domain_track = function(track_viewer) {
    region_track = new RegionTrack('Entrez Domains', track_viewer.viewer, this.protein_data);
    region_track.create(track_viewer.axis, this.width, this.region_colors, 'ncbi_domains');
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_region_track = function(track_viewer, name, region_name) {
    region_track = new RegionTrack(name, track_viewer.viewer, this.protein_data);

    var fallback_region_colors = this.region_colors;
    var color_fn = function(region) {
        return fallback_region_colors(region.label);
    };
    if (region_name === 'macro_molecular') {
        var macro_regions = ((this.protein_data.regions || {})[region_name]) || [];
        var macro_labels = [];
        for (var i = 0; i < macro_regions.length; i++) {
            var label = macro_regions[i].label;
            if (label && macro_labels.indexOf(label) === -1) {
                macro_labels.push(label);
            }
        }

        if (macro_labels.length) {
            var macro_palette = [
                '#4E79A7',
                '#F28E2B',
                '#E15759',
                '#76B7B2',
                '#59A14F',
                '#EDC948',
                '#B07AA1',
                '#FF9DA7',
                '#9C755F',
                '#BAB0AC'
            ];
            var macro_region_colors = {};
            for (var j = 0; j < macro_labels.length; j++) {
                macro_region_colors[macro_labels[j]] = macro_palette[j % macro_palette.length];
            }

            color_fn = function(region) {
                return macro_region_colors[region.label] || fallback_region_colors(region.label);
            };
        }
    }

    if (region_name === 'exons') {
        var exon_palette = this.exon_palette;
        var exon_regions = ((this.protein_data.regions || {})[region_name]) || [];
        var exon_color_map = {};
        for (var k = 0; k < exon_regions.length; k++) {
            var exon_label = exon_regions[k].label;
            if (exon_label && !exon_color_map[exon_label]) {
                exon_color_map[exon_label] = exon_palette[Object.keys(exon_color_map).length % exon_palette.length];
            }
        }

        color_fn = function(region) {
            return exon_color_map[region.label] || exon_palette[0];
        };
    }

    if (region_name === 'uniprot_structure') {
        var structure_colors = this.uniprot_structure_colors;
        color_fn = function(region) {
            var key = String(region.label || '').toLowerCase();
            return structure_colors[key] || fallback_region_colors(region.label);
        };
    }

    region_track.create(track_viewer.axis, this.width, color_fn, region_name);
    region_track.has_content = (((this.protein_data.regions || {})[region_name]) || []).length > 0;
    track_viewer.add_track(region_track);
};

StructureViewer.prototype.create_domain_track = function(track_viewer) {
    domain_track = new DomainTrack('Interpro Domains', track_viewer.viewer, this.protein_data);
    domain_track.create(track_viewer.axis, this.width, this.domain_colors);
    domain_track.has_content = ((this.protein_data.domains || []).length > 0);
    track_viewer.add_track(domain_track);
};

StructureViewer.prototype.create_empty_track = function(track_viewer) {
    empty_track = new EmptyTrack('None', track_viewer.viewer, this.protein_data);
    track_viewer.add_track(empty_track);
};

StructureViewer.prototype.track_has_content = function(track_name) {
    var track = this.macro_viewer.get_track(track_name);
    return !!(track && track.has_content);
};

StructureViewer.prototype.autohide_empty_tracks = function() {
    var viewer = this;

    $('.tracks input.tracktoggle').each(function() {
        var track_name = $(this).attr('id');
        if (!viewer.track_has_content(track_name) && $(this).is(':checked')) {
            $(this).prop('checked', false);
            viewer.toggle_track(track_name, false);
        }
    });
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

StructureViewer.prototype._parse_svg_length = function(value) {
    if (value === undefined || value === null || value === '') {
        return null;
    }

    var parsed = parseFloat(value);
    if (isNaN(parsed) || !isFinite(parsed)) {
        return null;
    }
    return parsed;
};

StructureViewer.prototype._scale_style_value = function(value, scaleFactor) {
    if (!value || value === 'none') {
        return null;
    }

    var match = String(value).trim().match(/^(-?\d*\.?\d+)([a-z%]*)$/i);
    if (!match) {
        return null;
    }

    var numericValue = parseFloat(match[1]);
    var unit = match[2] || '';
    return (numericValue * scaleFactor) + unit;
};

StructureViewer.prototype._clamp_font_size_min_pt = function(value, minPt, pointsPerUserUnit) {
    if (!value) {
        return value;
    }

    var match = String(value).trim().match(/^(-?\d*\.?\d+)([a-z%]*)$/i);
    if (!match) {
        return value;
    }

    var numericValue = parseFloat(match[1]);
    var unit = (match[2] || '').toLowerCase();
    if (isNaN(numericValue) || !isFinite(numericValue)) {
        return value;
    }

    var safePointsPerUserUnit = pointsPerUserUnit;
    if (!safePointsPerUserUnit || !isFinite(safePointsPerUserUnit) || safePointsPerUserUnit <= 0) {
        safePointsPerUserUnit = 0.75; // Fallback for legacy 96dpi-like user unit mapping.
    }
    var minUserUnits = minPt / safePointsPerUserUnit;

    function toUserUnits(number, unitName) {
        if (unitName === 'pt') {
            return number * (96 / 72);
        }
        if (unitName === 'in') {
            return number * 96;
        }
        if (unitName === 'cm') {
            return number * (96 / 2.54);
        }
        if (unitName === 'mm') {
            return number * (96 / 25.4);
        }
        if (unitName === 'pc') {
            return number * 16;
        }
        if (unitName === 'q') {
            return number * (96 / 101.6);
        }
        if (unitName === 'px' || unitName === '') {
            return number;
        }
        return null;
    }

    var numericInUserUnits = toUserUnits(numericValue, unit);
    if (numericInUserUnits !== null) {
        return Math.max(numericInUserUnits, minUserUnits) + 'px';
    }

    // For uncommon units where reliable conversion is ambiguous, enforce directly in points.
    return (numericValue < minPt ? minPt + 'pt' : numericValue + unit);
};

StructureViewer.prototype._get_inherited_font_size = function(el) {
    var node = el;
    while (node) {
        if (node.style) {
            var styleSize = node.style.getPropertyValue('font-size');
            if (styleSize) {
                return styleSize;
            }
        }

        var attrSize = node.getAttribute && node.getAttribute('font-size');
        if (attrSize) {
            return attrSize;
        }

        node = node.parentElement;
    }

    return '12pt';
};

StructureViewer.prototype._get_min_export_font_pt = function(exportWidthInches) {
    var widthInches = parseFloat(exportWidthInches);
    if (isNaN(widthInches) || !isFinite(widthInches)) {
        return 8;
    }

    if (widthInches < 4) {
        return 6;
    }
    if (widthInches < 6) {
        return 8;
    }
    if (widthInches <= 8) {
        return 10;
    }
    return 12;
};

StructureViewer.prototype._layout_compact_feature_labels = function(exportedSvg, exportWidthInches) {
    var widthInches = parseFloat(exportWidthInches);
    if (!exportedSvg || isNaN(widthInches) || !isFinite(widthInches) || widthInches > 4) {
        return;
    }

    var viewer = this;

    function estimateTextWidth(textValue, fontSizePx) {
        var content = textValue || '';
        return content.length * fontSizePx * 0.56;
    }

    function fitTextToWidth(label, maxWidthPx, fontSizePx) {
        var fullText = label.getAttribute('data-export-original-text') || label.textContent || '';
        label.setAttribute('data-export-original-text', fullText);

        if (maxWidthPx <= 4) {
            label.textContent = '';
            return;
        }

        if (estimateTextWidth(fullText, fontSizePx) <= maxWidthPx) {
            label.textContent = fullText;
            return;
        }

        var ellipsis = '...';
        var low = 0;
        var high = fullText.length;
        var best = '';

        while (low <= high) {
            var mid = Math.floor((low + high) / 2);
            var candidate = fullText.substring(0, mid) + ellipsis;
            if (estimateTextWidth(candidate, fontSizePx) <= maxWidthPx) {
                best = candidate;
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }

        label.textContent = best;
    }

    function placeInside(featureClass) {
        Array.prototype.forEach.call(exportedSvg.querySelectorAll('g[id^="track"]'), function(trackGroup) {
            var rects = trackGroup.querySelectorAll('rect.' + featureClass);
            var labels = trackGroup.querySelectorAll('text.' + featureClass);
            var count = Math.min(rects.length, labels.length);

            for (var i = 0; i < count; i++) {
                var rect = rects[i];
                var label = labels[i];
                var x = parseFloat(rect.getAttribute('x'));
                var w = parseFloat(rect.getAttribute('width'));
                var y = parseFloat(rect.getAttribute('y'));
                var h = parseFloat(rect.getAttribute('height'));
                var labelFontSize = viewer._parse_svg_length(
                    (label.style && label.style.getPropertyValue('font-size')) || label.getAttribute('font-size')
                ) || 12;
                var verticalOffsetFactor = widthInches < 3.5 ? 0.54 : 0.48;

                if (!isFinite(x) || !isFinite(w) || !isFinite(y) || !isFinite(h)) {
                    continue;
                }

                // Illustrator often ignores dominant-baseline; use an explicit baseline offset
                // so text appears centered inside feature rectangles.
                label.setAttribute('x', x + (w / 2));
                label.setAttribute('y', y + (h / 2) + (labelFontSize * verticalOffsetFactor));
                label.style.setProperty('dominant-baseline', 'auto');
                label.style.setProperty('alignment-baseline', 'baseline');
                label.style.setProperty('text-anchor', 'middle');

                var horizontalPadding = 4;
                fitTextToWidth(label, Math.max(0, w - horizontalPadding), labelFontSize);
            }
        });
    }

    placeInside('domain');
    placeInside('region');
};

StructureViewer.prototype._adjust_export_visual_scale = function(exportedSvg, baseScale, pointsPerUserUnit, minTextPt, exportWidthInches) {
    if (!exportedSvg || !baseScale || !isFinite(baseScale) || baseScale <= 0) {
        return;
    }

    var minFontPt = minTextPt;
    if (!minFontPt || !isFinite(minFontPt) || minFontPt <= 0) {
        minFontPt = 8;
    }

    var textScale = Math.max(1.0, Math.min(1.35, baseScale));
    var strokeScale = Math.max(0.7, Math.min(1.4, baseScale));
    var textCompensation = textScale / baseScale;
    var strokeCompensation = strokeScale / baseScale;
    var widthInches = parseFloat(exportWidthInches);

    Array.prototype.forEach.call(exportedSvg.querySelectorAll('*'), function(el) {
        var textStyle = el.style ? el.style.getPropertyValue('font-size') : '';
        var textAttr = el.getAttribute('font-size');
        var scaledText;
        var effectiveMinFontPt = minFontPt;
        var isResidueLetter = el.classList && el.classList.contains('aminoacid');
        var isResidueTick = false;
        if (el.tagName && el.tagName.toLowerCase() === 'text' && el.classList && el.classList.length) {
            isResidueTick = Array.prototype.some.call(el.classList, function(cls) {
                return /^t\d+$/.test(cls);
            });
        }

        if (isResidueLetter || isResidueTick) {
            effectiveMinFontPt = widthInches < 7 ? Math.max(4, minFontPt - 4) : Math.max(4, minFontPt - 2);
        }

        if (widthInches < 7 && isResidueTick) {
            var tickY = this._parse_svg_length(el.getAttribute('y'));
            if (isFinite(tickY)) {
                el.setAttribute('y', tickY + 4);
            }
        }

        if (textStyle) {
            scaledText = this._scale_style_value(textStyle, textCompensation);
            if (scaledText) {
                scaledText = this._clamp_font_size_min_pt(scaledText, effectiveMinFontPt, pointsPerUserUnit);
                el.style.setProperty('font-size', scaledText);
            }
        }
        if (textAttr) {
            scaledText = this._scale_style_value(textAttr, textCompensation);
            if (scaledText) {
                scaledText = this._clamp_font_size_min_pt(scaledText, effectiveMinFontPt, pointsPerUserUnit);
                el.setAttribute('font-size', scaledText);
            }
        }

        if (!textStyle && !textAttr && el.tagName && el.tagName.toLowerCase() === 'text') {
            var inheritedText = this._get_inherited_font_size(el);
            var scaledInherited = this._scale_style_value(inheritedText, textCompensation) || inheritedText;
            var clampedInherited = this._clamp_font_size_min_pt(scaledInherited, effectiveMinFontPt, pointsPerUserUnit);
            if (clampedInherited) {
                el.style.setProperty('font-size', clampedInherited);
            }
        }

        var strokeStyle = el.style ? el.style.getPropertyValue('stroke-width') : '';
        var strokeAttr = el.getAttribute('stroke-width');
        var scaledStroke;

        if (strokeStyle) {
            scaledStroke = this._scale_style_value(strokeStyle, strokeCompensation);
            if (scaledStroke) {
                el.style.setProperty('stroke-width', scaledStroke);
            }
        }
        if (strokeAttr) {
            scaledStroke = this._scale_style_value(strokeAttr, strokeCompensation);
            if (scaledStroke) {
                el.setAttribute('stroke-width', scaledStroke);
            }
        }
    }, this);
};

StructureViewer.prototype._is_offscreen_transform = function(el, maxWidth) {
    if (!el) {
        return false;
    }

    var transform = el.getAttribute('transform');
    if (!transform) {
        return false;
    }

    // Catch translated track groups parked far off to the right during hide animations.
    var match = transform.match(/translate\(\s*(-?\d*\.?\d+)/i);
    if (!match) {
        return false;
    }

    var tx = parseFloat(match[1]);
    if (isNaN(tx) || !isFinite(tx)) {
        return false;
    }

    return tx > (maxWidth * 1.5);
};

StructureViewer.prototype._prune_exported_svg = function(exportedSvg, sourceWidth) {
    if (!exportedSvg) {
        return;
    }

    var maxWidth = sourceWidth || this.width || 900;
    var nodesToRemove = [];

    // Only prune track container groups that were moved off-canvas.
    // Avoid pruning arbitrary hidden nodes, which can remove intended content.
    Array.prototype.forEach.call(exportedSvg.querySelectorAll('g[id^="track"]'), function(el) {
        if (this._is_offscreen_transform(el, maxWidth)) {
            nodesToRemove.push(el);
        }
    }, this);

    nodesToRemove.forEach(function(node) {
        if (node && node.parentNode) {
            node.parentNode.removeChild(node);
        }
    });
};

StructureViewer.prototype._inches_to_px = function(inches) {
    return Math.round(inches * this.export_dpi);
};

StructureViewer.prototype.parse_export_inches = function(inchesValue) {
    if (inchesValue === undefined || inchesValue === null || inchesValue === '') {
        return null;
    }

    var requestedInches = parseFloat(inchesValue);
    if (isNaN(requestedInches) || !isFinite(requestedInches) || requestedInches < 1 || requestedInches > 40) {
        alert('Please enter a width between 1 and 40 inches.');
        return null;
    }

    return requestedInches;
};

StructureViewer.prototype.export_svg = function(targetWidthPx, targetWidthInches) {
    var sourceSvg = document.querySelector('.protein_viewer .viewer svg');
    if (!sourceSvg) {
        alert('No viewer SVG found to export.');
        return;
    }

    var exportedSvg = sourceSvg.cloneNode(true);
    exportedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    exportedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

    var sourceViewBox = sourceSvg.viewBox && sourceSvg.viewBox.baseVal;
    var sourceWidth = sourceViewBox && sourceViewBox.width ? sourceViewBox.width :
        this._parse_svg_length(sourceSvg.getAttribute('width')) || sourceSvg.clientWidth || 900;
    var sourceHeight = sourceViewBox && sourceViewBox.height ? sourceViewBox.height :
        this._parse_svg_length(sourceSvg.getAttribute('height')) || sourceSvg.clientHeight || 400;

    var finalWidth = targetWidthPx || sourceWidth;
    if (!finalWidth || !isFinite(finalWidth) || finalWidth <= 0) {
        finalWidth = sourceWidth;
    }

    var baseScale = finalWidth / sourceWidth;
    var finalHeight = Math.max(1, Math.round(sourceHeight * baseScale));
    var finalWidthInches = targetWidthInches || (finalWidth / this.export_dpi);
    var finalHeightInches = finalHeight / this.export_dpi;
    var pointsPerUserUnit = (72 * finalWidthInches) / sourceWidth;
    var minTextPt = this._get_min_export_font_pt(finalWidthInches);

    this._prune_exported_svg(exportedSvg, sourceWidth);

    exportedSvg.setAttribute('viewBox', '0 0 {0} {1}'.format(sourceWidth, sourceHeight));
    exportedSvg.setAttribute('width', finalWidthInches.toFixed(3).replace(/0+$/, '').replace(/\.$/, '') + 'in');
    exportedSvg.setAttribute('height', finalHeightInches.toFixed(3).replace(/0+$/, '').replace(/\.$/, '') + 'in');

    this._adjust_export_visual_scale(exportedSvg, baseScale, pointsPerUserUnit, minTextPt, finalWidthInches);
    this._layout_compact_feature_labels(exportedSvg, finalWidthInches);

    var serialized = new XMLSerializer().serializeToString(exportedSvg);
    if (!serialized.startsWith('<?xml')) {
        serialized = '<?xml version="1.0" standalone="no"?>\n' + serialized;
    }

    var blob = new Blob([serialized], { type: 'image/svg+xml;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = 'protein-viewer.svg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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
    if (!this.macro_viewer || !this.zoom_viewer) {
        return;
    }

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
    function wireButton(selector, options, onClick) {
        var element = $(selector);
        if (!element.length) {
            return;
        }

        if (typeof element.button === 'function') {
            element.button(options || {});
        }

        if (typeof onClick === 'function') {
            element.on('click', onClick);
        }
    }

    wireButton('.zoomout-tool', { icons: { primary: 'ui-icon-zoomout' }, text:false }, function(){
        if (window.structure_viewer) {
            window.structure_viewer.zoom_off();
        }
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

    wireButton('.svg-tool', {}, function(){
        if (!window.structure_viewer) {
            return;
        }

        var modalElement = document.getElementById('svgExportModal');
        if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) {
            alert('Export modal is not available.');
            return;
        }

        var sourceSvg = document.querySelector('.protein_viewer .viewer svg');
        var sourceWidth = sourceSvg ? (
            window.structure_viewer._parse_svg_length(sourceSvg.getAttribute('width')) || sourceSvg.clientWidth || 900
        ) : 900;
        var defaultInches = Math.max(1, Math.min(40, sourceWidth / window.structure_viewer.export_dpi));

        var presetRadios = $('.svg-export-size');
        var customRadio = $('#svg-size-custom');
        var customInput = $('#svgExportCustomInches');
        var pixelPreview = $('#svgExportPxPreview');

        function selectedInchesFromModal() {
            var selected = $('input[name="svg-export-size"]:checked').val();
            if (selected === 'custom') {
                return window.structure_viewer.parse_export_inches(customInput.val());
            }
            return window.structure_viewer.parse_export_inches(selected);
        }

        function updateCustomState() {
            var isCustom = customRadio.is(':checked');
            customInput.prop('disabled', !isCustom);
        }

        function updatePixelPreview() {
            var inches = selectedInchesFromModal();
            if (inches === null) {
                pixelPreview.text('');
                return;
            }
            var px = window.structure_viewer._inches_to_px(inches);
            pixelPreview.text('Approximate width: ' + px + ' px at ' + window.structure_viewer.export_dpi + ' DPI');
        }

        var presetMatch = false;
        presetRadios.each(function() {
            var value = $(this).val();
            if (value !== 'custom' && Math.abs(parseFloat(value) - defaultInches) < 0.05) {
                $(this).prop('checked', true);
                presetMatch = true;
            }
        });
        if (!presetMatch) {
            customRadio.prop('checked', true);
            customInput.val(defaultInches.toFixed(2));
        }

        updateCustomState();
        updatePixelPreview();

        presetRadios.off('change.svgexport').on('change.svgexport', function() {
            updateCustomState();
            updatePixelPreview();
        });
        customInput.off('input.svgexport').on('input.svgexport', function() {
            updatePixelPreview();
        });

        $('#svg-export-confirm').off('click.svgexport').on('click.svgexport', function() {
            var selectedInches = selectedInchesFromModal();
            if (selectedInches === null) {
                return;
            }

            var targetWidthPx = window.structure_viewer._inches_to_px(selectedInches);
            window.structure_viewer.export_svg(targetWidthPx, selectedInches);
            window.bootstrap.Modal.getOrCreateInstance(modalElement).hide();
        });

        window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
    });

    wireButton('.help-tool', { icons: { primary: 'ui-icon-help' }, text:false });

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
    });
});
