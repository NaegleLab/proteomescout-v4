import celery
import logging
from app.database import experiment, upload
from proteomescout_worker.helpers import upload_helpers
from proteomescout_worker import notify_tasks, protein_tasks
log = logging.getLogger('ptmscout')

@celery.task
@upload_helpers.notify_job_failed
@upload_helpers.dynamic_transaction_task
def start_import(exp_id, session_id, job_id, nullmods=False):
    exp = experiment.get_experiment_by_id(exp_id, check_ready=False, secure=False)
    
    # log.info("Loading session info...")
    session = upload.get_session_by_id(session_id, secure=False)
    
    # log.info("Loading data file...")
    accessions, sites, site_type, mod_map, data_runs, errors, line_mapping = upload_helpers.parse_datafile(session, nullmods)

    if exp.loading_stage == 'in queue' or exp.status != 'error':
        exp.clearErrors()
        # log.info("Reporting %d data file errors..." % (len(errors)))
        upload_helpers.report_errors(exp_id, errors, line_mapping)
        exp.save_experiment()

    if len(accessions) == 0:
        log.info("Nothing to do: all proteins were rejected!")
        return notify_tasks.finalize_experiment_import, (exp_id,), None
    else:
        headers = upload_helpers.get_series_headers(session)

        load_ambiguities = exp.ambiguity == 1
        notify_tasks.set_job_status.apply_async((job_id, 'started'))

        query_task = protein_tasks.get_proteins_from_external_databases.s(accessions, line_mapping, exp_id, job_id)
        proteins_task = protein_tasks.query_protein_metadata.s(accessions, line_mapping, exp_id, job_id)
        GO_task = GO_tasks.import_go_terms.s(exp_id, job_id)
        
        peptide_task = peptide_tasks.run_peptide_import.s(sites, mod_map, data_runs, headers, session.units, load_ambiguities, nullmods, site_type == 'sites', exp_id, job_id)
        

        annotate_task = annotate_tasks.annotate_experiment.si(exp_id, job_id)
        finalize_task = notify_tasks.finalize_experiment_import.si(exp_id)

        last_stage_arg = upload_helpers.get_stage_input(exp.id, exp.loading_stage)
        
        if exp.loading_stage == 'query':
            load_task = ( query_task | proteins_task | GO_task | peptide_task | annotate_task | finalize_task )
        elif exp.loading_stage == 'proteins':
            load_task = ( proteins_task | GO_task | peptide_task | annotate_task | finalize_task )
        elif exp.loading_stage == 'GO terms':
            load_task = ( GO_task | peptide_task | annotate_task | finalize_task )
        elif exp.loading_stage == 'peptides':
            load_task = ( peptide_task | annotate_task | finalize_task )

        log.info("Tasks created... now we wait")

        return load_task, (last_stage_arg,), None

