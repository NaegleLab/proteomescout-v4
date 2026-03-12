"""
Refactored protein structure view using TSV flat text format.
Renders protein structure visualization with modifications, domains, and regions.
"""

import json
import base64
from flask import Blueprint, render_template, url_for, request
from flask_login import current_user
from app.main.views.proteins import bp
from app.config import settings
from app.database.tsv_protein_data import (
    get_protein_by_id,
    get_citation_by_id,
    parse_modifications,
    parse_evidence_ids,
    parse_uniprot_domains,
    parse_structure,
    parse_go_terms,
    get_site_regions
)
from collections import defaultdict


def format_scansite_predictions(prot):
    """Format scansite predictions (if available in future)."""
    return {}


def format_protein_mutations(prot):
    """Format protein mutations from TSV data."""
    # Mutations not currently in TSV format
    return {}


def get_activation_loops(prot):
    """Extract activation loop regions (if present in structure data)."""
    return []


def get_uniprot_domains(prot):
    """Extract UniProt domains from protein data."""
    formatted_regions = []
    domains = prot.get('uniprot_domains', '')
    
    for domain in parse_uniprot_domains(domains):
        formatted_regions.append(domain)
    
    return sorted(formatted_regions, key=lambda d: d['start'])


def get_ncbi_domains(prot):
    """Extract NCBI domains (if present in TSV)."""
    # Not currently in TSV format
    return []


def get_uniprot_structure(prot):
    """Extract secondary structure elements from UniProt."""
    formatted_regions = []
    structure_types = {'helix', 'turn', 'strand'}
    
    structures = parse_structure(prot.get('structure', ''))
    
    for struct in structures:
        if struct['type'] in structure_types:
            formatted_regions.append({
                'type': struct['type'],
                'label': struct['type'],
                'source': struct['source'],
                'start': struct['start'],
                'stop': struct['stop']
            })
    
    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_sites(prot):
    """Extract UniProt binding sites and active sites from macro_molecular field."""
    formatted_regions = []
    site_types = {
        'metal ion-binding site',
        'binding site',
        'calcium-binding region',
        'nucleotide phosphate-binding region',
        'lipid moiety-binding region',
        'active site',
        'DNA-binding region'
    }
    
    macro_data = prot.get('macro_molecular', '')
    if macro_data and str(macro_data).strip():
        # Parse macro_molecular field for site information
        for site_entry in str(macro_data).split(';'):
            site_entry = site_entry.strip()
            if not site_entry:
                continue
            
            parts = site_entry.split(':')
            if len(parts) >= 3:
                site_type = ':'.join(parts[:-2])
                try:
                    start = int(parts[-2])
                    stop = int(parts[-1])
                    if site_type.lower() in site_types:
                        formatted_regions.append({
                            'type': site_type,
                            'label': site_type,
                            'source': 'uniprot',
                            'start': start,
                            'stop': stop
                        })
                except ValueError:
                    continue
    
    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_macro(prot):
    """Extract macro structural features (transmembrane, coiled-coil, etc)."""
    formatted_regions = []
    macro_types = {
        'zinc finger region',
        'intramembrane region',
        'coiled-coil region',
        'transmembrane region'
    }
    
    macro_data = prot.get('macro_molecular', '')
    if macro_data and str(macro_data).strip():
        for macro_entry in str(macro_data).split(';'):
            macro_entry = macro_entry.strip()
            if not macro_entry:
                continue
            
            parts = macro_entry.split(':')
            if len(parts) >= 3:
                macro_type = ':'.join(parts[:-2])
                try:
                    start = int(parts[-2])
                    stop = int(parts[-1])
                    if macro_type.lower() in macro_types:
                        formatted_regions.append({
                            'type': macro_type,
                            'label': macro_type,
                            'source': 'uniprot',
                            'start': start,
                            'stop': stop
                        })
                except ValueError:
                    continue
    
    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_topological(prot):
    """Extract topological domains from UniProt."""
    formatted_regions = []
    
    macro_data = prot.get('macro_molecular', '')
    if macro_data and str(macro_data).strip():
        for topo_entry in str(macro_data).split(';'):
            topo_entry = topo_entry.strip()
            if 'topological domain' not in topo_entry.lower():
                continue
            
            parts = topo_entry.split(':')
            if len(parts) >= 3:
                try:
                    start = int(parts[-2])
                    stop = int(parts[-1])
                    formatted_regions.append({
                        'type': 'topological domain',
                        'label': 'topological domain',
                        'source': 'uniprot',
                        'start': start,
                        'stop': stop
                    })
                except ValueError:
                    continue
    
    return sorted(formatted_regions, key=lambda d: d['start'])


def format_protein_regions(prot):
    """Format all protein regions/features."""
    formatted_regions = {}
    
    formatted_regions['activation_loops'] = get_activation_loops(prot)
    formatted_regions['uniprot_domains'] = get_uniprot_domains(prot)
    formatted_regions['uniprot_structure'] = get_uniprot_structure(prot)
    formatted_regions['uniprot_sites'] = get_uniprot_sites(prot)
    formatted_regions['uniprot_macro'] = get_uniprot_macro(prot)
    formatted_regions['uniprot_topological'] = get_uniprot_topological(prot)
    formatted_regions['ncbi_domains'] = get_ncbi_domains(prot)
    
    return formatted_regions


def format_protein_domains(prot):
    """Format protein domains."""
    formatted_domains = []
    
    domains = parse_uniprot_domains(prot.get('uniprot_domains', ''))
    for domain in domains:
        formatted_domains.append(domain)
    
    return sorted(formatted_domains, key=lambda d: d['start'])


def format_protein_modifications(prot):
    """
    Format protein modifications from TSV data.
    Parse modifications field and map to evidence/experiments.
    """
    experiments = {}
    mod_types = set()
    mods = {}
    
    # Get modification data
    mod_string = prot.get('modifications', '')
    if not mod_string or str(mod_string).strip() == '':
        return experiments, sorted(list(mod_types)), mods
    
    modifications = parse_modifications(mod_string)
    
    # Get evidence (experiment) IDs
    evidence_string = prot.get('evidence', '')
    evidence_ids = parse_evidence_ids(evidence_string)
    
    # Get citations for each evidence ID
    citations = _load_citations()
    for exp_id in evidence_ids:
        citation = get_citation_by_id(exp_id)
        if citation is not None:
            experiments[exp_id] = citation.get('Name', f'Experiment {exp_id}')
    
    # Format modifications by position
    for mod in modifications:
        position = mod['position']
        modification_type = mod['modification']
        residue = mod['residue']
        
        mod_types.add(modification_type)
        
        # Create entry for this position if it doesn't exist
        if position not in mods:
            mods[position] = {
                'mods': {},
                'residue': residue,
                'domain': None,
                'regions': [],
                'peptide': None
            }
        
        # Add modification type for this position
        if modification_type not in mods[position]['mods']:
            mods[position]['mods'][modification_type] = []
        
        # Add experiment evidence for this modification
        for exp_id in evidence_ids:
            mods[position]['mods'][modification_type].append({
                'experiment': exp_id,
                'experiment_url': '',
                'has_data': True
            })
    
    return experiments, sorted(list(mod_types)), mods


def _load_citations():
    """Load citations cache (simple wrapper)."""
    from app.database.tsv_protein_data import _load_citations
    return _load_citations()


@bp.route('/<protein_id>', strict_slashes=False)
@bp.route('/<protein_id>/structure')
def structure(protein_id):
    """Render protein structure visualization page using TSV data."""
    user = None
    if current_user.is_authenticated:
        user = current_user
    
    # Get protein data from TSV
    prot = get_protein_by_id(protein_id)
    
    if prot is None:
        from flask import abort
        abort(404)
    
    # Format protein data for visualization
    formatted_exps, formatted_mod_types, formatted_mods = format_protein_modifications(prot)
    formatted_domains = format_protein_domains(prot)
    formatted_regions = format_protein_regions(prot)
    formatted_mutations = format_protein_mutations(prot)
    formatted_scansite = format_scansite_predictions(prot)
    
    # Get protein name from accessions (use first accession or protein_name field)
    protein_name = prot.get('protein_name', protein_id)
    
    # Build data dictionary for JavaScript
    data = {
        'seq': prot.get('sequence', ''),
        'domains': formatted_domains,
        'mods': formatted_mods,
        'mutations': formatted_mutations,
        'regions': formatted_regions,
        'mod_types': formatted_mod_types,
        'scansite': formatted_scansite,
        'exps': formatted_exps,
        'pfam_url': 'HOLDER PFAM URL',
        'protein_data_url': url_for('protein.data', protein_id=protein_id),
        'images_url': 'IMAGES URL',
        'experiment': request.form.get('experiment_id')
    }
    
    # Convert to JSON for template
    js = json.dumps(data)
    
    track_names = [
        "PFam Domains",
        "PTMs",
        "Activation Loops",
        "Uniprot Domains",
        "Uniprot Structure",
        "Uniprot Binding Sites",
        "Uniprot Macrostructure",
        "Uniprot Topology",
        "Mutations",
        "Scansite"
    ]
    
    return render_template(
        'proteomescout/proteins/structure.html',
        pageTitle=protein_name,
        protein_viewer_help_page="/".join([settings.documentationUrl, settings.proteinViewerHelp]),
        protein=prot,
        experiments=formatted_exps,
        mod_types=formatted_mod_types,
        tracks=track_names,
        data=js
    )
