from flask_login import current_user
from flask import render_template, request, redirect, url_for, flash, session, current_app
from app.main.views.upload import bp

from app.utils import uploadutils
from app.database import upload, experiment, protein
from proteomescout_worker.helpers import upload_helpers


def get_proteomescout_accesssions(accessions):
    pscout_accessions = {}
    for accession in accessions.keys():
        pscout_accessions[accession] = protein.get_proteins_by_accession(accession)
    return pscout_accessions


@bp.route('/<session_id>/review', strict_slashes=False, methods=['GET', 'POST'])
def review(session_id):
    user = current_user if current_user.is_authenticated else None

    db_session = upload.get_session_by_id(session_id, user=user)

    
    accessions, sites, site_type, mod_map, data_runs, errors, line_mapping = upload_helpers.parse_datafile(db_session, False)
    pscout_accessions = get_proteomescout_accesssions(accessions)

    return render_template(
        'proteomescout/upload/review.html',
        accessions=accessions,
        sites=sites,
        site_type=site_type,
        line_mapping=line_mapping,
        pscout_accessions=pscout_accessions
    )



