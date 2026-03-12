from flask import render_template, redirect, flash, url_for, request, jsonify, send_file, send_from_directory
from flask_login import login_required, logout_user, current_user, login_user
#from app import current_app
import sqlalchemy as sa
from app.database import jobs 
from proteomescout_worker import export_tasks
from app.main.forms.email_validator import EmailForm, DownloadForm
from app.main.views.experiments import bp
from app import db
import time
from random import randint
import os
from app.config import settings, strings 




# temp function to just send an email
# creating temp function for data exports
#@bp.route('/experiment/download_experiment/<int:experiment_id>', methods = ['GET', 'POST'])
#def download_experiment(experiment_id):
   # form = EmailForm()
 #  if form.validate_on_submit(): 
  #      send_email('test', sender = current_app.config['ADMINS'][0], recipients = [form.email.data], text_body = 'test', html_body = 'test')
  #      flash('Email sent to ' + form.email.data)

    # Fetch the experiment data using experiment_id
    # Render a template or return a response
 #   return render_template('proteomescout/experiments/download_experiment.html', experiment_id=experiment_id, form=form)'''





def create_export_job(export_id, experiment_id, user_id):
    export_id = "%f.%d" % (time.time(), randint(0,10000))
    j = jobs.Job()
    j.status = 'in queue'
    j.stage = 'initializing'
    j.progress = 0
    j.max_progress = 0
    j.name = "Export experiment %d" % (experiment_id)
    #j.status_url = url_for('account.manage_experiments')
    # placeholder
    #j.result_url = url_for('info.home')
    #j.result_url = '' #request.route_url('batch.batch_download', id=batch_id)
    j.type = 'experiment_export'
    j.user_id = user_id
    j.save()
    return j.id

'''
@bp.route('/experiment/download_experiment/<int:experiment_id>', methods = ['GET', 'POST'])
def download_experiment(experiment_id):
    form = DownloadForm()
    if form.validate_on_submit(): 
        annotate = form.annotate.data
        user_id = form.email.data  # assuming user_id is email in this context

        export_id = "%f.%d" % (time.time(), randint(0,10000))
        job_id = create_export_job(export_id, experiment_id, user_id)  # replace with your actual job creation logic

        export_tasks.run_experiment_export_job.apply_async(
            args=(annotate, export_id, experiment_id, user_id, job_id),
        )
        #flash('Export job started. You will receive an email when it is complete.')
        return jsonify({'message': 'Export job started. You will receive an email when it is complete.'})

    return render_template('proteomescout/experiments/download_experiment.html', experiment_id=experiment_id, form=form)
'''

@bp.route('/experiment/download_experiment/<int:experiment_id>', methods = ['GET', 'POST'])
def download_experiment(experiment_id):
    form = DownloadForm()
    user = current_user if current_user.is_authenticated else None
    if user is None:
        flash('You must be logged in to download an experiment.')
        return redirect(url_for('auth.login'))
    if form.validate_on_submit(): 
        annotate = form.annotate.data
        user_email = user.email
        user_id = user.id
        export_id = "%f.%d" % (time.time(), randint(0,10000))
        job_id = create_export_job(export_id, experiment_id, user_id)  # replace with your actual job creation logic

        # Generate the filename
        exp_filename = f"experiment_{experiment_id}_{export_id}.tsv"

        # Generate the result URL
        result_url = url_for('experiment.download_result', filename=exp_filename,  _external=True)
        #print(f"Generated URL: {result_url}")   

        # Update the job with the result_url
        job = jobs.get_job_by_id(job_id)
        job.result_url = result_url
        job.save()


        export_tasks.run_experiment_export_job.apply_async(
            args=(annotate, export_id, experiment_id, user_id, exp_filename, result_url, user_email, job_id),
        )
        return render_template('proteomescout/info/information.html',
                                   title=strings.experiment_downloand_submitted_page_title,
                                   header=strings.experiment_downloand_submitted_page_title,
                                   message=strings.experiment_downloadoad_submitted_message,
                                   link=url_for('account.manage_experiments'),
                                   )
        #flash('Export job started. You will receive an email when it is complete.')
        #return jsonify({'message': 'Export job started. You will receive an email when it is complete.'})
        
    return render_template('proteomescout/experiments/download_experiment.html', experiment_id=experiment_id, form=form)

## something here is wrong, this route is not being populated in the html file 
# 
#
#@bp.route('/experiments/download_result/<path:filename>', methods=['GET'])
@bp.route('/download_result/<path:filename>', methods=['GET'])
def download_result(filename):
    # Retrieve the job using the job_id
    #job = jobs.Job.get(job_id)

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
    
# Not sure if this is actually even doing anything. Might remove.
@bp.route('/download_page/<path:filename>', methods=['GET'])
def download_page(filename):
    #print(f"filename: {filename}")

    return render_template('proteomescout/experiments/download_results.html', filename=filename)