
from flask import render_template
from flask_login import current_user
from app.main.views.experiments import bp
from app.database import experiment
from app.config import strings
import json

# def domain_tree(measurements):
#     domain_map = {}
#     for m in measurements:
#         prot = m.protein

#         for d in prot.domains:
#             pass




def format_pfam_domains(measurements):
    
    domain_map = {}
    for m in measurements:
        prot = m.protein
        
        for d in prot.domains:
            mapset = domain_map.get(d.label, set())
            mapset.add(prot.name)
            domain_map[d.label] = mapset
            
        if len(prot.domains) == 0:
            mapset = domain_map.get('None', set())
            mapset.add(prot.name)
            domain_map['None'] = mapset
    domain_size = []
    domain_sort = {}
    for domain in domain_map:
        domain_size.append({"name": domain, "value" : len(domain_map[domain]) })
        domain_map[domain] = list(domain_map[domain])
        domain_sort[domain] = len(domain_map[domain])
    
    domain_list = sorted(domain_sort.items(), key=lambda item: -item[1])
    domain_size = []
    for (domain, size) in domain_list:
        domain_size.append({"name": domain, "value": size})
    jsondata = json.dumps(domain_size)
    return {'table': domain_list, 'json': jsondata}


def format_pfam_sites(measurements):
    
    site_map = {}
    
    for m in measurements:
        for p in m.peptides:
            pep = p.peptide
            
            if pep.protein_domain is not None:
                pfam_site = pep.protein_domain.label
            else:
                pfam_site = 'None'
            
            mapset = site_map.get(pfam_site, set())
            mapset.add(m)
            site_map[pfam_site] = mapset

    for site in site_map:
        site_map[site] = len(site_map[site])
    
    site_list = sorted(site_map.items(), key=lambda item: -item[1])
    site_json = []
    for (site, size) in site_list:
        site_json.append({'name': site, 'value': size})

    jsondata = json.dumps(site_json)
    
    return {'table': site_list, 'json': jsondata}

# def create_query_generator(field):
#     from ptmscout.utils.query_generator import generate_metadata_query

#     def query_generator(value):
#         return {'query': generate_metadata_query(field, value)}

#     return query_generator

# @decorators.cache_result
def get_pfam_view_data(exp):
    formatted_sites = format_pfam_sites(exp.measurements)
    formatted_domains = format_pfam_domains(exp.measurements)

    return formatted_sites, formatted_domains



@bp.route('/<experiment_id>/pfam')
def protein_families(experiment_id):
    user = current_user if current_user.is_authenticated else None
    # user_owner = current_user is not None and current_user.experiment_owner(exp)
    exp = experiment.get_experiment_by_id(experiment_id, user)
    formatted_sites, formatted_domains = get_pfam_view_data(exp)
    return render_template(
        'proteomescout/experiments/pfam.html',
        title = strings.experiment_pfam_page_title % (exp.name),
        experiment=exp,
        sites=formatted_sites,
        domains=formatted_domains
        )