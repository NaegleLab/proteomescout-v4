from flask import render_template
from flask_login import current_user
from app.database import experiment, protein, modifications

#from app.main.views.proteins.search import get_protein_metadata
from app.main.views.experiments import bp
from app.config import strings

# this function was initially imported from proteins/search.py
# Because of how much the original function has been altered this was moved 
# here to prevent any issues
# NEEDS TO BE REWORKED FOR COMPATIBILITY WITH NEW FUNCTION (use celery)
def get_protein_metadata(prot, metadata_map, user, exp_id=None):
    
    measured = modifications.get_measured_peptides_by_protein(prot.id, user)

    exp_ids = set()
    residues = set()
    ptms = set()
    sites = set()

    for ms in measured:
        exp_ids.add(ms.experiment_id)

    if exp_id:
        measured = [ms for ms in measured if ms.experiment_id == exp_id]

    for ms in measured:
        for mspep in ms.peptides:
            residues.add(mspep.peptide.site_type)
            sites.add(mspep.peptide.site_pos)
            ptms.add(mspep.modification.name)

    metadata_map[prot.id] = (
        prot,
        len(prot.sequence),
        len(exp_ids),
        len(sites),
        ','.join(residues),
        ', '.join(ptms))

def query_all(exp_id):
    protein_cnt, proteins = protein.get_proteins_by_experiment(exp_id)
    return proteins

@bp.route('/<experiment_id>/browse')
def browse(experiment_id):
    # species_list = [ species.name for species in taxonomies.getAllSpecies() ]
    # submitted, form_schema = search_view.build_schema(request, species_list)

    # pager = paginate.Paginator(form_schema, search_view.QUERY_PAGE_LIMIT)
    # pager.parse_parameters(request)

    user = current_user if current_user.is_authenticated else None
    exp = experiment.get_experiment_by_id(experiment_id, user)
    proteins = query_all(experiment_id)
    # proteins = []
    protein_metadata = {}
    # errors = []

    # if submitted:
    #     errors = search_view.build_validator(form_schema).validate()
    #     if len(errors) == 0:
    #         proteins = search_view.perform_query(form_schema, pager, experiment_id)
    # else:
    #     proteins = query_all(experiment_id, pager)

    for p in proteins:
        get_protein_metadata(p, protein_metadata, user, experiment_id)

    # form_renderer = forms.FormRenderer(form_schema)
    return render_template(
        'proteomescout/experiments/browse.html',
        title = strings.experiment_browse_page_title % (exp.name),
        experiment=exp,
        proteins=proteins,
        protein_metadata=protein_metadata,
        protein_zip=zip(proteins, protein_metadata),
    )

