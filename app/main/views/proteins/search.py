from app.config import strings
from app import celery
from flask import render_template, redirect, request, jsonify, current_app
from flask_login import current_user
from app.main.views.proteins import bp
from app.database import protein, modifications
from celery.result import AsyncResult

from app.main.forms.search_form import ProteinSearchForm


@celery.task
def perform_queries(search, peptide, species, protein_names):
    proteins = protein_query(search, peptide, species, protein_names)
    metadata = {}
    for p in proteins:
        metadata[p.id] = get_peptides_by_proteins(p.id)
    
    return [proteins, metadata]
    # except Exception as ex:
    #     app.log_exception(ex)
    #     print(ex)
    #     raise ex
    
def protein_query(search, peptide, species, protein_names):

    if search == '':
        search = None

    if peptide == '':
        peptide = None

    if species == 'all' or species == '':
        species = None

    protein_cnt, proteins = protein.search_proteins(
        search=search,
        species=species,
        sequence=peptide,
        page=None,
        exp_id=None,
        includeNames=protein_names)

    return proteins


def get_peptides_by_proteins(prot_id, exp_id=None):
    print('get_peptides_by_proteins invoked')
    measured = modifications.get_measured_peptides_by_protein(prot_id)

    exp_ids = set()
    residues = set()
    ptms = set()
    sites = set()

    for ms in measured:
        exp_ids.add(ms.experiment_id)

    if exp_id:
        measured = [ms for ms in measured if ms.experiment_id == exp_id]

    for ms in measured:
        for mspep in ms.peptides:
            residues.add(mspep.peptide.site_type)
            sites.add(mspep.peptide.site_pos)
            ptms.add(mspep.modification.name)
    
    return [exp_ids, sites, residues, ptms]


def get_protein_metadata(prot, metadata_map, exp_ids, sites, residues, ptms):

    # exp_ids = set()
    # residues = set()
    # ptms = set()
    # sites = set()

    # for ms in measured:
    #     exp_ids.add(ms.experiment_id)

    # if exp_id:
    #     measured = [ms for ms in measured if ms.experiment_id == exp_id]

    # for ms in measured:
    #     for mspep in ms.peptides:
    #         residues.add(mspep.peptide.site_type)
    #         sites.add(mspep.peptide.site_pos)
    #         ptms.add(mspep.modification.name)

    prot_id = prot.id
    prot_name = prot.name
    prot_gene = prot.get_gene_name()
    prot_species = prot.species.name
    prot_sequence = prot.sequence

    metadata_map[prot_id] = [
        prot_name,
        prot_gene,
        prot_species,
        len(prot_sequence),
        len(exp_ids),
        len(sites),
        ','.join(residues),
        ', '.join(ptms)]


def generate_metadata(result):
        proteins = result[0]
        protein_metadata = {}
        for p in proteins:
            async_metadata = result[1][p.id]
            exp_ids = async_metadata[0]
            sites = async_metadata[1]
            residues = async_metadata[2]
            ptms = async_metadata[3]
            get_protein_metadata(p, protein_metadata, exp_ids, sites, residues, ptms)
        return protein_metadata


@bp.route('/', methods=['GET', 'POST'])
def search():
    # try:
    search = False
    # page = request.args.get(get_page_parameter(), type=int, default=1)

    form = ProteinSearchForm()
    user = current_user if current_user.is_authenticated else None

    if form.validate_on_submit():
        
        search = form.protein.data
        peptide = form.peptide.data
        species = form.species.data
        protein_names = form.protein_names.data
    
        task = perform_queries.delay(search, peptide, species, protein_names)
        current_app.logger.info('perform_queries task sent to queue')
        
        return jsonify({'task_id': task.id})
    # except Exception as ex:
    #     app.log_exception(ex)
    #     print(ex)
    #     raise ex
        
    return render_template(
        'proteomescout/proteins/search.html', 
        title=strings.protein_search_page_title, 
        form=form)


@bp.route('/search_status/<task_id>', methods=['GET'])
def search_status(task_id):
    task = AsyncResult(task_id, app=celery)
    
    response = {
        'state': task.state,
    }
    if task.state=='SUCCESS':
        current_app.logger.info('Search task [' + str(task_id) + '] succeeded')
        response['result'] = generate_metadata(task.result)
    return jsonify(response)