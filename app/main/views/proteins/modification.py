from flask import render_template
from flask_login import current_user
from app.database import protein, modifications
from app.main.views.proteins import bp


@bp.route('/<protein_id>/modifications')
def modification(protein_id):
    prot = protein.get_protein_by_id(protein_id)
    
    mod_sites = {}
    # experiment_filter = request.urlfilter.get_field('experiment_id')
    user = None
    if current_user.is_authenticated:
        user = current_user
    mspeps = modifications.get_measured_peptides_by_protein(protein_id, user)
    mspeps = modifications.MeasuredPeptide.query.filter_by(protein_id=protein_id).all()

    # if experiment_filter:
    #     mspeps = [ ms for ms in mspeps if ms.experiment_id == experiment_filter ]

    for MS in mspeps:
        for pepmod in MS.peptides:
            pep = pepmod.peptide
            pep_tuple = (pep, pepmod.modification.name)
            exps = mod_sites.get(pep_tuple, set())
            exps.add(MS.experiment)
            mod_sites[pep_tuple] = exps
            
    mod_sites = [{'site':pep.site_pos, 'name':pep.get_name(), 'type':mod_type, 'peptide':pep.get_peptide(), 'experiments':exps} for (pep, mod_type), exps in mod_sites.items()]
    mod_sites = sorted( mod_sites, key=lambda item: item['site'] )
    
    return render_template(
        'proteomescout/proteins/modifications.html',
        protein=prot,
        modification_sites=mod_sites)
