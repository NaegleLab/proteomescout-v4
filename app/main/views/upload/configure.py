from flask_login import current_user
from flask import render_template, request, redirect, url_for, flash, session, current_app
from app.main.views.upload import bp
from app.config import strings
from app.utils import uploadutils
from app.database import upload
import pandas as pd
import os


# def parse_user_input(session, request):
    
#     units = webutils.post(request, 'units', '')
    
#     numcols = 0
#     for field in request.POST:
#         m = re.match('column_([0-9]+)_(type|label)', field)
#         if m:
#             col = int(m.group(1))
#             if col + 1 > numcols:
#                 numcols = col + 1
                
#     errors = []
#     columns = {}
    
#     data_labels = set()
#     stddev_labels = set()
#     stddev_cols = []
#     for c in xrange(0, numcols):
#         col = {'type':'', 'label':''}
#         columns[c] = col
#         col['type'] = webutils.post(request,'column_%d_type' % (c), "").strip()
        
#         if col['type'] == "":
#             errors.append(strings.experiment_upload_error_column_type_not_defined % (c+1))
            
#         col['label'] = webutils.post(request, 'column_%d_label' % (c), "").strip()

#         if col['label'] == "" and col['type'] in set(['stddev','data']):        
#             errors.append(strings.experiment_upload_error_data_column_empty_label % (c+1))
            
#         if col['label'] != "":
#             if col['type'] == 'data':
#                 if col['label'] in data_labels:
#                     errors.append(strings.experiment_upload_error_data_column_label_duplicated % (c+1))
#                 data_labels.add(col['label'])
#             elif col['type'] == 'stddev':
#                 if col['label'] in stddev_labels:
#                     errors.append(strings.experiment_upload_error_data_column_label_duplicated % (c+1))
#                 stddev_labels.add(col['label'])
#                 stddev_cols.append(c)
#             else:
#                 col['label'] = ""

#     [ errors.append(strings.experiment_upload_error_standard_deviation_label_does_not_match_any_data_column % (c+1, columns[c]['label'])) 
#             for c in stddev_cols if columns[c]['label'] not in data_labels ]

#     session.columns = []
#     for c in xrange(0, numcols):
#         col = upload.SessionColumn()
#         col.type = columns[c]['type']
#         col.label = columns[c]['label']
#         col.column_number = c
#         session.columns.append(col)
        
#     session.units = units

#     return {'columns':columns,'units':units}, [ uploadutils.ColumnError(e) for e in errors ]

def parse_user_input(db_session, num_cols):
    units = request.form.get('units', '')
    errors = []
    columns = {}  

    data_labels = set()
    stddev_labels = set()
    stddev_cols = []

    for c in range(0, num_cols):
        col = {'type':'', 'label':''}
        columns[c] = col
        col['type'] = request.form.get('column_%d_type' % (c), "").strip()
        
        if col['type'] == "":
            errors.append(strings.experiment_upload_error_column_type_not_defined % (c+1))
            
        col['label'] = request.form.get('column_%d_label' % (c), "").strip()

        if col['label'] == "" and col['type'] in set(['stddev','data']):        
            errors.append(strings.experiment_upload_error_data_column_empty_label % (c+1))
            
        if col['label'] != "":
            if col['type'] == 'data':
                if col['label'] in data_labels:
                    errors.append(strings.experiment_upload_error_data_column_label_duplicated % (c+1))
                data_labels.add(col['label'])
            elif col['type'] == 'stddev':
                if col['label'] in stddev_labels:
                    errors.append(strings.experiment_upload_error_data_column_label_duplicated % (c+1))
                stddev_labels.add(col['label'])
                stddev_cols.append(c)
            else:
                col['label'] = ""

    [ errors.append(strings.experiment_upload_error_standard_deviation_label_does_not_match_any_data_column % (c+1, columns[c]['label'])) 
            for c in stddev_cols if columns[c]['label'] not in data_labels ]

    db_session.columns = []
    for c in range(0, num_cols):
        col = upload.SessionColumn()
        col.type = columns[c]['type']
        col.label = columns[c]['label']
        col.column_number = c
        db_session.columns.append(col)
        
    db_session.units = units

    return {'columns':columns,'units':units}, [ uploadutils.ColumnError(e) for e in errors ]


@bp.route('/<session_id>/configure', strict_slashes=False, methods=['GET', 'POST'])
def configure(session_id):
    user = current_user if current_user.is_authenticated else None

    db_session = upload.get_session_by_id(session_id, user=user)
    column_defs = uploadutils.assign_column_defaults(db_session)

    headers, rows = uploadutils.load_header_and_data_rows(db_session.data_file,uploadutils.MAX_ROW_CHECK)

    num_cols = len(headers)
    allow_override = False

    if request.method == 'POST' and request.form.get('submit_button') == 'btn-continue':
        force = request.form.get('override')
        column_defs, errors = parse_user_input(db_session, num_cols)
        commit = False
        try:
            if len(errors) > 0:
                raise uploadutils.ErrorList(errors, True)
            uploadutils.check_data_column_assignments(db_session, True)
            commit = True
        except uploadutils.ErrorList as ce:
            allow_override = not ce.critical
            commit = force and allow_override
            errors = ce.error_list()
                
        if commit:
            db_session.stage = 'metadata'
            db_session.save()
            return redirect(url_for('upload.metadata', session_id = db_session.id))
        else:
            for error in errors:
                flash(error)

    return render_template(
        'proteomescout/upload/configure.html',
        column_values=['none',
        # 'hidden',
        'data','stddev','accession','peptide','sites','species','modification','run'],
        headers = headers,
        data_rows = rows,
        instructions=strings.experiment_upload_configure_instructions,
        data_definitions = column_defs,
        allow_override = allow_override
        
    )
        
        
    #     return {'allowoverride': allowoverride,
    #         'navigation': navWizard,
    #         'headers': headers,
    #         'data_rows': data_rows,
    #         'error': errors,
    #         'data_definitions':column_defs,
    #         'session_id': session.id,
    #         'column_values': ['none','hidden','data','stddev','accession','peptide','sites','species','modification','run'],
    #         'instructions': strings.experiment_upload_configure_instructions,
    #         'pageTitle': pageTitle}column_defs
    # )