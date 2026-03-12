function create_amino_acid_colors() {
    var colors = d3.scaleOrdinal();

    colors.domain([
        'E', 'D',
        'R', 'H', 'K',
        'G', 'A',
        'T', 'S', 'C',
        'V', 'L', 'I', 'M', 'P',
        'Y', 'F', 'W',
        'Q', 'N',
        '-'
    ]);

    var acidic = '#d62728';
    var basic = '#6b6ecf';
    var small = '#7f7f7f';
    var nucleophilic = '#ff7f0e';
    var hydrophobic = '#292929';
    var aromatic = '#c49c94';
    var amide = '#ce6dbd';
    var other = '#000000';

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

Array.max = function(array) {
    return Math.max.apply(Math, array);
};

Array.min = function(array) {
    return Math.min.apply(Math, array);
};

Array.unique = function(array) {
    return array.filter(function(item, index, items) {
        return index === items.indexOf(item);
    });
};

String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
        return typeof args[number] !== 'undefined' ? args[number] : match;
    });
};