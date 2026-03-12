import json
import base64
from flask import Blueprint, render_template, url_for, request

from flask_login import current_user
from app.main.views.proteins import bp
from app.config import settings
from app.database import protein, modifications
from collections import defaultdict

def format_scansite_predictions(prot):
    formatted_scansite = defaultdict(list)
    
    for pred in prot.scansite:
        ss = { 'source': pred.source,
               'value': pred.value,
               'score': "%.2f%%" % (pred.percentile)
               }
        formatted_scansite[pred.site_pos].append( ss )

    return formatted_scansite


def format_protein_mutations(prot):
    formatted_mutations = {}
    for m in prot.mutations:
        mut_dict = {}
        mut_dict['type'] = m.mutationType
        mut_dict['location'] = m.location
        mut_dict['original'] = m.original
        mut_dict['mutant'] = m.mutant
        mut_dict['annotation'] = m.annotation
        mut_dict['clinical'] = m.clinical

        mut_list = formatted_mutations.get(m.location, [])
        mut_list.append(mut_dict)
        formatted_mutations[m.location] = mut_list

    return formatted_mutations


def get_activation_loops(prot):
    formatted_regions = []
    for d in prot.regions:
        if d.type == 'Activation Loop':
            region_dict = {}
            region_dict['type'] = d.type
            region_dict['label'] = d.label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_domains(prot):
    formatted_regions = []

    for d in prot.regions:
        if d.type == 'domain' and d.source == 'uniprot':
            region_dict = {}
            region_dict['type'] = d.type
            region_dict['label'] = d.label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_ncbi_domains(prot):
    formatted_regions = []

    for d in prot.regions:
        if d.type == 'Domain' and d.source == 'ncbi':
            region_dict = {}
            region_dict['type'] = d.type
            region_dict['label'] = d.label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_structure(prot):
    formatted_regions = []
    structure_types = set(['helix', 'turn', 'strand'])
    for d in prot.regions:
        if d.type in structure_types  and d.source == 'uniprot':
            region_dict = {}
            region_dict['type'] = d.type
            region_dict['label'] = d.type
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_sites(prot):
    formatted_regions = []
    structure_types = set([
                        'metal ion-binding site',
                        'binding site',
                        'calcium-binding region',
                        'nucleotide phosphate-binding region',
                        'lipid moiety-binding region',
                        'active site',
                        'DNA-binding region'
                        ])

    for d in prot.regions:
        if d.type in structure_types  and d.source == 'uniprot':
            region_dict = {}
            region_dict['type'] = d.type
            region_dict['label'] = d.label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_macro(prot):
    formatted_regions = []
    structure_types = set([
                        'zinc finger region',
                        'intramembrane region',
                        'coiled-coil region',
                        'transmembrane region'
                        ])

    for d in prot.regions:
        if d.type in structure_types and d.source == 'uniprot':
            region_dict = {}
            region_dict['type'] = d.type
            label = d.label if d.label != "" else d.type
            region_dict['label'] = label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def get_uniprot_topological(prot):
    formatted_regions = []
    structure_types = set([
                        'topological domain',
                        ])

    for d in prot.regions:
        if d.type in structure_types and d.source == 'uniprot':
            region_dict = {}
            region_dict['type'] = d.type
            label = d.label if d.label != "" else d.type
            region_dict['label'] = label
            region_dict['source'] = d.source
            region_dict['start'] = d.start
            region_dict['stop'] = d.stop

            formatted_regions.append(region_dict)

    return sorted(formatted_regions, key=lambda d: d['start'])


def format_protein_regions(prot):
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
    formatted_domains = []
    for d in prot.domains:
        domain_dict = {}
        domain_dict['label'] = d.label
        domain_dict['source'] = d.source
        domain_dict['start'] = d.start
        domain_dict['stop'] = d.stop

        formatted_domains.append(domain_dict)

    return sorted(formatted_domains, key=lambda d: d['start'])


def get_site_regions(regions, pos):
    region_names = []
    for r in regions:
        if r.start <= pos and pos <= r.stop:
            region_names.append(r.label)

    return region_names


def format_protein_modifications(prot, mod_sites):
    experiments = {}
    mod_types = set()
    mods = {}

    for ms in mod_sites:
        experiments[ms.experiment_id] = ms.experiment.name

        exp_url = url_for('experiment.home', experiment_id=ms.experiment_id)
        if ms.experiment.type == 'compendia':
            exp_url = ms.experiment.URL

        for modpep in ms.peptides:
            mod_types.add(modpep.modification.name)
            pep = modpep.peptide
            ptm = modpep.modification

            pos_description = mods.get( 
                pep.site_pos,
                { 
                    'mods': {},
                    'residue': pep.site_type,
                    'domain': pep.protein_domain.label if pep.protein_domain else None,
                    'regions': get_site_regions(prot.regions, pep.site_pos),
                    'peptide': pep.pep_aligned
                } 
            )

            mod_list = pos_description['mods'].get(ptm.name, [])
            mod_list.append(
                {
                    'MS': ms.id, 
                    'experiment_url': exp_url,
                    'experiment': ms.experiment_id,
                    'has_data': len(ms.data) > 0
                }
            )
            pos_description['mods'][ptm.name] = mod_list

            mods[pep.site_pos] = pos_description

    return experiments, sorted(list(mod_types)), mods


@bp.route('/<protein_id>', strict_slashes=False)
@bp.route('/<protein_id>/structure')
def structure(protein_id):
    user = None
    if current_user.is_authenticated:
        user = current_user
    
    prot = protein.get_protein_by_id(protein_id)
    
    mod_sites = modifications.get_measured_peptides_by_protein(protein_id, user)

    formatted_exps, formatted_mod_types, formatted_mods = format_protein_modifications(prot, mod_sites)
    formatted_domains = format_protein_domains(prot)
    formatted_regions = format_protein_regions(prot)
    formatted_mutations = format_protein_mutations(prot)
    formatted_scansite = format_scansite_predictions(prot)

    data = {'seq': prot.sequence, 
            'domains': formatted_domains, 
            'mods': formatted_mods,
            'mutations': formatted_mutations,
            'regions': formatted_regions,
            'mod_types': formatted_mod_types,
            'scansite': formatted_scansite,
            'exps': formatted_exps,
            'pfam_url': 'HOLDER PFAM URL',
            'protein_data_url': url_for('protein.data', protein_id=protein_id),
            # 'images_url': url_for('static'),
            'images_url': 'IMAGES URL',
            'experiment': request.form.get('experiment_id')
            }
    
    # Converts a python object into a JSON string
    js = json.dumps(data)
    # encoded_data = base64.b64encode(js.encode('utf-8'))

    track_names = [
                    "PFam Domains",
                    "PTMs",
                    "Activation Loops",
                    "Uniprot Domains",
                    "Uniprot Structure",
                    "Uniprot Binding Sites",
                    "Uniprot Macrostructure",
                    "Uniprot Topology",
#                    "Entrez Domains",
                    "Mutations",
                    "Scansite"
                ]
    
    return render_template(
        'proteomescout/proteins/structure.html',
        pageTitle=prot.name,
        protein_viewer_help_page="/".join([settings.documentationUrl, settings.proteinViewerHelp]),
        protein=prot,
        experiments=formatted_exps,
        mod_types=formatted_mod_types,
        tracks=track_names,
        data=js
    )
