from app import celery
from proteomescout_worker.helpers import upload_helpers
from app.database import experiment, modifications, jobs
from app.config import strings, settings
# from app.utils import mail

@celery.task
@upload_helpers.transaction_task
def finalize_batch_annotate_job(stats, job_id):
    protein_cnt, error_cnt = stats
    job = jobs.get_job_by_id(job_id)
    job.finish()
    job.save()
    
    subject = strings.batch_annotation_finished_subject
    message = strings.batch_annotation_finished_message % (job.name, protein_cnt, error_cnt, job.result_url)
    
    # mail.celery_send_mail([job.user.email], subject, message)

@celery.task
@upload_helpers.transaction_task
def finalize_experiment_export_job(job_id):
    job = jobs.get_job_by_id(job_id)
    job.finish()
    job.save()
    
    subject = strings.experiment_export_finished_subject
    message = strings.experiment_export_finished_message % (job.name, job.result_url)
    
    # mail.celery_send_mail([job.user.email], subject, message)

@celery.task
@upload_helpers.transaction_task
def finalize_mcam_export_job(job_id):
    job = jobs.get_job_by_id(job_id)
    job.finish()
    job.save()
    
    subject = strings.mcam_enrichment_finished_subject
    message = strings.mcam_enrichment_finished_message % (job.name, job.result_url)
    
    # mail.celery_send_mail([job.user.email], subject, message)

@celery.task
@upload_helpers.transaction_task
def finalize_experiment_import(exp_id):
    exp = experiment.get_experiment_by_id(exp_id, check_ready=False, secure=False)
    exp.job.finish()
    exp.job.save()

    peptides = modifications.countMeasuredPeptidesForExperiment(exp_id)
    proteins = modifications.countProteinsForExperiment(exp_id)
    exp_errors = experiment.countErrorsForExperiment(exp_id)

    error_log_url = "%s/errors" % (exp.job.result_url)
    
    subject = strings.experiment_upload_finished_subject
    message = strings.experiment_upload_finished_message % (exp.name, peptides, proteins, exp_errors, error_log_url)
    
    # mail.celery_send_mail([exp.job.user.email], subject, message)

@celery.task
@upload_helpers.transaction_task
def finalize_annotation_upload_job(job_id, total, errors):
    job = jobs.get_job_by_id(job_id)
    job.finish()
    job.save()
    
    subject = strings.annotation_upload_finished_subject
    message = strings.annotation_upload_finished_message % (job.name, total, len(errors), job.result_url)
    
    for err in errors:
        message += "%s\n" % ( err )
    
    # mail.celery_send_mail([job.user.email], subject, message)
    

@celery.task
@upload_helpers.transaction_task
def notify_job_failed(job_id, exc, stack_trace):
    job = jobs.get_job_by_id(job_id)
    job.fail(stack_trace)
    job.save()
    
    subject = strings.job_failed_subject
    message = strings.job_failed_message % (job.name, job.stage, "Exception: " + str(exc), settings.issueTrackerUrl)
    
    # mail.celery_send_mail([job.user.email, settings.adminEmail], subject, message)
    
    

@celery.task
@upload_helpers.transaction_task
def set_job_status(job_id, status):
    job = jobs.get_job_by_id(job_id)
    job.status = status
    job.save()

@celery.task
@upload_helpers.transaction_task
def set_job_stage(job_id, stage, max_value):
    job = jobs.get_job_by_id(job_id)
    job.stage = stage
    job.progress = 0
    job.max_progress = max_value
    job.save()

@celery.task
@upload_helpers.transaction_task
def set_job_progress(job_id, value, max_value):
    job = jobs.get_job_by_id(job_id)
    job.progress = value
    job.max_progress = max_value
    job.save()

@celery.task
@upload_helpers.transaction_task
def increment_job_progress(job_id):
    job = jobs.get_job_by_id(job_id)
    job.progress = job.progress+1
    job.save()

