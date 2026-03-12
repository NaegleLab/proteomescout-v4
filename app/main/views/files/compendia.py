from app.main.views.files import bp
#from . import bp  # Import the Blueprint object from your __init__.py file
from flask import render_template, url_for, request, send_file
from werkzeug.exceptions import NotFound
import os
import pickle
import time
from app.config import strings, settings

def create_file_entry(fn, desc, listing):
    entry = {'link': url_for('compendia.compendia_download', name=fn),
             'name': fn,
             'desc': desc,
             'size': listing[fn]['size'],
             'contents': '%d proteins, %d modifications' % (listing[fn]['proteins'], listing[fn]['modifications']),
             'date': listing[fn]['date']}
    return entry

@bp.route('/', methods=['GET', 'POST'])
def compendia_listing():
    listing = None

    with open(os.path.join(settings.ptmscout_path, settings.export_file_path, "listing.pyp"), "rb") as listing_file:
        listing = pickle.load(listing_file)

    files = [
        create_file_entry('proteomescout_everything.zip', 'All proteins and modifications', listing)
    ]

    return render_template(
        'proteomescout/info/downloads.html',
        files = files,
        title = strings.compendia_download_page_title
    )

@bp.route('/compendia_download')
def compendia_download():
    listing = None
    with open(os.path.join(settings.ptmscout_path, settings.export_file_path, "listing.pyp"),'rb') as listing_file:
        listing = pickle.load(listing_file)

    fname = request.args.get('name')
    file_path = os.path.join(settings.export_file_path, fname)
    fpath = os.path.join(settings.ptmscout_path, file_path)
    if not os.path.exists(fpath):
        raise NotFound()

    t = time.strptime( listing[fname]['date'] )
    strt = time.strftime("%Y%m%d", t)
    
    file_download_name = '%s_%s.zip' % (fname[:fname.find('.zip')], strt)

    return send_file(file_path, download_name=file_download_name)