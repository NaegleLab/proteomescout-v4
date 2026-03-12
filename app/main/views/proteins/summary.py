from flask import render_template
from app.database import protein
from app.main.views.proteins import bp
from collections import defaultdict


@bp.route('/<protein_id>/summary')
def summary(protein_id):
    prot = protein.get_protein_by_id(protein_id)
    accessions = defaultdict(list)
    for acc in prot.accessions:
        accessions[acc.get_type()].append(
            {'name': acc.value, 'url': acc.get_url()})

    return render_template(
        'proteomescout/proteins/summary.html',
        protein=prot,
        accessions=accessions)
