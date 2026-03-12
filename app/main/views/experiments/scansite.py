from flask import render_template
from flask_login import current_user
from app.main.views.experiments import bp
from app.config import strings
from app.database import experiment
import json

def filter_predictions(predictions, threshold = 1.0):
    return [ p for p in predictions if p.percentile <= threshold ]

def format_predictions(measurements):
    source_predictions = {}
    
    predictions = []
    phosphomap = {}
    for m in measurements:
        for p in m.peptides:
            pep = p.peptide
            
            for s in pep.predictions:
                predictions.append(s)
                phosphomap[s.id] = m
    
    predictions = filter_predictions(predictions)
    
    for scansite in predictions:
        source_predictions[scansite.source] = {}
       
    for scansite in predictions:
        m = phosphomap[scansite.id]
        
        measureset = source_predictions[scansite.source].get(scansite.value, set())
        measureset.add(m)
        source_predictions[scansite.source][scansite.value] = measureset
        
    allmeasures = set(measurements)
    keyset = source_predictions.keys()
    
    # return source_predictions

    formatted_predictions = {}
    for source in source_predictions:
        total = set()

        formatted_predictions[source] = {}
        for prediction in source_predictions[source]:
            formatted_predictions[source][prediction] = len(source_predictions[source][prediction])
            [ total.add(m) for m in source_predictions[source][prediction] ]

        diffset = allmeasures - total
        formatted_predictions[source]["None"] = len(diffset)
    
        formatted_predictions[source] = sorted(formatted_predictions[source].items(), key=lambda item: -item[1])
    
    json_predictions = {}
    for source, predictions in formatted_predictions.items():
        json_predictions[source] = []
        for (name, value) in predictions:
            json_predictions[source].append({"name": name, "value": value})
    
    combined_predictions = {}
    for source in formatted_predictions.keys():
        source_name = strings.prediction_type_map[source] if source in strings.prediction_type_map else source
        combined_predictions[source_name] = {'table' : formatted_predictions[source], 'json': json.dumps(json_predictions[source])}

        

    return combined_predictions

    

    # json_predictions = {}
    # for source in source_predictions:
    #     if source in strings.prediction_type_map:
    #         json_predictions[strings.prediction_type_map[source]] = {}
    #         tmp = formatted_predictions[source]
    #         jsontable = []
    #         for (name, value) in tmp.items():
    #             jsontable.append({'name': name, 'value': value})
    #         # del formatted_predictions[source]
    #         json_predictions[strings.prediction_type_map[source]]['table'] = tmp
    #         jsontable = json.dumps(jsontable)
    #         json_predictions[strings.prediction_type_map[source]]['json'] = jsontable


    # return json_predictions
    

    

    # for source in source_predictions.keys():
    #     total = set()
    #     for value in formatted_predictions[source]:
    #         [ total.add(m) for m in formatted_predictions[source][value] ]
    #         formatted_predictions[source][value] = len(formatted_predictions[source][value])
            
    #     diffset = allmeasures - total
        
    #     formatted_predictions[source]["None"] = len(diffset)
        
    #     formatted_predictions[source] = sorted(formatted_predictions[source].items(), key=lambda item: -item[1])
    #     table = formatted_predictions[source]
        
    #     jsontable = json.dumps(table)
        
    #     formatted_predictions[source] = {'json': jsontable, 'table':table}
        
    #     if source in strings.prediction_type_map:
    #         tmp = formatted_predictions[source]
    #         del formatted_predictions[source]
    #         formatted_predictions[strings.prediction_type_map[source]] = tmp 
        
    # return formatted_predictions
# def filter_predictions(predictions, threshold=1.0):
#     return [ p for p in predictions if p.percentile <= threshold ]

# def format_predictions(measurements):
#     formatted_predictions = {}
    
#     predictions = []
#     phosphomap = {}
#     for m in measurements:
#         for p in m.peptides:
#             pep = p.peptide
            
#             for s in pep.predictions:
#                 predictions.append(s)
#                 phosphomap[s.id] = m
    
#     predictions = filter_predictions(predictions)
    
#     for scansite in predictions:
#         formatted_predictions[scansite.source] = {}
       
#     for scansite in predictions:
#         m = phosphomap[scansite.id]
        
#         measureset = formatted_predictions[scansite.source].get(scansite.value, set())
#         measureset.add(m)
#         formatted_predictions[scansite.source][scansite.value] = measureset
        
#     allmeasures = set(measurements)
    
    
#     for source in formatted_predictions.keys():
#         total = set()
#         for value in formatted_predictions[source]:
#             [ total.add(m) for m in formatted_predictions[source][value] ]
#             formatted_predictions[source][value] = len(formatted_predictions[source][value])
            
#         diffset = allmeasures - total
        
#         formatted_predictions[source]["None"] = len(diffset)
        
#         formatted_predictions[source] = sorted(formatted_predictions[source].items(), key=lambda item: -item[1])
#         table = formatted_predictions[source]
        
#         jsontable = json.dumps(table)
        
#         formatted_predictions[source] = {'json': jsontable, 'table':table}
        
#         if source in strings.prediction_type_map:
#             tmp = formatted_predictions[source]
#             del formatted_predictions[source]
#             formatted_predictions[strings.prediction_type_map[source]] = tmp 
        
#     return formatted_predictions

def wrap_format_predictions(exp):
    return format_predictions(exp.measurements)

@bp.route('/<experiment_id>/scansite')
def scansite_predictions(experiment_id):
    user = current_user if current_user.is_authenticated else None
    # user_owner = current_user is not None and current_user.experiment_owner(exp)
    exp = experiment.get_experiment_by_id(experiment_id, user)
    formatted_predictions = wrap_format_predictions(exp)

    return render_template(
        'proteomescout/experiments/scansite.html',
        title = strings.experiments_scansite_page_title % (exp),
        experiment=exp,
        predictions=formatted_predictions)
