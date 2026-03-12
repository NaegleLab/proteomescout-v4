from flask_login import current_user
from flask import render_template, request, redirect, url_for, flash, session, current_app
from app.main.views.upload import bp
import json
from werkzeug.utils import secure_filename
import os
from app.database import upload
import time



ALLOWED_EXTENSIONS = set(['tsv', 'txt'])
# from app.main.forms import upload_form
    
def validate_required(field_data, field_name):
    data = request.form.get(field_data)
    if not data:
        flash(f"Required form field '{field_name}' cannot be empty")
        return False
    return True

def vailidate_file(field_data, field_name):
    data = request.files.get(field_data)
    if not data:
        flash(f"Required form field '{field_name}' cannot be empty")
        return False
    return True


def validate_on_submit():
    upload_type = request.form.get('upload_type')
    valid = vailidate_file('data_file', 'Input Data File')
    valid_parent = validate_required('parent_experiment','Parent Experiment') if upload_type != 'new' else True
    valid = valid and valid_parent
    if upload_type == 'extend':
        valid_title = validate_required('extension_title','Extension Title')
        valid_description = validate_required('extension_description', 'Extension Description')
        valid = valid and valid_title and valid_description
            
    return valid
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file():
    if 'data_file' not in request.files:
        flash('No file uploaded')
        return redirect(request.url)
    file = request.files['data_file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
        
    elif file and allowed_file(file.filename):
        splitfile =  file.filename.rsplit('.', 1)
        
        filename = secure_filename(splitfile[0] + str(time.time()) + '.' + splitfile[1])
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        return filename
        # session['data_file'] = filename
    else:
        flash('Incorrect File Type : Please upload a .tsv file')
    

def create_session(exp_file):
    session = upload.Session()
    
    session.user_id = current_user.id
    session.data_file = exp_file
    session.resource_type = 'experiment'
    session.load_type = request.form.get('upload_type').strip()
    session.parent_experiment = None
    session.stage = 'config'
    session.change_name = ''
    session.change_description = ''
    
    if session.load_type != 'new':
        session.parent_experiment = int(request.form.get('parent_experiment'))
    
    if session.load_type == 'extend':
        session.change_name = request.form.get('extension_title')
        session.change_description = request.form.get('extension_description')

    session.save()
    
    return session.id
    



def process_submit():
    upload_type = request.form.get('upload_type')
    session['upload_type'] = upload_type
    upload_file()
    if upload_type == 'new':
        session['parent_experiment'] = None
    else:
        session['parent_experiment'] = request.form.get('parent_experiment')

    if upload_type == 'extend':
        session['extension_title'] = request.form.get('extension_title')
        session['extension_description'] = request.form.get('extension_description')
    else:
        session['extension_title'] = None
        session['extension_description'] = None

   
    

@bp.route('/', strict_slashes=False, methods=['GET', 'POST'])
def start():
    # form = upload_form.UploadForm()
    user = current_user if current_user.is_authenticated else None
    user_experiments = []
    if user:
        user_experiments = [e for e in user.my_experiments() if e.ready()]
    experiment_size = len(user_experiments)
    
    
    if request.method == 'POST' and validate_on_submit():
        # process_submit()
        filename = upload_file()
        session_id = create_session(filename)
        return redirect(url_for('upload.configure', session_id = session_id))
    


    # flash('HERE we are')
    # flash('That was wrong')

    return render_template(
        'proteomescout/upload/start.html',
        user_experiments=user_experiments,
        experiment_size=experiment_size,
    )
        