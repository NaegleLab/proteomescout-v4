from flask import render_template
from flask_login import current_user
from app.main.views.experiments import bp
from app.database import experiment
from app.utils import protein_utils
from app.config import strings
import base64
import json

def summarize_measurements(measurements):
    summary = {'modifications': 0,
               'measured': 0,
               'proteins': set(),
               'by_residue': {},
               'by_species': {},
               'by_type': {}}
    
    for measured_peptide in measurements:
        for p in measured_peptide.peptides:
            pep = p.peptide
            
            residue_count = summary['by_residue'].get(pep.site_type, 0)
            summary['by_residue'][pep.site_type] = residue_count+1
            
            species = measured_peptide.protein.species.name
            species_count = summary['by_species'].get(species, 0)
            summary['by_species'][species] = species_count+1
            
            mod = p.modification
            while mod.parent:
                mod = mod.parent 
            
            type_count = summary['by_type'].get(mod.name, 0)
            summary['by_type'][mod.name] = type_count+1
            
            mods = summary['modifications']
            summary['modifications'] = mods+1
            
        measured = summary['measured']
        summary['measured'] = measured+1
        
        summary['proteins'].add(measured_peptide.protein_id)
    
    summary['proteins'] = len(summary['proteins'])
    
    return summary

def summarize_experiment(exp):
    measurement_summary = summarize_measurements(exp.measurements)
    sequence_profile = protein_utils.create_sequence_profile(exp.measurements)
    rejected_peps = len(set([err.peptide for err in exp.errors]))

    return measurement_summary, sequence_profile, rejected_peps

@bp.route('/<experiment_id>/summary')
def summary(experiment_id):
    user = current_user if current_user.is_authenticated else None
    # user_owner = current_user is not None and current_user.experiment_owner(exp)
    exp = experiment.get_experiment_by_id(experiment_id, user)
    measurement_summary, sequence_profile, rejected_peps = summarize_experiment(exp)

    profile_bytes = json.dumps(sequence_profile).encode('utf8')
    encoded = base64.b64encode(profile_bytes)
    

    return render_template(
        'proteomescout/experiments/summary.html',
        title=strings.experiment_summary_page_title % (exp.name),
        experiment=exp,
        measurement_summary=measurement_summary,
        sequence_profile=json.dumps(sequence_profile),
        rejected_peptides=rejected_peps,
        # user_owner=user_owner
        )












