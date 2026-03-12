import json

from flask import Blueprint, abort, current_app, render_template, request, url_for

from flatfile_app.protein_data import (
    get_citation_by_id,
    get_protein_by_id,
    get_species_options,
    parse_evidence_ids,
    parse_site_evidence_entries,
    parse_interpro_domains,
    parse_modifications,
    parse_structure,
    parse_uniprot_domains,
    search_proteins,
)


bp = Blueprint('proteins', __name__, url_prefix='/proteins')


def format_scansite_predictions(_protein):
    return {}


def format_protein_mutations(_protein):
    return {}


def get_activation_loops(_protein):
    return []


def _parse_macro_regions(macro_string, allowed_types=None, contains_text=None):
    formatted_regions = []
    for region_entry in str(macro_string or '').split(';'):
        region_entry = region_entry.strip()
        if not region_entry:
            continue

        parts = region_entry.split(':')
        if len(parts) < 3:
            continue

        region_type = ':'.join(parts[:-2])
        region_type_lower = region_type.lower()
        if allowed_types and region_type_lower not in allowed_types:
            continue
        if contains_text and contains_text not in region_type_lower:
            continue

        try:
            start = int(parts[-2])
            stop = int(parts[-1])
        except ValueError:
            continue

        formatted_regions.append(
            {
                'type': region_type if not contains_text else contains_text,
                'label': region_type,
                'source': 'uniprot',
                'start': start,
                'stop': stop,
            }
        )

    return sorted(formatted_regions, key=lambda item: item['start'])


def get_uniprot_domains(protein):
    return sorted(parse_uniprot_domains(protein.get('uniprot_domains', '')), key=lambda item: item['start'])


def get_ncbi_domains(_protein):
    return []


def get_uniprot_structure(protein):
    structure_types = {'helix', 'turn', 'strand'}
    formatted_regions = []

    for structure in parse_structure(protein.get('structure', '')):
        if structure['type'] in structure_types:
            formatted_regions.append(
                {
                    'type': structure['type'],
                    'label': structure['type'],
                    'source': structure['source'],
                    'start': structure['start'],
                    'stop': structure['stop'],
                }
            )

    return sorted(formatted_regions, key=lambda item: item['start'])


def get_uniprot_sites(protein):
    return _parse_macro_regions(
        protein.get('macro_molecular', ''),
        allowed_types={
            'metal ion-binding site',
            'binding site',
            'calcium-binding region',
            'nucleotide phosphate-binding region',
            'lipid moiety-binding region',
            'active site',
            'dna-binding region',
        },
    )


def get_uniprot_macro(protein):
    return _parse_macro_regions(
        protein.get('macro_molecular', ''),
        allowed_types={
            'zinc finger region',
            'intramembrane region',
            'coiled-coil region',
            'transmembrane region',
        },
    )


def get_uniprot_topological(protein):
    return _parse_macro_regions(
        protein.get('macro_molecular', ''),
        contains_text='topological domain',
    )


def format_protein_regions(protein):
    return {
        'activation_loops': get_activation_loops(protein),
        'uniprot_domains': get_uniprot_domains(protein),
        'uniprot_structure': get_uniprot_structure(protein),
        'macro_molecular': _parse_macro_regions(protein.get('macro_molecular', '')),
        'ncbi_domains': get_ncbi_domains(protein),
    }


def format_protein_domains(protein):
    return sorted(parse_interpro_domains(protein.get('Interpro_domains', '')), key=lambda item: item['start'])


def format_protein_modifications(protein):
    experiments = {}
    experiment_links = {}
    modification_types = set()
    modifications_by_site = {}

    modifications = parse_modifications(protein.get('modifications', ''))
    evidence_entries = parse_site_evidence_entries(protein.get('evidence', ''))

    def citation_is_current(citation):
        current_value = str(citation.get('Current', citation.get('current', ''))).strip().lower()
        return current_value in {'true', '1', 'yes', 'y'}

    def normalize_pmid(value):
        pmid = str(value or '').strip()
        if pmid.endswith('.0'):
            pmid = pmid[:-2]
        return pmid

    for index, modification in enumerate(modifications):
        position = modification['position']
        modification_type = modification['modification']
        evidence_entry = evidence_entries[index] if index < len(evidence_entries) else ''
        if not evidence_entry:
            continue

        candidate_experiment_ids = [item.strip() for item in evidence_entry.split(',') if item.strip()]
        if not candidate_experiment_ids:
            continue

        grouped_experiments = []
        for experiment_id in candidate_experiment_ids:
            citation = get_citation_by_id(experiment_id)
            if citation is None or not citation_is_current(citation):
                continue

            pmid = normalize_pmid(citation.get('PMID', ''))
            group_id = f'pmid:{pmid}' if pmid else f'exp:{experiment_id}'
            citation_url = str(citation.get('URL', citation.get('url', '')) or '').strip()
            fallback_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else '#'
            preferred_url = citation_url or fallback_url

            if group_id not in experiments:
                experiments[group_id] = citation.get('Name', f'Experiment {experiment_id}')

            # Prefer explicit citation URLs; otherwise keep PMID fallback.
            if (
                group_id not in experiment_links
                or (
                    citation_url
                    and experiment_links[group_id].startswith('https://pubmed.ncbi.nlm.nih.gov/')
                )
            ):
                experiment_links[group_id] = preferred_url

            grouped_experiments.append(
                {
                    'group_id': group_id,
                }
            )

        if not grouped_experiments:
            continue

        modification_types.add(modification_type)

        if position not in modifications_by_site:
            modifications_by_site[position] = {
                'mods': {},
                'residue': modification['residue'],
                'domain': None,
                'regions': [],
                'peptide': None,
            }

        modifications_by_site[position]['mods'].setdefault(modification_type, [])
        seen_group_ids = {
            item['experiment'] for item in modifications_by_site[position]['mods'][modification_type]
        }

        for grouped in grouped_experiments:
            if grouped['group_id'] in seen_group_ids:
                continue

            modifications_by_site[position]['mods'][modification_type].append(
                {
                    'experiment': grouped['group_id'],
                    'experiment_url': experiment_links.get(grouped['group_id'], '#'),
                    'has_data': False,
                }
            )
            seen_group_ids.add(grouped['group_id'])

    return experiments, sorted(modification_types), modifications_by_site


@bp.route('/')
def search():
    query = request.args.get('q', '').strip()
    peptide = request.args.get('peptide', '').strip()
    species = request.args.get('species', '').strip()

    results = search_proteins(query=query, peptide=peptide, species=species)
    return render_template(
        'proteins/search.html',
        query=query,
        peptide=peptide,
        selected_species=species,
        species_options=get_species_options(),
        results=results,
        result_count=len(results),
        max_results=current_app.config['MAX_SEARCH_RESULTS'],
    )


@bp.route('/<protein_id>')
@bp.route('/<protein_id>/structure')
def structure(protein_id):
    protein = get_protein_by_id(protein_id)
    if protein is None:
        abort(404)

    formatted_experiments, formatted_mod_types, formatted_mods = format_protein_modifications(protein)
    protein_name = protein.get('protein_name') or protein.get('acc_gene') or protein_id
    template_protein = {
        'protein_name': protein_name,
        'acc_gene': protein.get('acc_gene', ''),
        'uniprot_id': protein.get('uniprot_id', ''),
        'species': protein.get('species', ''),
    }

    viewer_data = {
        'seq': protein.get('sequence', ''),
        'domains': format_protein_domains(protein),
        'mods': formatted_mods,
        'mutations': format_protein_mutations(protein),
        'regions': format_protein_regions(protein),
        'mod_types': formatted_mod_types,
        'scansite': format_scansite_predictions(protein),
        'exps': formatted_experiments,
        'pfam_url': '',
        'protein_data_url': '#',
        'images_url': '',
        'experiment': request.args.get('experiment_id'),
    }

    return render_template(
        'proteins/structure.html',
        protein=template_protein,
        page_title=protein_name,
        viewer_help_url=current_app.config['DOCUMENTATION_URL'],
        experiments=formatted_experiments,
        mod_types=formatted_mod_types,
        tracks=[
            'Interpro Domains',
            'PTMs',
            'Activation Loops',
            'Uniprot Domains',
            'Uniprot Structure',
            'Macro Molecular',
        ],
        data=json.dumps(viewer_data),
    )