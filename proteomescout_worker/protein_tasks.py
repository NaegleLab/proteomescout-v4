from app import celery
import logging
from proteomescout_worker import notify_tasks
# changed to see if celery works with the new line since we're currently not using the other modules
# from proteomescout_worker.helpers import upload_helpers, entrez_tools, pfam_tools, picr_tools, uniprot_tools, dbsnp_tools
from proteomescout_worker.helpers import upload_helpers, entrez_tools, uniprot_tools
from app.database import protein, experiment
from app.config import strings
from app.utils import uploadutils
import traceback
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

log = logging.getLogger('ptmscout')

MAX_NCBI_BATCH_SIZE = 400
MAX_UNIPROT_BATCH_SIZE = 200

def get_uniprot_proteins(protein_accessions):
    log.info("Getting uniprot records for %d accessions", len(protein_accessions))
    prot_map = uniprot_tools.get_uniprot_records(protein_accessions)

    errors = []
    for acc in protein_accessions:
        if acc not in prot_map:
            errors.append(entrez_tools.EntrezError())
            errors[-1].acc = acc

    return prot_map, errors

def log_errors(query_errors, exp_id, accessions, line_mappings):
    log.info("Detected %d errors", len(query_errors))
    
    #report errors
    for error in query_errors:
        for line in accessions[error.acc]:
            accession, peptide = line_mappings[line]
            experiment.createExperimentError(exp_id, line, accession, peptide, strings.experiment_upload_warning_accession_not_found % (accession))

# def load_scansite(prot, taxonomy):
#     motif_class = None
#     if 'mammalia' in taxonomy:
#         motif_class="MAMMALIAN"
#     elif 'saccharomycotina' in taxonomy:
#         motif_class="YEAST"
#     elif 'saccharomyces' in taxonomy:
#         motif_class="YEAST"
    
#     if motif_class != None:
#         upload_helpers.query_protein_scansite(prot, motif_class)

# def parse_region_tracks(prot, features):
#     for f in features:
#         pr = protein.ProteinRegion(f.type, f.name, f.source, f.start, f.stop)
#         if not prot.hasRegion(pr):
#             prot.regions.append(pr)

# def get_clinical_significance(mutations):
#     snps = {}
#     for m in mutations:
#         dbsnp_id = m.getDBSNPId()
#         if dbsnp_id != None:
#             snps[dbsnp_id] = m

#     result = dbsnp_tools.get_variant_classification(snps.keys())
#     for rsid in snps:
#         if rsid in result:
#             snps[rsid].clinical = result[rsid]

# def load_new_protein(accession, protein_record):
#     created = False
#     prot = protein.getProteinBySequence(protein_record.sequence, protein_record.species)
#     if prot == None:
#         prot = upload_helpers.create_new_protein(protein_record.name, protein_record.gene, protein_record.locus, protein_record.sequence, protein_record.species)
#         created = True

#     # load the host organism taxonomy

#     if protein_record.host_organism:
#         protein_record.set_host_organism_taxonomy( upload_helpers.get_taxonomic_lineage(protein_record.host_organism) )

#     # load additional protein accessions if available

#     other_accessions = picr_tools.get_picr(accession, prot.species.taxon_id)
#     added_accessions = upload_helpers.create_accession_for_protein(prot, protein_record.other_accessions + other_accessions)

#     parse_region_tracks(prot, protein_record.features)
#     upload_helpers.find_activation_loops(prot)

#     upload_helpers.map_expression_probesets(prot)

#     if created:
#         pfam_tools.parse_or_query_domains(prot, accession)
#         load_scansite( prot, protein_record.full_taxonomy )
        
#     new_mutations = []
#     for m in protein_record.mutations:
#         if not prot.hasMutation(m):
#             prot.mutations.append(m)
#             new_mutations.append(m)
#     get_clinical_significance(new_mutations)

#     prot.saveProtein()

#     log.info("%s protein: %s | %s" , "Created" if created else "Updated", accession, str(added_accessions))
#     return prot

# def report_protein_error(acc, protein_map, accessions, line_mappings, exp_id, message):
#     log.warning("Failed to create protein: %s -- '%s'", acc, message)
#     del protein_map[acc]

#     if acc in accessions:
#         for line in accessions[acc]:
#             accession, peptide = line_mappings[line]
#             experiment.createExperimentError(exp_id, line, accession, peptide, message)

# UPDATE_EVERY = 30
# def create_missing_proteins(protein_map, missing_proteins, accessions, line_mappings, exp_id, job_id):

#     i = 0
#     #create entries for the missing proteins
#     protein_id_map = {}
#     for acc in missing_proteins:
#         try:
#             prot = load_new_protein(acc, protein_map[acc])
#             protein_id_map[acc] = prot.id

#         except uploadutils.ParseError, e:
#             report_protein_error(acc, protein_map, accessions, line_mappings, exp_id, e.message)
#         except pfam_tools.PFamError:
#             report_protein_error(acc, protein_map, accessions, line_mappings, exp_id, "PFam query failed for protein: %s" % (acc))
#         except picr_tools.PICRError:
#             report_protein_error(acc, protein_map, accessions, line_mappings, exp_id, "PICR query failed for protein: %s" % (acc))
#         except DBAPIError:
#             raise
#         except SQLAlchemyError:
#             raise
#         except Exception, e:
#             log.warning("Unexpected Error: %s\n%s\nDuring import of protein %s", str(e), traceback.format_exc(), acc)
#             report_protein_error(acc, protein_map, accessions, line_mappings, exp_id, "Unexpected Error: %s" % (str(e)))

#         i+=1
#         if i % UPDATE_EVERY == 0:
#             notify_tasks.set_job_progress.apply_async((job_id, i, len(missing_proteins)))

#     notify_tasks.set_job_progress.apply_async((job_id, i, len(missing_proteins)))
#     return protein_map, protein_id_map


# @celery.task
# @upload_helpers.notify_job_failed
# @upload_helpers.transaction_task
# def query_protein_metadata(external_db_result, accessions, line_mapping, exp_id, job_id):
#     #list the missing proteins
#     missing_proteins = set()
#     for acc in external_db_result:
#         pr = external_db_result[acc]
#         if protein.getProteinBySequence(pr.sequence, pr.species) == None:
#             missing_proteins.add(acc)

#     upload_helpers.store_stage_input(exp_id, 'proteins', external_db_result)
#     notify_tasks.set_job_stage.apply_async((job_id, 'proteins', len(missing_proteins)))

#     return create_missing_proteins(external_db_result, missing_proteins, accessions, line_mapping, exp_id, job_id)


def get_proteins_by_accession(accessions, start_callback, notify_callback):
    uniprot_ids, other_ids = upload_helpers.extract_uniprot_accessions(accessions.keys())
    uniprot_tasks = upload_helpers.create_chunked_tasks_preserve_groups(sorted(uniprot_ids), MAX_UNIPROT_BATCH_SIZE)
    ncbi_tasks = upload_helpers.create_chunked_tasks(sorted(other_ids), MAX_NCBI_BATCH_SIZE)
    total_task_cnt = len(uniprot_tasks) + len(ncbi_tasks)
    
    start_callback(total_task_cnt)

    i = 0
    protein_map = {}
    for ncbi_accessions in ncbi_tasks:
        log.info("Getting Geeneus records for %d accessions", len(ncbi_accessions))
        result, errors = entrez_tools.get_proteins_from_ncbi(ncbi_accessions)
        protein_map.update(result)

        i+=1
        notify_callback(i, total_task_cnt, errors)

    for uniprot_accessions in uniprot_tasks:
        log.info("Getting Uniprot records for %d accessions", len(uniprot_accessions))
        result, errors = get_uniprot_proteins(uniprot_accessions)
        protein_map.update(result)

        i+=1
        notify_callback(i, total_task_cnt, errors)

    return protein_map


@celery.task
@upload_helpers.notify_job_failed
@upload_helpers.transaction_task
def get_proteins_from_external_databases(accessions, line_mapping, exp_id, job_id):
    def start_callback(total_task_cnt):
        notify_tasks.set_job_stage.apply_async((job_id, 'query', total_task_cnt))
    def notify_callback(i, total_task_cnt, errors):
        log_errors(errors, exp_id, accessions, line_mapping)
        notify_tasks.set_job_progress.apply_async((job_id, i, total_task_cnt))

    return get_proteins_by_accession(accessions, start_callback, notify_callback)