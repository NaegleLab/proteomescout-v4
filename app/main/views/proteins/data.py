from flask import render_template

from flask_login import current_user
from app.main.views.proteins import bp
from app.database import protein, modifications

def filter_mods(mods, site_pos):
    filtered = []
    for mod in mods:
        keep = False
        for pep in mod.peptides:
            if pep.peptide.site_pos == site_pos:
                keep = True
                break
        if keep:
            filtered.append(mod)

    return filtered


def format_protein_data(mods):
    experiment_data = {}
    
    for mod in mods:
        exp_key = (mod.experiment.id, mod.experiment.name)
        ms_data = experiment_data.get(exp_key, [])
        
        peptides = [p.peptide.get_name() for p in mod.peptides]
        
        run_data = {}
        for d in mod.data:
            values = run_data.get(d.run, set())
            values.add((d.priority, d.units, d.label, d.value, d.type))
            run_data[d.run] = values

        sorted_data = []
        for run in run_data:
            data_units = [item[1] for item in run_data[run] if item[4] == 'data']
            units = data_units[0]
            
            sorted_values = [(label, str(value), type_) for (_, _, label, value, type_) in sorted(run_data[run], key=lambda item: item[0])]
            data_dict = {'run':run, 'units': units, 'values':sorted_values, 'peptides':peptides}
            
            sorted_data.append(data_dict)
            
        sorted_data = sorted(sorted_data, key=lambda item: item['run'])
        
        ms_data.extend(sorted_data)
        experiment_data[exp_key] = ms_data
    
    return [ {'id': eid, 'title':name, 'data':experiment_data[(eid,name)]} for (eid, name) in experiment_data if len(experiment_data[(eid,name)]) > 0]




@bp.route('/<protein_id>/data')
def data(protein_id):
    prot = protein.get_protein_by_id(protein_id)
    user = None
    if current_user.is_authenticated:
        user = current_user

    # mods = modifications.get_measured_peptides_by_protein(protein_id, user)
    mods = modifications.MeasuredPeptide.query.filter_by(protein_id=protein_id).all()
   
    # experiment_id = request.urlfilter.get_field('experiment_id')
    # site_pos = webutils.get(request, 'site_pos', None)
    
    # if experiment_id == None:
    #     mods = modifications.get_measured_peptides_by_protein(pid, request.user)
    # else:
    #     mods = modifications.get_measured_peptides_by_experiment(experiment_id, request.user, [pid])

    # if site_pos != None:
    #     mods = filter_mods(mods, int(site_pos))

    output_data = format_protein_data(mods)
    
    return render_template(
        'proteomescout/proteins/data.html',
        protein=prot,
        experiment_data=output_data)
