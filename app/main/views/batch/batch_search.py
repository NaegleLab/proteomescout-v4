from turtle import title
import re 
from app.config import strings
from flask import render_template, redirect, request, url_for, flash , send_from_directory
from flask_login import current_user
from app.main.views.batch import bp
from app.main.forms.batch_search_form import BatchSearchForm
from app.database import jobs
import time
from random import randint
from proteomescout_worker import export_tasks
import os 

''' def create_job_and_submit(accessions, user_id):
    accessions = accessions.replace(',', ' ').split()
    batch_id = "%f.%d" % (time.time(), randint(0,10000))

    j = jobs.Job()
    j.status = 'in queue'
    j.stage = 'initializing'
    j.progress = 0
    j.max_progress = 0
    j.status_url = url_for('account.manage_experiments')

    if len(accessions) == 1:
        j.name = "Batch annotate 1 protein"
    else:
        j.name = "Batch annotate %d proteins" % (len(accessions))
    j.type = 'batch_annotate'
    j.user_id = user_id

    # Generate the filename
    
    print(batch_id)
    # Generate the result URL
    result_url = url_for('batch.download_result', batch_id=batch_id, user_id=current_user.id, _external=True)
    print(f"Generated URL: {result_url}")       

# Update the job with the result_url
    j.result_url = result_url 

    j.save()
    job_id = j.id
    export_tasks.batch_annotate_proteins.apply_async((accessions, batch_id, user_id, job_id))

'''
def create_job_and_submit(accessions, batch_id, user_id):
    #accessions = accessions.replace(',', ' ').split()
    #print(f"Before split: {accessions}")
    #accessions = re.split('[, ]+', accessions)
    #print(f"After split: {accessions}")
    #accessions = re.split('[, ]+', accessions)
    batch_id = batch_id
    j = jobs.Job()
    j.status = 'in queue'
    j.stage = 'initializing'
    j.progress = 0
    j.max_progress = 0
    j.name = "Batch annotate %s" % (batch_id)
    j.status_url = url_for('account.manage_experiments')
    # placeholder
    #j.result_url = url_for('info.home')
    #j.result_url = '' #request.route_url('batch.batch_download', id=batch_id)
    j.type = 'batch_annote_proteins'
    j.user_id = user_id
    j.save()
    return j.id

'''
@bp.route('/', methods=['GET', 'POST'])
def batch_search():
    form = BatchSearchForm()

    if form.validate_on_submit():
        if current_user.is_authenticated:
            accessions = form.accessions.data
            create_job_and_submit(accessions, current_user.id)
            return render_template('proteomescout/info/information.html',
                                   title=strings.protein_batch_search_submitted_page_title,
                                   header=strings.protein_batch_search_submitted_page_title,
                                   message=strings.protein_batch_search_submitted_message,
                                   link=url_for('account.manage_experiments'),
                                   )
        else:
            flash('You are not signed in. Please sign in to continue.')
            return redirect(url_for('auth.login', next=request.url))
    else:
        return render_template(
            'proteomescout/batch/batch_search.html',
            title=strings.protein_batch_search_page_title,
            form=form,
        )
'''
@bp.route('/', methods=['GET', 'POST'])
def batch_search(): 
    form = BatchSearchForm()
    user = current_user if current_user.is_authenticated else None
    if user is None:
        flash('You must be logged in to download an experiment.')
        return redirect(url_for('auth.login'))
    if form.validate_on_submit():
        if current_user.is_authenticated:
            accessions = form.accessions.data
            accessions = accessions.replace(',', ' ').split()
            #user_email = user.email
            batch_id = "%f.%d" % (time.time(), randint(0,10000))
            user_id = user.id
            job_id = create_job_and_submit(accessions, batch_id, user_id)  # replace with your actual job creation logic

            print(f"Job ID: {job_id}")

            # generate filename 
            exp_filename = f"batch_{batch_id}_{user_id}"

            # generate result URL
            result_url = url_for('batch.download_result',  filename=exp_filename, _external=True)

            # update the jpob with result url 
            job = jobs.get_job_by_id(job_id)
            print(job)
            job.result_url = result_url
            job.save()
            # submitting the job for annotation 
            export_tasks.batch_annotate_proteins.apply_async((accessions, batch_id, user_id, job_id, exp_filename))
            return render_template('proteomescout/info/information.html',
                                   title=strings.protein_batch_search_submitted_page_title,
                                   header=strings.protein_batch_search_submitted_page_title,
                                   message=strings.protein_batch_search_submitted_message,
                                   link=url_for('account.manage_experiments'),
                                   )
        else:
            flash('You are not signed in. Please sign in to continue.')
            return redirect(url_for('auth.login', next=request.url))
    else:
        return render_template(
            'proteomescout/batch/batch_search.html',
            title=strings.protein_batch_search_page_title,
            form=form,
        )
'''
@bp.route('/download_result/<batch_id>/<user_id>', methods=['GET'])
def download_result(batch_id, user_id):
    filename = "batch_%s_%s.zip" % (batch_id, user_id)
    file_path = os.path.join('app/data/annotate', filename)  # Construct the relative file path

    print(os.getcwd())
    print(os.path.exists(file_path))

    print(file_path)
    if os.path.exists(file_path):
        absolute_directory = os.path.abspath(os.path.dirname(file_path))
        return send_from_directory(absolute_directory, os.path.basename(file_path), as_attachment=True)
    else:
        return "File not found", 404

'''
#@bp.route('/experiments/download_result/<path:filename>', methods=['GET'])
@bp.route('/download_result/<path:filename>', methods=['GET'])
def download_result(filename):
    # Retrieve the job using the job_id
    #job = jobs.Job.get(job_id)
    filename = filename + '.zip'
    #file_path = os.path.join('/Users/logan/proteome-scout-3/app/data/annotate', filename)
    file_path = os.path.join('app/data/annotate', filename)  # Construct the relative file path

    print(f"File path: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(f"Directory: {os.path.dirname(file_path)}")
    print(f"Filename: {os.path.basename(file_path)}")
    # Check if the file exists
    #print(os.getcwd())
    #print(os.path.exists(file_path))
    #print(file_path)
    if os.path.exists(file_path):
        # Get the absolute directory path
        absolute_directory = os.path.abspath(os.path.dirname(file_path))
        return send_from_directory(absolute_directory, os.path.basename(file_path), as_attachment=True)
        #return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True)
    
    else:
        return "File not found", 404
    