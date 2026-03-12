from flask import render_template
from app.database import protein
from app.main.views.proteins import bp
import json

@bp.route('/<protein_id>/expression')
def expression(protein_id):
    prot = protein.get_protein_by_id(protein_id)
    
    probe_ids = []
    collections = set()
    expression_data = []
    
    for probe in prot.expression_probes:
        probe_ids.append(probe.probeset_id)
        
        for sample in probe.samples:
            col_name = sample.collection.name
            tissue_name = sample.tissue.name
            collections.add(col_name)
            expression_data.append({'probeset': probe.probeset_id, 
                                    'collection': col_name, 
                                    'tissue': tissue_name,
                                    'value': sample.value})

    expression_data = sorted(expression_data, key=lambda item: item['tissue'])
    expression_data = json.dumps(expression_data)

    return render_template(
        'proteomescout/proteins/expression.html',
        protein=prot,
        probe_ids=sorted(probe_ids),
        collections=sorted(list(collections)),
        expression_data=expression_data)
