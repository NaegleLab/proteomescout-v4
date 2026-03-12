from flask import render_template
from app.database import protein
from app.main.views.proteins import bp

@bp.route('/<protein_id>/go')
def go(protein_id):
    prot = protein.get_protein_by_id(protein_id)

    term_dict = {'F': set(), 'P': set(), 'C': set()}

    for goe in prot.GO_terms:
        term = goe.GO_term
        term_dict[term.aspect].add((term.GO, term.term))
        
    for aspect in term_dict:
        term_dict[aspect] = sorted(list(term_dict[aspect]), key=lambda item: item[1])

    return render_template(
        'proteomescout/proteins/go.html',
        protein=prot,
        F_terms=term_dict['F'],
        P_terms=term_dict['P'],
        C_terms=term_dict['C']
        )