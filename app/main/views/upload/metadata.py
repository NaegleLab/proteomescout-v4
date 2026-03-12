from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.main.views.upload import bp
from app import db

from app.database import experiment, upload

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def write_experiment_properties(nexp, db_session):
    user = current_user if current_user.is_authenticated else None

    nexp.name = request.form.get('experiment_name')
    nexp.description = request.form.get('description')
    
    nexp.dataset = db_session.data_file
    
    nexp.published = 1 if request.form.get('published') == "yes" else 0
    nexp.ambiguity = 1 if request.form.get('ambiguous') == "yes" else 0
    nexp.URL = request.form.get('url')
    nexp.type = 'experiment'

    nexp.contact = None
    nexp.author = None
    nexp.journal = None
    nexp.volume = None
    nexp.page_end = None
    nexp.page_start = None
    nexp.publication_month = None
    nexp.publication_year = None
    nexp.errorLog = None
    nexp.PMID = None
    
    nexp.submitter_id = user.id
    
    if(db_session.load_type == 'extension'):
        nexp.experiment_id = db_session.parent_experiment
        
    if(request.form.get('published') == "yes"):
        nexp.contact = request.form.get('author_email')
        nexp.author = request.form.get('authors')
        
        nexp.volume = int(request.form.get('volume'))
        nexp.page_start = request.form.get('page_start')
        nexp.page_end = request.form.get('page_end')
        
        nexp.publication_month = request.form.get('publication_month')
        nexp.publication_year = int(request.form.get('publication_year'))
        
        nexp.journal = request.form.get('journal')
        if(request.form.get('pmid') != ""):
            nexp.PMID = int(request.form.get('pmid'))
    
    
    nexp.grant_permission(user, 'owner')
    nexp.save_experiment()


def mark_status(nexp, db_session):
    db_session.experiment_id = nexp.id
    db_session.stage = 'condition'
    db.session.commit()

def get_experiment_ref(db_session):
    user = current_user if current_user.is_authenticated else None
    if(db_session.experiment_id != None):
        nexp = experiment.get_experiment_by_id(db_session.experiment_id, user, False)
    else: 
        nexp = experiment.Experiment()
        nexp.public = 0
        nexp.experiment_id = None
    return nexp

def populate_metadata(db_session):
    user = current_user if current_user.is_authenticated else None
    field_dict = {
                     'pmid' : '',
                     'publication_year': '',
                     'publication_month': '',
                     'published': 'no',
                     'ambiguous': 'yes',
                     'author_contact' : '',
                     'page_start': '',
                     'page_end': '',
                     'authors': '',
                     'journal': '',
                     'volume': '',
                     'description': '',
                     'experiment_name':'',
                     'URL': ''
                  }

    if db_session.experiment_id is not None:
        try:
            exp = experiment.get_experiment_by_id(db_session.experiment_id, user, False)
            field_dict = {
                     'pmid':exp.PMID,
                     'publication_year': exp.publication_year,
                     'publication_month': exp.publication_month,
                     'published': 'yes' if exp.published == 1 else 'no',
                     'ambiguous': 'yes' if exp.ambiguity == 1 else 'no',
                     'author_contact' : exp.contact,
                     'page_start': exp.page_start,
                     'page_end': exp.page_end,
                     'authors': exp.author,
                     'journal': exp.journal,
                     'volume': exp.volume,
                     'description': exp.description,
                     'experiment_name':exp.name,
                     'URL': exp.URL
                  }

        except Exception as error:
            flash(error)
        
    elif db_session.parent_experiment is not None:
        try:
            exp = experiment.get_experiment_by_id(db_session.parent_experiment, user, False)
            field_dict = {
                        'pmid':exp.PMID,
                        'publication_year': exp.publication_year,
                        'publication_month': exp.publication_month,
                        'published': 'yes' if exp.published == 1 else 'no',
                        'ambiguous': 'yes' if exp.ambiguity == 1 else 'no',
                        'author_contact' : exp.contact,
                        'page_start': exp.page_start,
                        'page_end': exp.page_end,
                        'authors': exp.author,
                        'journal': exp.journal,
                        'volume': exp.volume,
                        'description': exp.description,
                        'experiment_name':exp.name,
                        'URL': exp.URL
                    }
        except Exception as error:
            flash(error)
    return field_dict
       

        





@bp.route('/<session_id>/metadata', strict_slashes=False, methods=['GET', 'POST'])
def metadata(session_id):
    user = current_user if current_user.is_authenticated else None
    db_session = upload.get_session_by_id(session_id, user=user)

    submitted = request.method == 'POST' and request.form.get('submit_button') == 'btn-continue'
    
    if submitted:
        nexp = get_experiment_ref(db_session)
        write_experiment_properties(nexp, db_session)
        mark_status(nexp, db_session)
        return redirect(url_for('upload.conditions', session_id = session_id))

    field_dict = populate_metadata(db_session)
    return render_template(
        'proteomescout/upload/metadata.html',
        field_dict = field_dict
        
    )